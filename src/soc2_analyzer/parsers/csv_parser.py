"""CSV evidence file parser."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from soc2_analyzer.models import EvidenceFile


def parse_csv(filepath: Path) -> EvidenceFile:
    """Read a CSV file and format its contents as readable text.

    Args:
        filepath: Path to the CSV file.

    Returns:
        EvidenceFile with CSV data formatted as a readable table.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    with filepath.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        extracted_text = "[Empty CSV file]"
    else:
        header = rows[0]
        lines: list[str] = [" | ".join(header), "-" * (len(" | ".join(header)))]
        for row in rows[1:]:
            lines.append(" | ".join(row))
        extracted_text = "\n".join(lines)

    return EvidenceFile(
        filename=filepath.name,
        filepath=str(filepath),
        file_type="csv",
        extracted_text=extracted_text,
        parse_timestamp=datetime.now(timezone.utc),
    )
