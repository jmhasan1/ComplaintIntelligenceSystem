"""
LLM provider configuration for the AIVOA Complaint Intelligence System.

The rest of the application interacts with Groq through this module rather
than depending directly on provider-specific configuration.

Environment variables:
    GROQ_API_KEY
    GROQ_MODEL_PRIMARY
    GROQ_MODEL_FALLBACK
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


# Load environment variables when this module is imported directly or
# through the FastAPI application.
load_dotenv()


PRIMARY_MODEL = os.getenv(
    "GROQ_MODEL_PRIMARY",
    "openai/gpt-oss-20b",
)

FALLBACK_MODEL = os.getenv(
    "GROQ_MODEL_FALLBACK",
    "openai/gpt-oss-20b",
)


def _get_api_key() -> str:
    """Return the Groq API key or fail with an actionable error."""
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add GROQ_API_KEY to the project's .env file."
        )

    return api_key


def get_llm(
    structured: bool = False,
    temperature: float = 0.1,
) -> ChatGroq:
    """
    Return the configured primary Groq chat model.

    structured=True is used for complaint extraction/editing where
    deterministic JSON-compatible output is required.
    """

    return ChatGroq(
        model=PRIMARY_MODEL,
        temperature=0.0 if structured else temperature,
        api_key=_get_api_key(),
    )


def get_fallback_llm(
    temperature: float = 0.0,
) -> ChatGroq:
    """Return the configured fallback Groq chat model."""

    return ChatGroq(
        model=FALLBACK_MODEL,
        temperature=temperature,
        api_key=_get_api_key(),
    )
