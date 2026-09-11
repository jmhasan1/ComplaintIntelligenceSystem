# AIVOA Complaint Intelligence System

An AI-powered pharmaceutical customer complaint management prototype built for the **AIVOA.AI Round 1 AI Product Engineer (Fresher)** technical assignment.

The system combines a React complaint form with an AI Copilot that can understand natural-language complaints, extract structured complaint information, edit existing complaints conversationally, process complaint documents, perform completeness and deterministic validation, identify potential duplicates, generate an initial risk assessment, and guide the complaint through a human-review step before persistence.

---

## Overview

Traditional complaint intake requires users to manually populate multiple structured fields from emails, documents, or customer messages.

This prototype demonstrates a conversational alternative:

```text
Customer Complaint / Document
            ↓
       AI Copilot
            ↓
     Intent Detection
            ↓
 ┌──────────┼───────────┐
 ↓          ↓           ↓
Log       Edit        Extract
Complaint Complaint   Document
 └──────────┼───────────┘
            ↓
      State Merge
            ↓
 Deterministic Validation
            ↓
   Completeness Check
            ↓
  Duplicate Detection
            ↓
    Risk Assessment
            ↓
     Human Review
            ↓
       Save / QMS
            ↓
       PostgreSQL
```

A separate read-only QA path allows users to ask questions about the current complaint state without modifying the complaint form.

---

# Key Features

## 1. Natural-Language Complaint Logging

Users can describe a pharmaceutical complaint conversationally instead of manually entering every form field.

Example:

> Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026. Expiry date February 2028. Please log this complaint.

The AI extracts structured complaint information and updates the complaint form.

The workflow can populate fields such as:

- Complaint Type
- Complaint Date
- Customer / Reporter
- Product
- Batch Number
- Manufacturing Date
- Expiry Date
- Affected Quantity
- Initial Severity
- Priority
- Complaint Description
- Risk Assessment

The system also generates an initial AI-assisted risk assessment.

---

## 2. Natural-Language Complaint Editing

Existing complaint information can be modified conversationally.

Example:

> Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.

The system updates only the requested fields while preserving unrelated complaint information.

This is implemented using **sparse state updates**.

```text
Current Complaint State
          +
     User Request
          ↓
    Intent Detection
          ↓
    Structured Diff
          ↓
      State Merge
          ↓
   Updated Complaint
```

For example, an edit can produce:

```json
{
  "batch_number": "BMX240602",
  "affected_quantity": "48 capsules"
}
```

Rather than returning a complete replacement complaint form.

This reduces the risk of accidentally overwriting information that the user did not request to change.

---

# 3. Multi-Format Document Extraction

The Copilot accepts complaint documents in multiple formats:

- PDF
- DOCX
- TXT
- EML

The extracted document content is passed through the same complaint intelligence workflow used for natural-language input.

```text
Document
   ↓
Document Parser
   ↓
Extracted Text
   ↓
LangGraph Workflow
   ↓
Structured Complaint State
   ↓
Validation / Completeness / Risk
```

PDF extraction uses `pypdf`.

DOCX extraction uses `python-docx`.

Email (`.eml`) content is parsed using Python's standard email handling capabilities.

This implementation is intended for assignment demonstration purposes and is **not positioned as production-grade OCR or document-understanding infrastructure**.

---

# 4. QA Intent

The Copilot supports a separate **QA / question-answering intent**.

Users can ask questions about the current complaint without modifying the form.

Example:

> What is the current batch number?

or:

> What information is still missing?

The QA path is deliberately read-only:

```text
User Question
     ↓
Intent Classifier
     ↓
     QA
     ↓
Response
     ↓
END
```

It does not mutate the complaint state.

This separates informational questions from complaint-changing actions.

---

# 5. Deterministic Validation

The system does not rely exclusively on the LLM to determine whether complaint data is internally consistent.

Deterministic application-level validation is performed after state updates.

Current validation rules include:

- Expiry Date cannot be earlier than Manufacturing Date.
- Complaint Date cannot be in the future.
- Priority must be one of:
  - Low
  - Medium
  - High
  - Urgent
- Initial Severity must be one of:
  - Minor
  - Major
  - Critical
- Invalid/unparseable dates generate validation errors.

The rules are implemented separately from the LangGraph orchestration:

```text
backend/app/validation.py
```

The LangGraph validation node invokes these deterministic application rules.

This creates a clear separation:

```text
LLM
 ↓
Structured AI Output
 ↓
Application Validation
 ↓
State Mutation
```

The LLM is responsible for understanding language and proposing structured information.

Application code remains responsible for enforcing deterministic business rules.

---

# 6. Completeness Checking

The workflow checks whether the complaint contains sufficient information for further processing.

The UI displays completeness-related feedback so the user can identify missing information before saving the complaint.

This supports the human-in-the-loop workflow rather than treating AI extraction as automatically final.

---

# 7. AI Risk Assessment

The AI generates an initial risk assessment from the complaint information.

The assessment can include:

- Initial Severity
- Risk reasoning
- Suggested Next Action
- Investigation considerations
- CAPA recommendation where generated by the current workflow

The risk assessment is presented as an **AI-assisted initial assessment**, not as a final regulatory or quality decision.

A human reviewer remains responsible for approving the complaint before persistence.

---

# 8. Field Confidence

AI-extracted or AI-updated fields can include confidence estimates.

The UI exposes field-confidence information to help the reviewer understand where the AI may be less certain.

Confidence is treated as an **AI signal**, not as a replacement for human validation.

```text
AI Extraction
     ↓
Field Value
     +
Confidence Estimate
     ↓
Human Review
```

This is particularly useful for document-derived complaint information.

---

# 9. Duplicate Complaint Detection

The system includes duplicate complaint detection against previously committed complaints.

Historical committed complaints are loaded from PostgreSQL and compared with the current complaint.

The current similarity pipeline uses:

```text
Complaint Text
     ↓
TF-IDF Vectorization
     ↓
Cosine Similarity
     ↓
Configured Threshold
     ↓
Potential Duplicate
```

The database is the source of truth for historical committed complaints.

This means duplicate detection is not dependent solely on an in-memory collection and can continue to work across application restarts.

During local testing, a similar complaint produced a similarity score of approximately `0.98`.

The result is presented as a **potential duplicate warning**, allowing a human reviewer to decide whether the complaint is genuinely duplicated.

---

# 10. Human Review Workflow

Phase 2 introduces an explicit human-review state.

The complaint can move through:

```text
Draft
  ↓
Needs Review
  ↓
Reviewed
```

AI processing and validation can mark the complaint as requiring review.

The UI provides a **Mark Reviewed** action.

A complaint cannot be committed until it has been explicitly marked as reviewed.

```text
AI Processing
     ↓
Validation
     ↓
Completeness
     ↓
Duplicate Check
     ↓
Review Required
     ↓
Human Reviewer
     ↓
Mark Reviewed
     ↓
Save Complaint
```

This provides an important human-in-the-loop boundary between AI assistance and persistent complaint records.

---

# 11. Save Complaint / QMS Persistence

After human review, the complaint can be saved to the QMS Ledger.

The backend:

1. Verifies the complaint has been reviewed.
2. Generates the committed complaint record.
3. Persists it to PostgreSQL.

The database maintains separate persistence for:

- Complaint sessions
- Committed complaints

PostgreSQL therefore acts as the persistent source of truth for committed complaint records.

---

# 12. Reset Form

The frontend provides a **Reset Form** action.

Reset clears the current complaint session so the user can begin a new complaint workflow without manually removing existing fields.

---

# Architecture

```text
┌─────────────────────────────────────────────┐
│                React + Redux                │
│                                             │
│  Complaint Form       AI Copilot            │
│  Risk Assessment      Review State          │
└──────────────────────┬──────────────────────┘
                       │
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────┐
│                   FastAPI                   │
│                                             │
│  Chat API                                   │
│  Document Upload                            │
│  Review API                                 │
│  Commit API                                 │
│  Reset API                                  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                 LangGraph                   │
│                                             │
│  Intent Classification                      │
│       │                                     │
│       ├── Complaint Logging                 │
│       ├── Complaint Editing                 │
│       ├── Document Extraction               │
│       └── QA (read-only)                    │
│                                             │
│  State Merge                                │
│       ↓                                     │
│  Deterministic Validation                   │
│       ↓                                     │
│  Completeness Check                         │
│       ↓                                     │
│  Duplicate Detection                        │
│       ↓                                     │
│  Response / Risk Assessment                 │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌────────────────┐
│  Groq LLM    │  │   PostgreSQL   │
│              │  │                │
│ Structured   │  │ Sessions       │
│ Extraction   │  │ Complaints     │
│ Reasoning    │  │ Source of Truth│
└──────────────┘  └────────────────┘
```

---

# LangGraph Workflow

## Normal Complaint Workflow

```text
START
  ↓
classify_intent
  ↓
┌───────────────┬────────────────┬──────────────────┐
│               │                │
▼               ▼                ▼
log_complaint  edit_complaint  extract_document
│               │                │
└───────────────┴────────────────┘
                ↓
           merge_state
                ↓
    deterministic_validation
                ↓
      completeness_check
                ↓
        duplicate_check
                ↓
        compose_reply
                ↓
               END
```

## QA Workflow

```text
START
  ↓
classify_intent
  ↓
     qa
  ↓
 END
```

QA intentionally bypasses the complaint mutation and persistence workflow because it is read-only.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Frontend Build | Vite |
| State Management | Redux Toolkit |
| Backend | Python + FastAPI |
| AI Orchestration | LangGraph |
| LLM Provider | Groq |
| Primary LLM | `openai/gpt-oss-20b` |
| Fallback LLM | `openai/gpt-oss-120b` |
| Database | PostgreSQL |
| ORM / Persistence | SQLAlchemy |
| PDF Parsing | pypdf |
| DOCX Parsing | python-docx |
| Email Parsing | Python `email` |
| Similarity Detection | TF-IDF + Cosine Similarity |
| UI Font | Inter |
| Local Infrastructure | Docker Compose |

## Groq Model Note

The original assignment referenced:

```text
gemma2-9b-it
```

That model is no longer available in the configured Groq environment used for this implementation.

The application therefore uses currently available Groq models:

```text
Primary:
openai/gpt-oss-20b

Fallback:
openai/gpt-oss-120b
```

The structured-output and LangGraph workflow remains the same; only the configured model backend was updated to an available model.

---

# Project Structure

```text
AIVOA-Complaint-Intelligence-System/
│
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── document_parser.py
│   │   ├── duplicate_detection.py
│   │   ├── graph.py
│   │   ├── llm.py
│   │   ├── main.py
│   │   ├── prompts.py
│   │   ├── schemas.py
│   │   └── validation.py
│   │
│   ├── sample_data/
│   │   └── zenith_metformin_complaint.pdf
│   │
│   ├── scripts/
│   ├── tests/
│   │   └── test_phase2_quality.py
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── store/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── pyproject.toml
├── .python-version
└── .gitignore
```

---

# Local Setup

## Prerequisites

Install:

- Python
- Node.js / npm
- Docker Desktop
- A Groq API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/jmhasan1/ComplaintIntelligenceSystem.git
cd ComplaintIntelligenceSystem
```

---

## 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

Verify the container:

```bash
docker ps
```

PostgreSQL is exposed on port:

```text
5432
```

---

## 3. Configure the Backend

From the backend directory:

```powershell
cd backend
copy .env.example .env
```

Add your Groq API key:

```text
GROQ_API_KEY=your_groq_api_key
```

Never commit `.env` or API keys to Git.

---

## 4. Install Backend Dependencies

Install the Python dependencies using the project's configured dependency setup.

For a standard requirements-based environment:

```powershell
pip install -r requirements.txt
```

---

## 5. Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 6. Install and Start the Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# Demonstration Workflow

The following workflow demonstrates the main capabilities of the system.

## Test 1 — Natural-Language Complaint Logging

Enter:

> Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026. Expiry date February 2028. Please log this complaint.

Expected behavior:

- Complaint information is extracted.
- Complaint Type / Date / Priority and other available fields are populated.
- Initial risk assessment is generated.
- Extracted fields are displayed in the complaint form.

---

## Test 2 — Natural-Language Editing

Enter:

> Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.

Expected behavior:

- Batch Number changes.
- Affected Quantity changes.
- Unrelated complaint information remains intact.
- Changed fields are visually highlighted.

---

## Test 3 — QA

After a complaint has been populated, ask:

> What is the current batch number?

Expected behavior:

- The Copilot identifies the request as QA.
- It answers using the current complaint state.
- The complaint form is not modified.

---

## Test 4 — PDF Extraction

Upload:

```text
backend/sample_data/zenith_metformin_complaint.pdf
```

Expected behavior:

- The document is parsed.
- Complaint information is extracted.
- The form is populated.
- AI risk assessment is generated.
- The complaint can subsequently be edited conversationally.

---

## Test 5 — DOCX Extraction

Upload a `.docx` complaint document.

Expected behavior:

- Paragraph and table content is extracted.
- Extracted text is passed through the complaint workflow.
- Structured complaint fields are populated.

---

## Test 6 — Deterministic Validation

Provide an invalid combination such as:

```text
Manufacturing Date: March 2026
Expiry Date: January 2026
```

Expected behavior:

```text
Expiry Date cannot be earlier than Manufacturing Date.
```

The complaint is marked as requiring review.

---

## Test 7 — Confidence and Completeness

Process a complaint with partially known information.

Expected behavior:

- Missing information is identified through completeness checking.
- AI-extracted fields can expose confidence information.
- The user can review and correct the extracted values.

---

## Test 8 — Duplicate Detection

First save a complaint.

Then submit a new complaint describing the same or a highly similar issue.

Expected behavior:

- Previously committed complaints are loaded from PostgreSQL.
- Similarity is calculated.
- A potential duplicate warning is displayed when the configured threshold is exceeded.

---

## Test 9 — Human Review and Save

After processing a complaint:

1. Review the extracted fields.
2. Review validation errors.
3. Review completeness information.
4. Review duplicate warnings.
5. Review the AI risk assessment.
6. Click **Mark Reviewed**.
7. Click **Save Complaint**.

The complaint can only be committed after it has entered the reviewed state.

---

## Test 10 — Reset

Click:

**Reset Form**

Expected behavior:

- The current complaint state is cleared.
- The user can begin a new complaint workflow.

---

# Design Decisions

## 1. Sparse State Updates

The system uses sparse structured updates for conversational editing.

Instead of asking the LLM to regenerate the entire complaint form, the LLM returns only the fields that need to change.

```text
Existing State
     +
Sparse AI Patch
     ↓
State Merge
     ↓
Updated State
```

Example:

```json
{
  "batch_number": "BMX240602",
  "affected_quantity": "48 capsules"
}
```

This reduces accidental overwrites and makes conversational editing safer.

---

## 2. LLM Reasoning vs Application Validation

The application deliberately separates AI reasoning from deterministic business rules.

```text
Natural Language
       ↓
      LLM
       ↓
Structured Output
       ↓
Application Validation
       ↓
State Mutation
       ↓
Persistence
```

The LLM handles:

- Intent understanding
- Information extraction
- Natural-language interpretation
- Risk reasoning
- Natural-language responses

Application code handles:

- State management
- Deterministic validation
- Completeness state
- Review state
- Persistence
- Duplicate record retrieval

This prevents the LLM from being the sole authority for deterministic constraints.

---

## 3. Human-in-the-Loop Before Persistence

AI-generated complaint information is not treated as automatically final.

The workflow explicitly introduces:

```text
AI Processing
      ↓
Validation
      ↓
Review Required
      ↓
Human Review
      ↓
Reviewed
      ↓
Save
```

This is particularly important for a pharmaceutical complaint-management workflow where AI output should assist, rather than silently replace, human quality decisions.

---

## 4. PostgreSQL as Source of Truth

Committed complaints are persisted in PostgreSQL.

Duplicate detection retrieves historical committed complaints from the database rather than depending only on process-local memory.

This makes the persistence layer the source of truth for historical complaint records.

---

## 5. Read-Only QA Path

QA requests are routed separately from complaint mutations.

```text
QA Question
    ↓
QA Node
    ↓
Answer
    ↓
END
```

This prevents a simple informational question from unintentionally triggering complaint updates or persistence.

---

# Testing

Backend quality tests are included under:

```text
backend/tests/
```

The Phase 2 tests cover areas including:

- Invalid date relationships
- Valid complaint validation
- Sparse state updates
- Confidence handling

Run:

```powershell
pytest
```

---

# Frontend Verification

Build the frontend production bundle with:

```powershell
cd frontend
npm install
npm run build
```

A successful build verifies that the React application compiles correctly for production.

---

# API Workflow

The frontend communicates with the FastAPI backend through HTTP.

Conceptually:

```text
React / Redux
     ↓
FastAPI
     ↓
LangGraph
     ↓
Structured Complaint State
     ↓
React / Redux
```

Document uploads follow:

```text
React Upload
     ↓
FastAPI
     ↓
Document Parser
     ↓
Extracted Text
     ↓
LangGraph
     ↓
Complaint State
```

Review and persistence follow:

```text
Complaint State
     ↓
Validation
     ↓
Review Required
     ↓
Mark Reviewed
     ↓
Commit Complaint
     ↓
PostgreSQL
```

---

# Scope and Limitations

This project is a prototype created for the AIVOA.AI technical challenge.

It is **not a validated pharmaceutical GxP / 21 CFR Part 11 production system**.

The prototype does not provide:

- Production regulatory validation
- Electronic-signature compliance
- Full audit-event history
- Authentication and role-based access control
- Production-grade OCR
- Production document-understanding infrastructure
- Enterprise security controls
- Automated regulatory decision-making

AI-generated risk assessments, extracted fields, confidence scores, and duplicate warnings are intended to support human decision-making rather than replace qualified quality personnel.

Document extraction is designed for demonstration purposes and should not be interpreted as production-grade document processing.

The application should not be used with real patient or regulated production data without appropriate security, validation, privacy, regulatory, and quality controls.

---

# Future Improvements

Potential production-oriented extensions include:

1. Historical complaint retrieval using `pgvector`
2. Evidence panels for duplicate and related complaints
3. Investigation and root-cause hypothesis generation
4. CAPA workflow and tracking
5. Full audit-event timeline
6. Automated evaluation datasets for extraction and editing accuracy
7. Authentication and role-based access control
8. Stronger deterministic validation and auditability
9. Advanced human-in-the-loop approval workflows
10. Production-grade OCR and document understanding
11. Structured complaint analytics and dashboards
12. Automated regression evaluation for LLM outputs

These features are intentionally outside the scope of the current assignment implementation.

---

# Assignment Alignment

The implementation focuses on the core assignment requirements:

```text
React + Redux
       ↓
Python + FastAPI
       ↓
LangGraph
       ↓
Groq
       ↓
PostgreSQL
       ↓
Inter UI
```

The project demonstrates:

- AI-powered complaint intake
- Conversational complaint editing
- Document-based complaint extraction
- Structured AI output
- LangGraph orchestration
- Risk assessment
- Completeness checking
- Duplicate detection
- Deterministic validation
- AI confidence information
- Human review
- Complaint persistence

The design intentionally prioritizes a working end-to-end product, clear separation of AI and deterministic application logic, and explainable workflow boundaries over unnecessary architectural complexity.

---

# Demo Videos

The submission includes two complementary demonstrations.

## Video 1 — Product Demonstration

Demonstrates the working application, including:

- Complaint logging
- Conversational editing
- QA
- PDF/DOCX extraction
- Validation
- Confidence
- Completeness
- Duplicate detection
- Human review
- Save
- Reset

## Video 2 — Code and Architecture Explanation

Explains the end-to-end implementation:

```text
Frontend
   ↓
Redux State
   ↓
FastAPI
   ↓
LangGraph
   ↓
LLM / Structured Output
   ↓
Validation
   ↓
Completeness
   ↓
Duplicate Detection
   ↓
Risk Assessment
   ↓
Human Review
   ↓
PostgreSQL
```

The goal of the code walkthrough is to demonstrate the engineering decisions behind the product rather than simply walk through every source file.

---

# Security

Never commit secrets to the repository.

The Groq API key must remain in the local `.env` file:

```text
GROQ_API_KEY=your_groq_api_key
```

The `.env` file should remain excluded from Git.

---

# License / Assignment Use

This repository was created as a technical assignment submission for the AIVOA.AI AI Product Engineer (Fresher) evaluation.