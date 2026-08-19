"""
Generates a realistic fictional pharmaceutical complaint PDF for demoing the
extract_document tool. Run:

    python scripts/generate_sample_complaint_pdf.py

Outputs to sample_data/zenith_metformin_complaint.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "zenith_metformin_complaint.pdf")

LINES = [
    ("Zenith Life Sciences Pvt. Ltd.", 16, True),
    ("Customer Quality Complaint Report", 12, False),
    ("", 10, False),
    ("Complaint Reference No: CC-2026-00154", 10, False),
    ("Date Received: 12 July 2026", 10, False),
    ("Reported By: ABC Formulations Ltd. (Procurement QA)", 10, False),
    ("Complaint Channel: Email", 10, False),
    ("", 10, False),
    ("Product Details", 12, True),
    ("Product Name: Metformin Hydrochloride API", 10, False),
    ("Grade/Strength: IP/BP", 10, False),
    ("Batch / Lot Number: MFH260712A", 10, False),
    ("Manufacturing Date: 25 June 2026", 10, False),
    ("Expiry Date: Not provided by customer", 10, False),
    ("Affected Quantity: 25 kg (1 HDPE Drum)", 10, False),
    ("", 10, False),
    ("Complaint Description", 12, True),
    (
        "During incoming raw material inspection at ABC Formulations Ltd., visible",
        10,
        False,
    ),
    (
        "foreign matter (dark fibrous particles) was observed within the Metformin",
        10,
        False,
    ),
    (
        "Hydrochloride API drum referenced above. The drum seal was intact upon",
        10,
        False,
    ),
    (
        "receipt. Customer has quarantined the batch and requests investigation,",
        10,
        False,
    ),
    ("root cause analysis, and replacement of the affected quantity.", 10, False),
    ("", 10, False),
    ("Requested Action: Investigation + Replacement", 10, False),
]


def generate():
    c = canvas.Canvas(OUT_PATH, pagesize=A4)
    width, height = A4
    y = height - 30 * mm

    for text, size, bold in LINES:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(25 * mm, y, text)
        y -= (size + 6)

    c.save()
    print(f"Sample complaint PDF written to {OUT_PATH}")


if __name__ == "__main__":
    generate()
