"""JSON report generation."""

import json
from pathlib import Path

from soc2_analyzer.models import AnalysisReport


def generate_json_report(report: AnalysisReport, output_path: Path) -> Path:
    """Serialize an AnalysisReport to a JSON file.

    Args:
        report: The analysis report to serialize.
        output_path: Path to write the JSON file.

    Returns:
        Path to the written file.
    """
    data = report.model_dump(mode="json")
    output_path.write_text(json.dumps(data, indent=2, default=str))
    return output_path
