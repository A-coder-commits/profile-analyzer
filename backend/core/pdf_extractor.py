"""
PDF text extraction using PyMuPDF (fitz).

Extracts text page-by-page from a PDF file, cleans up whitespace artefacts,
and returns a single cleaned string ready for chunking and embedding.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str | Path) -> tuple[str, int]:
    """
    Extract and clean all text from a PDF file.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        A tuple of (cleaned_text, page_count).

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        RuntimeError: If PyMuPDF cannot open/parse the file.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise RuntimeError(f"Failed to open PDF: {exc}") from exc

    raw_pages: list[str] = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            raw_pages.append(text)

    doc.close()

    full_text = "\n\n".join(raw_pages)
    cleaned = _clean_text(full_text)
    return cleaned, len(raw_pages)


def _clean_text(text: str) -> str:
    """
    Clean extracted PDF text by removing common artefacts.

    Operations:
    - Collapse runs of 3+ newlines into 2
    - Collapse runs of 2+ spaces/tabs into 1
    - Strip common header/footer patterns (page numbers, "Page X of Y")
    - Strip leading/trailing whitespace
    """
    # Remove page-number patterns like "Page 1 of 5", "- 3 -", standalone digits
    text = re.sub(r"(?m)^[\s]*Page\s+\d+\s+of\s+\d+[\s]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^[\s]*-\s*\d+\s*-[\s]*$", "", text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse horizontal whitespace
    text = re.sub(r"[^\S\n]{2,}", " ", text)

    return text.strip()
