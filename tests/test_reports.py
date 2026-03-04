"""Tests for report generation."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from soc2_analyzer.models import (
    AnalysisReport,
    AnalysisResult,
    Assessment,
    EvidenceFile,
    EvidenceQuality,
    ReportSummary,
)
from soc2_analyzer.reports.json_report import generate_json_report
from soc2_analyzer.reports.generator import generate_html_report


@pytest.fixture
def sample_report():
    """Create a sample AnalysisReport for testing."""
    evidence = EvidenceFile(
        filename="test.txt",
        filepath="/tmp/test.txt",
        file_type="txt",
        extracted_text="Sample evidence content",
        parse_timestamp=datetime.now(timezone.utc),
    )
    analysis = AnalysisResult(
        control_id="CC6.1",
        assessment=Assessment.PARTIALLY_MET,
        confidence=0.75,
        relevance_score=0.9,
        strengths=["MFA is enabled", "Password policy is strong"],
        gaps=["Overly broad wildcard permissions"],
        reasoning="Evidence shows partial compliance with access controls.",
        recommendations=["Restrict wildcard permissions to specific services"],
        evidence_quality=EvidenceQuality.MEDIUM,
        key_observations=["IAM policy covers most requirements"],
    )
    summary = ReportSummary(
        total_controls_evaluated=1,
        fully_met=0,
        partially_met=1,
        not_met=0,
        not_applicable=0,
        overall_readiness_score=0.5,
        top_recommendations=["Restrict wildcard permissions"],
    )
    return AnalysisReport(
        report_id="test-report-001",
        generated_at=datetime.now(timezone.utc),
        evidence_files=[evidence],
        analyses=[analysis],
        summary=summary,
    )


def test_generate_json_report(tmp_path, sample_report):
    """Test JSON report generation."""
    output = tmp_path / "report.json"
    result_path = generate_json_report(sample_report, output)

    assert result_path == output
    assert output.exists()

    data = json.loads(output.read_text())
    assert data["report_id"] == "test-report-001"
    assert data["summary"]["total_controls_evaluated"] == 1
    assert len(data["analyses"]) == 1
    assert data["analyses"][0]["control_id"] == "CC6.1"


def test_generate_html_report(tmp_path, sample_report):
    """Test HTML report generation."""
    output = tmp_path / "report.html"
    result_path = generate_html_report(sample_report, output)

    assert result_path == output
    assert output.exists()

    html = output.read_text()
    assert "SOC 2 Evidence Analysis Report" in html
    assert "CC6.1" in html
    assert "Partially Met" in html
    assert "Restrict wildcard permissions" in html
