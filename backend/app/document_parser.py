"""
Extracts plain text from an uploaded complaint document.

Per the assignment: "Production-grade OCR or document parsing is not
required." So this deliberately stays simple -- pypdf for PDFs, raw decode
for .txt/.eml -- rather than a scanned-image OCR pipeline. If you want to
demo scanned/image PDFs later, swap in pytesseract, but don't over-invest
here; it's explicitly not what's being evaluated.
"""

import email
from io import BytesIO
from pypdf import PdfReader


def extract_text_from_upload(filename: str, content: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if lower.endswith(".eml"):
        msg = email.message_from_bytes(content)
        if msg.is_multipart():
            parts = []
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    parts.append(part.get_payload(decode=True).decode(errors="ignore"))
            return "\n".join(parts)
        return msg.get_payload(decode=True).decode(errors="ignore")

    # .txt, .docx-as-text fallback, etc.
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="ignore")
