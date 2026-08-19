"""
Central data contracts for the complaint system.

Design decision: ComplaintState is the single source of truth for the form.
Every AI tool (log / edit / extract) does NOT return a full form — it returns
a ComplaintStateUpdate, a sparse object where unset fields are None (meaning
"don't touch this field"). The graph's merge step applies only the non-None
fields onto the persisted ComplaintState. This is what makes the "edit"
tool safe: correcting the batch number can never accidentally wipe the
product name, dates, or risk assessment.
"""

from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    severity: Optional[str] = Field(
        default=None, description="One of: Critical, Major, Minor"
    )
    suggested_next_action: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    capa_recommendation: Optional[str] = Field(
        default=None,
        description="Bonus: Corrective and Preventive Action suggestion",
    )


class ComplaintState(BaseModel):
    """The full, persisted state of the Log Customer Complaint form."""

    # 1. Origin & customer details
    complaint_source: Optional[str] = None  # e.g. Pharmacy, Email, Distributor
    customer_name: Optional[str] = None

    # 2. Product & batch identification
    product_name: Optional[str] = None
    product_strength: Optional[str] = None  # e.g. "500 mg" or "IP/BP"
    batch_number: Optional[str] = None
    affected_quantity: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None

    # 3. Facility & material impact
    originating_site_block: Optional[str] = None
    impacted_npm: Optional[str] = None  # Non-Product Materials

    # 4. Defect analysis
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None

    # AI Copilot risk assessment
    risk_assessment: RiskAssessment = Field(default_factory=RiskAssessment)

    # Bonus: duplicate detection
    duplicate_flag: Optional[bool] = None
    duplicate_notes: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)

    def is_empty(self) -> bool:
        complaint_fields = (
            "complaint_source", "customer_name", "product_name",
            "product_strength", "batch_number", "affected_quantity",
            "manufacturing_date", "expiry_date", "originating_site_block",
            "impacted_npm", "complaint_category", "complaint_description",
        )
        return all(getattr(self, field) is None for field in complaint_fields)


class ComplaintStateUpdate(BaseModel):
    """
    Sparse diff returned by every extraction/edit tool.
    None = "no change to this field". Only the LLM-populated fields are set.
    """

    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    affected_quantity: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    originating_site_block: Optional[str] = None
    impacted_npm: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None

    severity: Optional[str] = None
    suggested_next_action: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    capa_recommendation: Optional[str] = None

    def applied_field_names(self) -> List[str]:
        return [k for k, v in self.model_dump().items() if v is not None]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str = ""
    # Base64-free: for the take-home, the doc is pre-extracted to text
    # client-side is NOT required — we accept raw text extracted server-side
    # by document_parser.py from an uploaded file. See /upload endpoint.


class ChatResponse(BaseModel):
    reply: str
    form_state: ComplaintState
    updated_fields: List[str] = Field(default_factory=list)
    intent: str  # "log" | "edit" | "extract"
