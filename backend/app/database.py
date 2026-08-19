
"""PostgreSQL persistence layer for the AIVOA take-home.

The graph remains storage-agnostic: it receives a ComplaintState and returns a
ComplaintState. This module persists that state between requests and stores
committed complaints for historical/duplicate analysis.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://aivoa:aivoa@localhost:5432/aivoa",
)

# Render JSON in PostgreSQL as JSONB. A SQLite URL can still be used for quick
# local smoke tests if PostgreSQL is unavailable.
if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import JSON
    JSON_TYPE = JSON
    connect_args = {"check_same_thread": False}
else:
    JSON_TYPE = JSONB
    connect_args = {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ComplaintSession(Base):
    __tablename__ = "complaint_sessions"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    state: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CommittedComplaintRecord(Base):
    __tablename__ = "committed_complaints"

    complaint_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255), default="")
    batch_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    complaint_description: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def init_db() -> None:
    Base.metadata.create_all(engine)


def load_state(session_id: str, state_model):
    with SessionLocal() as db:
        row = db.get(ComplaintSession, session_id)
        if row is None:
            return state_model()
        return state_model.model_validate(row.state)


def save_state(session_id: str, state) -> None:
    payload = state.model_dump()
    with SessionLocal() as db:
        row = db.get(ComplaintSession, session_id)
        if row is None:
            row = ComplaintSession(session_id=session_id, state=payload)
            db.add(row)
        else:
            row.state = payload
            row.updated_at = datetime.now(timezone.utc)
        db.commit()


def commit_state(session_id: str, state, complaint_id: str) -> None:
    with SessionLocal() as db:
        row = CommittedComplaintRecord(
            complaint_id=complaint_id,
            product_name=state.product_name or "",
            batch_number=state.batch_number,
            complaint_description=state.complaint_description or "",
            state=state.model_dump(),
        )
        db.add(row)
        db.commit()

        session_row = db.get(ComplaintSession, session_id)
        if session_row is not None:
            session_row.state = {}
            db.commit()


def list_committed_complaints():
    """
    Return committed complaints freshly read from PostgreSQL.

    This avoids relying on an in-memory duplicate store, which could become
    stale after a server restart or when multiple workers are running.
    """
    with SessionLocal() as db:
        rows = db.query(CommittedComplaintRecord).all()

        return [
            (
                row.complaint_id,
                row.product_name,
                row.batch_number,
                row.complaint_description,
            )
            for row in rows
        ]
