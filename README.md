# AIVOA Complaint Intelligence System

An AI-powered pharmaceutical customer complaint intake, triage, editing, document-extraction, duplicate-detection, and QMS persistence prototype built for the **AIVOA Round 1 AI Product Engineer challenge**.

The system allows a user to interact with a complaint-management workflow through natural language instead of manually filling the complaint form.

## Demo Workflow

```text
Natural-Language Complaint
          ↓
     AI Copilot
          ↓
    Intent Detection
          ↓
   Complaint Extraction
          ↓
   Structured Form State
          ↓
   Completeness Check
          ↓
    Risk Assessment
          ↓
 Natural-Language Editing
          ↓
 Document / PDF Extraction
          ↓
 Duplicate Detection
          ↓
    QMS Ledger Commit
          ↓
      PostgreSQL
```

The same complaint state is maintained throughout the workflow, allowing users to correct extracted or previously entered information without losing unrelated fields.

---

## Key Features

### 1. Natural-Language Complaint Logging

Users can describe a complaint conversationally instead of manually entering individual fields.

Example:

> Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026. Expiry date February 2028. Please log this complaint.

The AI extracts relevant complaint information and populates the complaint form.

The system also generates an initial AI-assisted risk assessment based on the complaint.

---

### 2. Natural-Language Complaint Editing

Existing complaints can be modified using conversational instructions.

Example:

> Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.

The system updates only the relevant fields while preserving the rest of the complaint.

This is implemented using **sparse state updates** rather than replacing the entire complaint state.

```text
Current Complaint State
        +
User Correction
        ↓
LLM produces changed fields
        ↓
Pydantic validation
        ↓
State merge
        ↓
Updated Complaint
```

This prevents a correction to one field from accidentally overwriting unrelated complaint information.

---

### 3. PDF / Document Extraction

The system accepts a sample pharmaceutical complaint PDF and extracts complaint information into the same structured complaint workflow.

Sample document:

```text
backend/sample_data/zenith_metformin_complaint.pdf
```

The extracted information is used to populate the complaint form and generate the corresponding AI risk assessment.

The complaint can then be modified using natural language after extraction.

---

### 4. AI Risk Assessment

The AI analyzes complaint information and provides an initial risk assessment, including relevant fields such as:

* Severity
* Risk reasoning
* Recommended action
* Investigation considerations

The risk assessment is generated as part of the complaint-processing workflow rather than being manually entered by the user.

---

### 5. Duplicate Complaint Detection

The system includes a lightweight duplicate complaint detection mechanism.

Previously committed complaints are loaded from PostgreSQL and compared with the current complaint using:

```text
TF-IDF
   ↓
Cosine Similarity
   ↓
Similarity Threshold
   ↓
Potential Duplicate Detection
```

For example, during testing, a new Amoxicillin complaint was identified as highly similar to a previously committed complaint with a similarity score of approximately **0.98**.

The system provides a warning so that users can consider whether the complaint represents a recurring issue.

---

### 6. QMS Ledger Persistence

After review, a complaint can be committed to the QMS Ledger.

The application generates a complaint ID and persists the committed complaint in PostgreSQL.

The database contains separate persistence for:

* Complaint sessions
* Committed complaints

PostgreSQL therefore acts as the persistent source of truth for committed complaint records.

---

# Technology Stack

The implementation follows the mandatory technology stack specified in the AIVOA assignment.

| Layer                | Technology       |
| -------------------- | ---------------- |
| Frontend             | React            |
| State Management     | Redux Toolkit    |
| Backend              | Python + FastAPI |
| AI Orchestration     | LangGraph        |
| LLM                  | Groq             |
| Model                | `gemma2-9b-it`   |
| Database             | PostgreSQL       |
| UI Font              | Inter            |
| Local Infrastructure | Docker Compose   |

---

# Architecture

```text
┌──────────────────────────────┐
│        React + Redux         │
│                              │
│  Complaint Form + AI Copilot │
└──────────────┬───────────────┘
               │
               │ HTTP
               ▼
┌──────────────────────────────┐
│          FastAPI             │
│                              │
│  Chat / Upload / Commit API  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          LangGraph           │
│                              │
│  Intent Classification       │
│  Complaint Logging           │
│  Complaint Editing           │
│  Document Processing         │
│  Completeness Checking       │
│  Risk Assessment             │
│  Duplicate Detection         │
└──────────────┬───────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐ ┌──────────────┐
│  Groq LLM    │ │ PostgreSQL   │
│              │ │              │
│ Extraction   │ │ Sessions     │
│ Reasoning    │ │ Complaints   │
└──────────────┘ └──────────────┘
```

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
│   │   └── schemas.py
│   │
│   ├── sample_data/
│   │   └── zenith_metformin_complaint.pdf
│   │
│   ├── scripts/
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
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

* Python
* Node.js / npm
* Docker Desktop
* A Groq API key

---

## 1. Clone the repository

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

The PostgreSQL service is exposed on port `5432`.

---

## 3. Configure the backend

Create the local environment file from the provided template.

From the `backend` directory:

```powershell
cd backend
copy .env.example .env
```

Add your Groq API key to `.env`:

```text
GROQ_API_KEY=your_groq_api_key
```

**Never commit `.env` or API keys to Git.**

---

## 4. Start the backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## 5. Install and start the frontend

Open a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# Demonstration Workflow

## Test 1 — Log Complaint

Enter:

> Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. Batch number AMX240602. Manufacturing date March 2026. Expiry date February 2028. Please log this complaint.

Expected behavior:

* Complaint details are extracted
* Complaint form is populated
* AI risk assessment is generated

---

## Test 2 — Edit Complaint

Enter:

> Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.

Expected behavior:

* Batch number changes
* Affected quantity is updated
* Existing complaint information is preserved

---

## Test 3 — PDF Extraction

Upload:

```text
backend/sample_data/zenith_metformin_complaint.pdf
```

Expected behavior:

* Complaint information is extracted
* Form fields are populated
* AI risk assessment is generated

---

## Test 4 — Edit After PDF Extraction

Enter:

> Sorry, the batch number is CHG260712A and affected quantity is 50 kg, 2 HDPE drums.

Expected behavior:

* Extracted complaint state is updated
* Existing extracted information is preserved

---

## Test 5 — Commit to QMS Ledger

Click:

**Commit to QMS Ledger**

The complaint is persisted to PostgreSQL as a committed complaint record.

---

## Test 6 — Duplicate Complaint Detection

Submit a new complaint similar to a previously committed complaint.

The system compares the complaint against historical committed complaints and reports a potential duplicate when the similarity exceeds the configured threshold.

---

# Design Decisions

## Sparse State Updates

The most important design decision is that AI editing produces **sparse patches** rather than complete replacement forms.

For example:

```json
{
  "batch_number": "BMX240602",
  "affected_quantity": "48 capsules"
}
```

The backend then merges these changes into the existing validated complaint state.

This makes conversational editing safer and preserves information that the user did not ask to change.

---

## Separation of Responsibilities

The system separates:

```text
LLM reasoning
      ↓
Structured state
      ↓
Application validation
      ↓
State mutation
      ↓
Persistence
```

The LLM is responsible for understanding natural-language requests and producing structured information.

Application code remains responsible for state management, validation, workflow orchestration, and database persistence.

---

## PostgreSQL as Source of Truth

Committed complaints are persisted in PostgreSQL.

The duplicate detection component loads committed complaint records from the database before performing similarity comparison.

This keeps historical complaint data independent of the in-memory duplicate detection component.

---

# Validation Performed

The complete workflow was tested locally, including:

* Natural-language complaint logging
* AI risk assessment
* Natural-language complaint editing
* PDF complaint extraction
* Editing after PDF extraction
* QMS Ledger commit
* PostgreSQL persistence
* Duplicate complaint detection

The duplicate detection workflow was also tested against a previously committed complaint and produced a high similarity score of approximately `0.98`.

---

# Scope and Limitations

This project is a prototype created for the AIVOA technical challenge.

It is **not** a validated pharmaceutical GxP / 21 CFR Part 11 production system.

It does not process real patient data and should not be used as a production quality-management system without appropriate validation, security controls, auditability, access control, regulatory compliance, and human review.

Document extraction is intended for demonstration purposes and is not positioned as production-grade OCR or document-understanding infrastructure.

---

# Future Improvements

Potential production-oriented extensions include:

1. Historical complaint similarity using `pgvector`
2. Evidence panels for related and duplicate complaints
3. Investigation and root-cause hypothesis generation
4. CAPA workflow and tracking
5. Audit-event timeline
6. Automated evaluation dataset for extraction and editing accuracy
7. Authentication and role-based access control
8. Stronger validation and auditability for regulated environments
9. Human-in-the-loop approval workflows
10. Production document/OCR processing

---

# AIVOA Challenge

This project was developed for the **AIVOA Round 1 AI Product Engineer** technical challenge.

The implementation follows the required workflow of using an AI Copilot to populate and update the customer complaint form rather than requiring the user to manually enter the complaint information.
