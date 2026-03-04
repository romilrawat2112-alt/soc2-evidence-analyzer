"""CLI entrypoint for SOC 2 Evidence Analyzer."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from soc2_analyzer.analyzer import analyze_directory, analyze_file
from soc2_analyzer.controls.loader import get_default_controls_dir, load_controls, get_control_by_id
from soc2_analyzer.models import Assessment
from soc2_analyzer.reports.generator import generate_html_report
from soc2_analyzer.reports.json_report import generate_json_report

app = typer.Typer(
    name="soc2-analyzer",
    help="AI-powered SOC 2 evidence analysis using Gemini.",
    no_args_is_help=True,
)
controls_app = typer.Typer(help="Manage SOC 2 control definitions.")
app.add_typer(controls_app, name="controls")

console = Console()

ASSESSMENT_COLORS = {
    Assessment.FULLY_MET: "green",
    Assessment.PARTIALLY_MET: "yellow",
    Assessment.NOT_MET: "red",
    Assessment.NOT_APPLICABLE: "dim",
}


@app.command()
def analyze(
    path: Path = typer.Argument(..., help="Path to evidence file or directory."),
    control: Optional[str] = typer.Option(None, "--control", "-c", help="Specific control ID to evaluate against."),
    auto_map: bool = typer.Option(False, "--auto-map", "-a", help="Auto-detect relevant controls using AI."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path for results JSON."),
    controls_dir: Optional[Path] = typer.Option(None, "--controls-dir", help="Path to controls YAML directory."),
) -> None:
    """Analyze evidence file(s) against SOC 2 controls."""
    if not path.exists():
        console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(1)

    if not control and not auto_map:
        console.print("[red]Error: Specify --control <ID> or --auto-map.[/red]")
        raise typer.Exit(1)

    try:
        if path.is_file():
            results = analyze_file(path, control_id=control, auto_map=auto_map, controls_dir=controls_dir)
        else:
            control_ids = [control] if control else None
            report = analyze_directory(path, control_ids=control_ids, auto_map=auto_map, controls_dir=controls_dir)
            results = report.analyses

            if output:
                if output.suffix == ".json":
                    generate_json_report(report, output)
                    console.print(f"\n[green]JSON report saved to {output}[/green]")
                else:
                    generate_html_report(report, output)
                    console.print(f"\n[green]HTML report saved to {output}[/green]")
                return

        if not results:
            console.print("[yellow]No analysis results produced.[/yellow]")
            return

        _print_results_table(results)

        if output:
            import json
            data = [r.model_dump(mode="json") for r in results]
            output.write_text(json.dumps(data, indent=2, default=str))
            console.print(f"\n[green]Results saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def report(
    path: Path = typer.Argument(..., help="Path to evidence directory."),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path (e.g., report.html or report.json)."),
    format: str = typer.Option("html", "--format", "-f", help="Output format: html or json."),
    controls_dir: Optional[Path] = typer.Option(None, "--controls-dir", help="Path to controls YAML directory."),
) -> None:
    """Generate a full analysis report from a directory of evidence."""
    if not path.exists() or not path.is_dir():
        console.print(f"[red]Error: '{path}' is not a valid directory.[/red]")
        raise typer.Exit(1)

    try:
        analysis_report = analyze_directory(path, auto_map=True, controls_dir=controls_dir)

        if format == "json" or output.suffix == ".json":
            generate_json_report(analysis_report, output)
            console.print(f"\n[green]JSON report saved to {output}[/green]")
        else:
            generate_html_report(analysis_report, output)
            console.print(f"\n[green]HTML report saved to {output}[/green]")

        _print_results_table(analysis_report.analyses)
        console.print(f"\n[bold]Overall Readiness Score: {analysis_report.summary.overall_readiness_score:.0%}[/bold]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@controls_app.command("list")
def controls_list(
    controls_dir: Optional[Path] = typer.Option(None, "--controls-dir", help="Path to controls YAML directory."),
) -> None:
    """List all available SOC 2 control definitions."""
    cdir = controls_dir or get_default_controls_dir()

    try:
        controls = load_controls(cdir)
    except Exception as e:
        console.print(f"[red]Error loading controls: {e}[/red]")
        raise typer.Exit(1)

    table = Table(title="SOC 2 Control Definitions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="dim")
    table.add_column("Title", style="bold")

    for c in sorted(controls, key=lambda x: x.id):
        table.add_row(c.id, c.category, c.title)

    console.print(table)
    console.print(f"\n[dim]{len(controls)} controls loaded.[/dim]")


@controls_app.command("show")
def controls_show(
    control_id: str = typer.Argument(..., help="Control ID to show details for (e.g., CC6.1)."),
    controls_dir: Optional[Path] = typer.Option(None, "--controls-dir", help="Path to controls YAML directory."),
) -> None:
    """Show detailed information for a specific control."""
    cdir = controls_dir or get_default_controls_dir()

    try:
        controls = load_controls(cdir)
    except Exception as e:
        console.print(f"[red]Error loading controls: {e}[/red]")
        raise typer.Exit(1)

    control = get_control_by_id(controls, control_id)
    if not control:
        console.print(f"[red]Control '{control_id}' not found.[/red]")
        console.print(f"Available: {', '.join(sorted(c.id for c in controls))}")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{control.id}[/bold cyan]: [bold]{control.title}[/bold]")
    console.print(f"[dim]Category: {control.category}[/dim]\n")
    console.print(f"[bold]Description:[/bold]\n{control.description}\n")

    console.print("[bold]Points of Focus:[/bold]")
    for p in control.points_of_focus:
        console.print(f"  • {p}")

    console.print("\n[bold]Evidence Expectations:[/bold]")
    for e in control.evidence_expectations:
        console.print(f"  • {e}")

    console.print("\n[bold]Scoring Guidance:[/bold]")
    for key, value in control.scoring_guidance.items():
        label = key.replace("_", " ").title()
        console.print(f"  [{_guidance_color(key)}]{label}:[/{_guidance_color(key)}] {value}")


def _guidance_color(key: str) -> str:
    return {
        "fully_met": "green",
        "partially_met": "yellow",
        "not_met": "red",
        "not_applicable": "dim",
    }.get(key, "white")


def _print_results_table(results: list) -> None:
    """Print analysis results as a rich table."""
    table = Table(title="Analysis Results")
    table.add_column("Control", style="cyan", no_wrap=True)
    table.add_column("Assessment")
    table.add_column("Confidence", justify="right")
    table.add_column("Quality")
    table.add_column("Key Finding", max_width=50)

    for r in results:
        color = ASSESSMENT_COLORS.get(r.assessment, "white")
        assessment_display = r.assessment.value.replace("_", " ").title()
        finding = r.gaps[0] if r.gaps else (r.strengths[0] if r.strengths else "-")

        table.add_row(
            r.control_id,
            f"[{color}]{assessment_display}[/{color}]",
            f"{r.confidence:.0%}",
            r.evidence_quality.value,
            finding,
        )

    console.print(table)
