from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List

from dateutil import parser as date_parser


VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
VALID_SEVERITIES = {"Critical", "Major", "Minor"}


def validate_complaint(form_state: Any) -> List[str]:
    """
    Run deterministic business-rule validation against the current
    ComplaintState.

    The LLM is responsible for extracting and recommending values.
    This module validates those values using deterministic rules.
    """

    errors: List[str] = []

    # ------------------------------------------------------------------
    # Manufacturing Date / Expiry Date
    # ------------------------------------------------------------------

    if form_state.manufacturing_date and form_state.expiry_date:
        try:
            manufacturing_date = date_parser.parse(
                form_state.manufacturing_date,
                default=datetime(1900, 1, 1),
            )
            expiry_date = date_parser.parse(
                form_state.expiry_date,
                default=datetime(1900, 1, 1),
            )

            if expiry_date < manufacturing_date:
                errors.append(
                    "Expiry Date cannot be earlier than Manufacturing Date."
                )

        except (ValueError, TypeError, OverflowError):
            errors.append(
                "Manufacturing Date or Expiry Date could not be validated."
            )

    # ------------------------------------------------------------------
    # Complaint Date
    # ------------------------------------------------------------------

    if form_state.complaint_date:
        try:
            complaint_date = date_parser.parse(
                form_state.complaint_date,
                default=datetime(1900, 1, 1),
            )

            if complaint_date.date() > datetime.now(timezone.utc).date():
                errors.append(
                    "Complaint Date cannot be in the future."
                )

        except (ValueError, TypeError, OverflowError):
            errors.append(
                "Complaint Date could not be validated."
            )

    # ------------------------------------------------------------------
    # Priority
    # ------------------------------------------------------------------

    if form_state.priority and form_state.priority not in VALID_PRIORITIES:
        errors.append(
            "Priority must be Low, Medium, High, or Urgent."
        )

    # ------------------------------------------------------------------
    # Initial Severity
    # ------------------------------------------------------------------

    severity = form_state.risk_assessment.severity

    if severity and severity not in VALID_SEVERITIES:
        errors.append(
            "Initial Severity must be Critical, Major, or Minor."
        )

    return errors