# AIVOA Complaint Intelligence Workbench

An AI-powered pharmaceutical customer complaint intake and triage prototype
built around the exact Round-1 AIVOA workflow:

**Natural-language complaint → Log Complaint → AI risk assessment → form update → natural-language edit → PDF/email extraction → QMS commit**

The implementation uses the mandatory stack:

- React + Redux Toolkit
- Python + FastAPI
- LangGraph
- Groq `gemma2-9b-it`
- PostgreSQL
- Google Inter font

## Why this version

This repository combines the strongest parts of the two provided project
archives.

The `aivoa-complaint-system` archive is used as the UI/workflow foundation
because it already closely matches the supplied AIVOA demo: read-only
AI-populated form, Copilot panel, natural-language editing, PDF extraction,
field-change highlighting, CAPA recommendation, duplicate detection, and QMS
commit.

The implementation is strengthened with:

1. **Sparse state diffs** for safe edits. An edit such as changing only the
   batch number cannot erase unrelated fields.
2. **PostgreSQL persistence** for complaint sessions and committed records.
3. **Deterministic completeness checking** after every AI operation.
4. Clear separation between LLM extraction/reasoning and application state
   mutation.
5. A small Docker Compose PostgreSQL setup for reproducible local development.

## Mandatory demo paths

### 1. Log complaint

Paste:

> Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500
> mg. Batch number AMX240602. Manufacturing date March 2026. Expiry date
> February 2028. Please log this complaint.

The Copilot should populate the left form and risk assessment.

### 2. Edit complaint

Then send:

> Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.

Only those fields should change; existing complaint information is preserved.

### 3. Document extraction

Upload:

`backend/sample_data/zenith_metformin_complaint.pdf`

The extracted complaint should populate the same form and risk assessment.
After extraction, send a natural-language correction to prove stateful editing.

## Architecture

```text
React + Redux
     |
     v
FastAPI
     |
     v
LangGraph
     |
     +--> intent classifier
     |
     +--> log complaint ------+
     |                        |
     +--> edit complaint -----+--> sparse diff --> merge state
     |                        |
     +--> document extraction-+
                                      |
                                      v
                             completeness check
                                      |
                                      v
                               risk assessment
                                      |
                                      v
                                PostgreSQL
```

## Fast setup

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env
```

Set `GROQ_API_KEY` in `.env`.

Then:

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Interview-critical design decision

The AI tools return **sparse patches**, not entire forms.

```text
Current state
    +
User correction
    |
    v
LLM produces only changed fields
    |
    v
Pydantic validation
    |
    v
single merge_state node
    |
    v
updated complaint
```

This directly addresses the demo's requirement that correcting the batch number
and quantity must preserve all other complaint information.

## Scope boundary

This is a prototype inspired by pharmaceutical QMS workflows. It is **not**
a validated GxP/21 CFR Part 11 production system and does not process real
patient data.

## Next high-value extensions

After the mandatory workflow is stable:

1. historical complaint similarity using pgvector
2. related/duplicate complaint evidence panel
3. investigation/root-cause hypotheses
4. CAPA workspace
5. audit-event timeline
6. evaluation dataset for extraction/edit accuracy
