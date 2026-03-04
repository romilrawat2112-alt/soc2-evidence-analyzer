"""Image evidence file parser for multimodal Gemini analysis."""

from datetime import datetime, timezone
from pathlib import Path

from soc2_analyzer.models import EvidenceFile

MIME_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def parse_image(filepath: Path) -> EvidenceFile:
    """Read an image file for multimodal analysis by Gemini.

    Stores raw bytes and MIME type so the image can be sent directly
    to the Gemini vision API. No OCR is performed locally.

    Args:
        filepath: Path to the image file.

    Returns:
        EvidenceFile with raw image bytes and MIME type.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the image extension is not supported.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Image file not found: {filepath}")

    suffix = filepath.suffix.lower()
    mime_type = MIME_TYPES.get(suffix)
    if mime_type is None:
        raise ValueError(f"Unsupported image extension: {suffix}")

    image_bytes = filepath.read_bytes()

    return EvidenceFile(
        filename=filepath.name,
        filepath=str(filepath),
        file_type="image",
        extracted_text="[Image content — awaiting multimodal analysis]",
        parse_timestamp=datetime.now(timezone.utc),
        image_bytes=image_bytes,
        image_mime_type=mime_type,
    )
