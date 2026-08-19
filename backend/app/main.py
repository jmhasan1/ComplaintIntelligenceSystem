"""FastAPI entrypoint for the AIVOA Complaint Intelligence Workbench."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from uuid import uuid4

from .schemas import ComplaintState, ChatResponse
from .graph import complaint_graph
from .document_parser import extract_text_from_upload
from .database import init_db, load_state, save_state, commit_state

app = FastAPI(title="AIVOA Complaint Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def _get_or_create_session(session_id: str) -> ComplaintState:
    return load_state(session_id, ComplaintState)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(session_id: str = Form(...), message: str = Form(...)):
    if not message.strip():
        raise HTTPException(400, "Message cannot be empty")

    form_state = _get_or_create_session(session_id)
    result = complaint_graph.invoke(
        {
            "message": message,
            "doc_text": None,
            "doc_filename": None,
            "form_state": form_state,
        }
    )

    updated = result["form_state"]
    save_state(session_id, updated)

    return ChatResponse(
        reply=result["reply"],
        form_state=updated,
        updated_fields=result.get("updated_fields", []),
        intent=result["intent"],
    )


@app.post("/api/upload", response_model=ChatResponse)
async def upload_document(session_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "Filename is required")

    content = await file.read()
    try:
        doc_text = extract_text_from_upload(file.filename, content)
    except Exception as exc:
        raise HTTPException(400, f"Document extraction failed: {exc}") from exc

    if not doc_text.strip():
        raise HTTPException(400, "Could not extract any text from the uploaded file.")

    form_state = _get_or_create_session(session_id)
    result = complaint_graph.invoke(
        {
            "message": "",
            "doc_text": doc_text,
            "doc_filename": file.filename,
            "form_state": form_state,
        }
    )

    updated = result["form_state"]
    save_state(session_id, updated)

    return ChatResponse(
        reply=result["reply"],
        form_state=updated,
        updated_fields=result.get("updated_fields", []),
        intent=result["intent"],
    )


@app.post("/api/commit/{session_id}")
async def commit_complaint(session_id: str):
    state = _get_or_create_session(session_id)
    if state.is_empty():
        raise HTTPException(400, "No complaint is ready to commit")

    complaint_id = f"CC-{uuid4().hex[:10].upper()}"
    commit_state(session_id, state, complaint_id)

    return {
        "status": "committed",
        "complaint_id": complaint_id,
        "message": "Complaint committed to the QMS ledger.",
    }


@app.get("/api/form/{session_id}", response_model=ComplaintState)
async def get_form(session_id: str):
    return _get_or_create_session(session_id)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aivoa-complaint-intelligence"}


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "service": "aivoa-complaint-intelligence"}
