from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfTextError(ValueError):
    pass


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract a native PDF text layer; scanned PDFs fail as empty text."""

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, ValueError) as exc:
        raise PdfTextError(f"could not read PDF: {exc}") from exc
    return "\n".join(pages_text).strip()
