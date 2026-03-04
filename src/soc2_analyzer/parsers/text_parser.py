"""Plain text evidence file parser for TXT, JSON, and YAML files."""

from datetime import datetime, timezone
from pathlib import Path

from soc2_analyzer.models import EvidenceFile

SUPPORTED_EXTENSIONS: set[str] = {".txt", ".json", ".yaml", ".yml"}


def parse_text(filepath: Path) -> EvidenceFile:
    """Read a text-based file as raw content.

    Supports .txt, .json, .yaml, and .yml files.

    Args:
        filepath: Path to the text file.

    Returns:
        EvidenceFile with the raw file content.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Text file not found: {filepath}")

    suffix = filepath.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported text extension: {suffix}")

    extracted_text = filepath.read_text(encoding="utf-8")
    if not extracted_text.strip():
        extracted_text = "[Empty file]"

    # Map extension to a descriptive file type
    file_type_map: dict[str, str] = {
        ".txt": "txt",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
    }

    return EvidenceFile(
        filename=filepath.name,
        filepath=str(filepath),
        file_type=file_type_map[suffix],
        extracted_text=extracted_text,
        parse_timestamp=datetime.now(timezone.utc),
    )
