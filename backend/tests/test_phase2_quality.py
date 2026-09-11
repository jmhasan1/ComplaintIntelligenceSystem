import unittest
from datetime import datetime

from app.graph import deterministic_validation_node, _apply_diff
from app.schemas import ComplaintState, ComplaintStateUpdate


class Phase2QualityTests(unittest.TestCase):
    def test_validation_rejects_bad_date_order_and_future_complaint(self):
        state = ComplaintState(
            product_name="Test Product",
            complaint_description="Test complaint",
            manufacturing_date="2026-08-01",
            expiry_date="2026-07-01",
            complaint_date="2099-01-01",
            priority="High",
        )

        result = deterministic_validation_node({"form_state": state})
        errors = result["form_state"].validation_errors

        self.assertIn("Expiry Date cannot be earlier than Manufacturing Date.", errors)
        self.assertIn("Complaint Date cannot be in the future.", errors)
        self.assertEqual(result["form_state"].review_status, "needs_review")
        self.assertTrue(result["form_state"].review_required)

    def test_validation_accepts_valid_enums_and_dates(self):
        state = ComplaintState(
            product_name="Test Product",
            complaint_description="Test complaint",
            manufacturing_date="2026-01-01",
            expiry_date="2028-01-01",
            complaint_date=datetime.now().date().isoformat(),
            priority="High",
        )
        state.risk_assessment.severity = "Major"

        result = deterministic_validation_node({"form_state": state})

        self.assertEqual(result["form_state"].validation_errors, [])
        self.assertEqual(result["form_state"].review_status, "needs_review")

    def test_sparse_edit_preserves_unchanged_fields_and_updates_confidence(self):
        state = ComplaintState(
            product_name="Amoxicillin Capsules",
            batch_number="AMX240602",
            complaint_description="Discoloration reported.",
            field_confidence={"product_name": 0.98, "batch_number": 0.97},
        )
        diff = ComplaintStateUpdate(
            batch_number="BMX240602",
            field_confidence={"batch_number": 0.99},
        )

        updated, fields = _apply_diff(state, diff)

        self.assertEqual(updated.product_name, "Amoxicillin Capsules")
        self.assertEqual(updated.batch_number, "BMX240602")
        self.assertEqual(updated.complaint_description, "Discoloration reported.")
        self.assertEqual(updated.field_confidence["product_name"], 0.98)
        self.assertEqual(updated.field_confidence["batch_number"], 0.99)
        self.assertEqual(fields, ["batch_number"])


if __name__ == "__main__":
    unittest.main()
