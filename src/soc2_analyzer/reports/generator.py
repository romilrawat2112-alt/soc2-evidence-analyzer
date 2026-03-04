"""HTML report generation using Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from soc2_analyzer.models import AnalysisReport


TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate_html_report(report: AnalysisReport, output_path: Path) -> Path:
    """Render an HTML report from an AnalysisReport.

    Args:
        report: The analysis report to render.
        output_path: Path to write the HTML file.

    Returns:
        Path to the written file.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")

    html = template.render(
        report=report,
        summary=report.summary,
        analyses=report.analyses,
        evidence_files=report.evidence_files,
    )
    output_path.write_text(html)
    return output_path
