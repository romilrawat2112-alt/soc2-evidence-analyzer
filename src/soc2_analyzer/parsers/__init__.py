"""Evidence file parsers.

Provides a unified ``parse_evidence`` dispatcher that routes files
to the correct parser based on their extension.
"""

from pathlib import Path

from soc2_analyzer.models import EvidenceFile
from soc2_analyzer.parsers.csv_parser import parse_csv
from soc2_analyzer.parsers.image_parser import parse_image
from soc2_analyzer.parsers.pdf_parser import parse_pdf
from soc2_analyzer.parsers.text_parser import parse_text


class UnsupportedFileTypeError(Exception):
    """Raised when a file's extension has no registered parser."""


# Extension-to-parser routing table
_PARSER_MAP: dict[str, callable] = {
    ".pdf": parse_pdf,
    ".png": parse_image,
    ".jpg": parse_image,
    ".jpeg": parse_image,
    ".csv": parse_csv,
    ".txt": parse_text,
    ".json": parse_text,
    ".yaml": parse_text,
    ".yml": parse_text,
}

SUPPORTED_EXTENSIONS: set[str] = set(_PARSER_MAP.keys())


def parse_evidence(filepath: Path) -> EvidenceFile:
    """Parse an evidence file by dispatching to the appropriate parser.

    Args:
        filepath: Path to the evidence file.

    Returns:
        EvidenceFile with extracted or loaded content.

    Raises:
        UnsupportedFileTypeError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    suffix = filepath.suffix.lower()
    parser = _PARSER_MAP.get(suffix)
    if parser is None:
        raise UnsupportedFileTypeError(
            f"No parser for '{suffix}' files. "
            f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    return parser(filepath)


__all__ = [
    "EvidenceFile",
    "UnsupportedFileTypeError",
    "parse_evidence",
    "parse_csv",
    "parse_image",
    "parse_pdf",
    "parse_text",
    "SUPPORTED_EXTENSIONS",
]
