"""Core analysis orchestration - ties parsers, controls, and Gemini client together."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.status import Status

from soc2_analyzer import gemini_client
from soc2_analyzer.controls.loader import get_default_controls_dir, load_controls, get_control_by_id
from soc2_analyzer.models import (
    AnalysisReport,
    AnalysisResult,
    Assessment,
    EvidenceFile,
    ReportSummary,
)
from soc2_analyzer.parsers import SUPPORTED_EXTENSIONS, parse_evidence

console = Console()


def analyze_file(
    filepath: Path,
    control_id: str | None = None,
    auto_map: bool = False,
    controls_dir: Path | None = None,
) -> list[AnalysisResult]:
    """Analyze a single evidence file against one or more controls.

    Args:
        filepath: Path to the evidence file.
        control_id: Specific control ID to evaluate against.
        auto_map: If True, use AI to detect relevant controls.
        controls_dir: Optional path to controls directory.

    Returns:
        List of AnalysisResult objects.
    """
    if not control_id and not auto_map:
        raise ValueError("Either --control or --auto-map must be specified.")

    cdir = controls_dir or get_default_controls_dir()
    controls = load_controls(cdir)

    with console.status("[bold cyan]Parsing evidence file...") as _:
        evidence = parse_evidence(filepath)

    results: list[AnalysisResult] = []

    if control_id:
        control = get_control_by_id(controls, control_id)
        if not control:
            raise ValueError(
                f"Control '{control_id}' not found. "
                f"Available: {', '.join(c.id for c in controls)}"
            )
        with console.status(f"[bold cyan]Analyzing against {control.id}...") as _:
            result = gemini_client.analyze_evidence(evidence, control)
        results.append(result)

    elif auto_map:
        with console.status("[bold cyan]Identifying relevant controls...") as _:
            relevant_ids = gemini_client.identify_relevant_controls(evidence, controls)

        if not relevant_ids:
            console.print("[yellow]No relevant controls identified for this evidence.[/yellow]")
            return results

        console.print(f"[green]Mapped to controls: {', '.join(relevant_ids)}[/green]")

        for rid in relevant_ids:
            control = get_control_by_id(controls, rid)
            if not control:
                console.print(f"[yellow]Warning: Control '{rid}' returned by AI not found in library, skipping.[/yellow]")
                continue
            with console.status(f"[bold cyan]Analyzing against {control.id}...") as _:
                result = gemini_client.analyze_evidence(evidence, control)
            results.append(result)

    return results


def analyze_directory(
    dirpath: Path,
    control_ids: list[str] | None = None,
    auto_map: bool = False,
    controls_dir: Path | None = None,
) -> AnalysisReport:
    """Analyze all supported evidence files in a directory.

    Args:
        dirpath: Path to directory containing evidence files.
        control_ids: Optional list of control IDs to evaluate against.
        auto_map: If True, use AI to detect relevant controls for each file.
        controls_dir: Optional path to controls directory.

    Returns:
        AnalysisReport with all results and summary.
    """
    if not control_ids and not auto_map:
        auto_map = True

    evidence_files: list[EvidenceFile] = []
    all_results: list[AnalysisResult] = []

    supported_files = [
        f for f in sorted(dirpath.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not supported_files:
        raise ValueError(f"No supported evidence files found in {dirpath}")

    console.print(f"[bold]Found {len(supported_files)} evidence files to analyze.[/bold]\n")

    for filepath in supported_files:
        console.print(f"[bold blue]Processing:[/bold blue] {filepath.name}")
        try:
            if control_ids:
                for cid in control_ids:
                    results = analyze_file(filepath, control_id=cid, controls_dir=controls_dir)
                    all_results.extend(results)
            else:
                results = analyze_file(filepath, auto_map=True, controls_dir=controls_dir)
                all_results.extend(results)

            evidence = parse_evidence(filepath)
            evidence_files.append(evidence)
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
            continue

        console.print()

    summary = _build_summary(all_results)

    return AnalysisReport(
        report_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc),
        evidence_files=evidence_files,
        analyses=all_results,
        summary=summary,
    )


def _build_summary(results: list[AnalysisResult]) -> ReportSummary:
    """Build a summary from a list of analysis results."""
    if not results:
        return ReportSummary(
            total_controls_evaluated=0,
            fully_met=0,
            partially_met=0,
            not_met=0,
            not_applicable=0,
            overall_readiness_score=0.0,
            top_recommendations=[],
        )

    fully_met = sum(1 for r in results if r.assessment == Assessment.FULLY_MET)
    partially_met = sum(1 for r in results if r.assessment == Assessment.PARTIALLY_MET)
    not_met = sum(1 for r in results if r.assessment == Assessment.NOT_MET)
    not_applicable = sum(1 for r in results if r.assessment == Assessment.NOT_APPLICABLE)

    scoreable = [r for r in results if r.assessment != Assessment.NOT_APPLICABLE]
    if scoreable:
        score_map = {
            Assessment.FULLY_MET: 1.0,
            Assessment.PARTIALLY_MET: 0.5,
            Assessment.NOT_MET: 0.0,
        }
        readiness = sum(score_map.get(r.assessment, 0) for r in scoreable) / len(scoreable)
    else:
        readiness = 0.0

    all_recommendations = []
    for r in results:
        all_recommendations.extend(r.recommendations)

    return ReportSummary(
        total_controls_evaluated=len(results),
        fully_met=fully_met,
        partially_met=partially_met,
        not_met=not_met,
        not_applicable=not_applicable,
        overall_readiness_score=round(readiness, 2),
        top_recommendations=all_recommendations[:10],
    )
