"""
Core agent graph.

Architecture decision (this is the thing to explain in the walkthrough video):
--------------------------------------------------------------------------
Every node that touches the form (log / edit / extract) returns a
ComplaintStateUpdate -- a sparse diff, never a full form. A single merge_node
is the ONLY place that writes to the persisted ComplaintState, by applying
non-None fields from the diff on top of the existing state. This means:

  1. The "edit" tool can never accidentally erase fields it wasn't told
     about -- correcting the batch number can't wipe the product name.
  2. All three tools share one merge code path, so there's exactly one
     place state-consistency bugs could live, instead of three.
  3. The frontend can highlight exactly which fields changed (see
     ChatResponse.updated_fields), matching the field-level highlight
     behavior seen in the reference demo.

Graph shape:

    START -> classify_intent -> [log_complaint | edit_complaint | extract_document]
                                          |
                                          v
                                     merge_state
                                          |
                                          v
                              completeness_check
                                          |
                                          v
                                duplicate_check
                                          |
                                          v
                                  compose_reply -> END
"""

from __future__ import annotations
from typing import TypedDict, Optional, List, Literal
import json

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .schemas import ComplaintState, ComplaintStateUpdate, RiskAssessment
from .llm import get_llm
from .duplicate_detection import duplicate_store
from .database import list_committed_complaints
from .prompts import (
    LOG_COMPLAINT_SYSTEM_PROMPT,
    EDIT_COMPLAINT_SYSTEM_PROMPT,
    EXTRACT_DOCUMENT_SYSTEM_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    CHAT_REPLY_LOG_TEMPLATE,
    CHAT_REPLY_EDIT_TEMPLATE,
    CHAT_REPLY_EXTRACT_TEMPLATE,
)


class GraphState(TypedDict, total=False):
    message: str
    doc_text: Optional[str]
    doc_filename: Optional[str]
    form_state: ComplaintState
    intent: Literal["log", "edit", "extract"]
    diff: ComplaintStateUpdate
    updated_fields: List[str]
    reply: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_structured_extraction(system_prompt: str, user_content: str) -> ComplaintStateUpdate:
    """
    Calls the LLM with a schema-describing system prompt and parses the JSON
    response into a ComplaintStateUpdate. Uses with_structured_output where
    available, with a manual json.loads fallback for robustness against a
    small model occasionally wrapping output in prose or code fences.
    """
    llm = get_llm(structured=True)
    try:
        structured_llm = llm.with_structured_output(ComplaintStateUpdate)
        result = structured_llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
        )
        return result
    except Exception:
        # Fallback: raw call + manual JSON parse (strip code fences defensively)
        raw = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
        ).content
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        return ComplaintStateUpdate(**data)


def _apply_diff(state: ComplaintState, diff: ComplaintStateUpdate) -> tuple[ComplaintState, List[str]]:
    updated_fields: List[str] = []
    new_state = state.model_copy(deep=True)

    form_fields = {
        "complaint_source", "customer_name", "product_name", "product_strength",
        "batch_number", "affected_quantity", "manufacturing_date", "expiry_date",
        "originating_site_block", "impacted_npm", "complaint_category",
        "complaint_description",
    }
    risk_fields = {
        "severity": "severity",
        "suggested_next_action": "suggested_next_action",
        "initial_risk_assessment": "initial_risk_assessment",
        "capa_recommendation": "capa_recommendation",
    }

    diff_dict = diff.model_dump()
    for field_name in form_fields:
        value = diff_dict.get(field_name)
        if value is not None:
            setattr(new_state, field_name, value)
            updated_fields.append(field_name)

    for diff_field, risk_attr in risk_fields.items():
        value = diff_dict.get(diff_field)
        if value is not None:
            setattr(new_state.risk_assessment, risk_attr, value)
            updated_fields.append(diff_field)

    return new_state, updated_fields


_FIELD_LABELS = {
    "complaint_source": "Complaint Source",
    "customer_name": "Customer Name",
    "product_name": "Product Name",
    "product_strength": "Product Strength",
    "batch_number": "Batch / Lot Number",
    "affected_quantity": "Affected Quantity",
    "manufacturing_date": "Manufacturing Date",
    "expiry_date": "Expiry Date",
    "originating_site_block": "Originating Site Block",
    "impacted_npm": "Impacted NPM",
    "complaint_category": "Complaint Category",
    "complaint_description": "Complaint Description",
    "severity": "Severity",
    "suggested_next_action": "Suggested Next Action",
    "initial_risk_assessment": "Initial Risk Assessment",
    "capa_recommendation": "CAPA Recommendation",
}


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def classify_intent(state: GraphState) -> GraphState:
    if state.get("doc_text"):
        return {**state, "intent": "extract"}

    form_state: ComplaintState = state["form_state"]
    if form_state.is_empty():
        return {**state, "intent": "log"}

    llm = get_llm(structured=False, temperature=0.0)
    prompt = INTENT_CLASSIFIER_PROMPT.format(
        state_status="already populated" if not form_state.is_empty() else "empty",
        message=state["message"],
    )
    result = llm.invoke([HumanMessage(content=prompt)]).content.strip().lower()
    intent = "edit" if "edit" in result else "log"
    return {**state, "intent": intent}


def log_complaint_node(state: GraphState) -> GraphState:
    diff = _run_structured_extraction(LOG_COMPLAINT_SYSTEM_PROMPT, state["message"])
    return {**state, "diff": diff}


def edit_complaint_node(state: GraphState) -> GraphState:
    current = state["form_state"].model_dump()
    user_content = (
        f"CURRENT FORM STATE:\n{json.dumps(current, indent=2)}\n\n"
        f"USER MESSAGE:\n{state['message']}"
    )
    diff = _run_structured_extraction(EDIT_COMPLAINT_SYSTEM_PROMPT, user_content)
    return {**state, "diff": diff}


def extract_document_node(state: GraphState) -> GraphState:
    diff = _run_structured_extraction(EXTRACT_DOCUMENT_SYSTEM_PROMPT, state["doc_text"])
    return {**state, "diff": diff}


def merge_state_node(state: GraphState) -> GraphState:
    new_state, updated_fields = _apply_diff(state["form_state"], state["diff"])
    return {**state, "form_state": new_state, "updated_fields": updated_fields}


def completeness_check_node(state: GraphState) -> GraphState:
    """Deterministic completeness check; no LLM guessing is involved."""
    form_state: ComplaintState = state["form_state"]
    required = {
        "customer_name": "Customer Name",
        "product_name": "Product Name",
        "product_strength": "Product Strength / Grade",
        "batch_number": "Batch / Lot Number",
        "affected_quantity": "Affected Quantity",
        "complaint_category": "Complaint Category",
        "complaint_description": "Complaint Description",
    }
    missing = [
        label for field, label in required.items()
        if not getattr(form_state, field, None)
    ]
    form_state.missing_fields = missing
    form_state.completeness_score = round(
        (len(required) - len(missing)) / len(required), 2
    )
    return {**state, "form_state": form_state}


def duplicate_check_node(state: GraphState) -> GraphState:
    """
    Detect likely recurring complaints against previously committed
    complaints.

    Only run the comparison when a meaningful complaint description
    exists. Product-name-only comparisons can generate noisy matches.
    """

    form_state: ComplaintState = state["form_state"]

    if not form_state.complaint_description:
        return state

    records = list_committed_complaints()

    duplicate_store.load_from_records(records)

    is_dup, note = duplicate_store.check_duplicate(
        form_state.product_name,
        form_state.complaint_description,
    )

    form_state.duplicate_flag = is_dup
    form_state.duplicate_notes = note

    return {
        **state,
        "form_state": form_state,
    }

def compose_reply_node(state: GraphState) -> GraphState:
    intent = state["intent"]
    updated_fields = state.get("updated_fields", [])

    if intent == "edit":
        labels = [f'"{_FIELD_LABELS.get(f, f)}"' for f in updated_fields]
        fields_str = ", ".join(labels) if labels else "the requested details"
        reply = CHAT_REPLY_EDIT_TEMPLATE.format(fields=fields_str)
    elif intent == "extract":
        reply = CHAT_REPLY_EXTRACT_TEMPLATE.format(filename=state.get("doc_filename") or "the uploaded document")
    else:
        extra = ""
        if state["form_state"].duplicate_flag:
            extra = " (note: this looks similar to a previously logged complaint)"
        reply = CHAT_REPLY_LOG_TEMPLATE.format(extra=extra)

    return {**state, "reply": reply}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("log_complaint", log_complaint_node)
    graph.add_node("edit_complaint", edit_complaint_node)
    graph.add_node("extract_document", extract_document_node)
    graph.add_node("merge_state", merge_state_node)
    graph.add_node("completeness_check", completeness_check_node)
    graph.add_node("duplicate_check", duplicate_check_node)
    graph.add_node("compose_reply", compose_reply_node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        lambda s: s["intent"],
        {
            "log": "log_complaint",
            "edit": "edit_complaint",
            "extract": "extract_document",
        },
    )

    graph.add_edge("log_complaint", "merge_state")
    graph.add_edge("edit_complaint", "merge_state")
    graph.add_edge("extract_document", "merge_state")

    graph.add_edge("merge_state", "completeness_check")
    graph.add_edge("completeness_check", "duplicate_check")
    graph.add_edge("duplicate_check", "compose_reply")
    graph.add_edge("compose_reply", END)

    return graph.compile()


complaint_graph = build_graph()
