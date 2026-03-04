"""PDF evidence file parser using PyMuPDF."""

from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

from soc2_analyzer.models import EvidenceFile


def parse_pdf(filepath: Path) -> EvidenceFile:
    """Extract text content from a PDF file.

    Args:
        filepath: Path to the PDF file.

    Returns:
        EvidenceFile with extracted text from all pages.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If the PDF cannot be read.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"PDF file not found: {filepath}")

    try:
        doc = fitz.open(filepath)
    except Exception as exc:
        raise RuntimeError(f"Failed to open PDF: {filepath}") from exc

    pages: list[str] = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append(f"--- Page {page_num} ---\n{text}")
    doc.close()

    extracted_text = "\n\n".join(pages) if pages else "[No extractable text found in PDF]"

    return EvidenceFile(
        filename=filepath.name,
        filepath=str(filepath),
        file_type="pdf",
        extracted_text=extracted_text,
        parse_timestamp=datetime.now(timezone.utc),
    )
