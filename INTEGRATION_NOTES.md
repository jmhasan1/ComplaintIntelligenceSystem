# Integration Notes

This version uses `aivoa-complaint-system` as the implementation/UI foundation and incorporates the stronger state-management ideas from `AIVOA-Complaint-Intelligence-Starter`.

## Kept from the project archive
- Reference-style React + Redux UI
- Read-only AI-populated complaint form
- Copilot chat and document upload
- LangGraph routing for log/edit/extract
- Sparse diff merge strategy
- CAPA recommendation field
- PDF sample and generator
- QMS commit interaction
- field-change highlighting

## Added/strengthened
- PostgreSQL persistence via SQLAlchemy + psycopg
- Docker Compose PostgreSQL service
- deterministic complaint completeness calculation
- persistent complaint sessions
- persistent committed complaint records
- startup `.env` loading
- safer commit validation

## Deliberately deferred until the mandatory path is stable
- pgvector historical similarity
- richer duplicate evidence panel
- investigation/root-cause workspace
- full audit-event timeline
- automated evaluation dataset

The goal is to preserve the exact AIVOA demo workflow first, then add high-value differentiators without risking the deadline.
