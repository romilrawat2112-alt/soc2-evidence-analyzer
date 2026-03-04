"""Tests for the analysis orchestrator with mocked Gemini calls."""

from pathlib import Path
from unittest.mock import patch

import pytest

from soc2_analyzer.analyzer import _build_summary
from soc2_analyzer.models import AnalysisResult, Assessment, EvidenceQuality


@pytest.fixture
def mock_results():
    """Create sample AnalysisResult objects for testing."""
    return [
        AnalysisResult(
            control_id="CC6.1",
            assessment=Assessment.FULLY_MET,
            confidence=0.9,
            relevance_score=0.95,
            strengths=["Strong access controls"],
            gaps=[],
            reasoning="Evidence fully meets the requirement.",
            recommendations=[],
            evidence_quality=EvidenceQuality.HIGH,
            key_observations=["Well-configured IAM"],
        ),
        AnalysisResult(
            control_id="CC6.2",
            assessment=Assessment.PARTIALLY_MET,
            confidence=0.7,
            relevance_score=0.8,
            strengths=["User provisioning documented"],
            gaps=["No automated deprovisioning"],
            reasoning="Partial compliance.",
            recommendations=["Automate deprovisioning"],
            evidence_quality=EvidenceQuality.MEDIUM,
            key_observations=["Manual process in place"],
        ),
        AnalysisResult(
            control_id="CC8.1",
            assessment=Assessment.NOT_MET,
            confidence=0.85,
            relevance_score=0.6,
            strengths=[],
            gaps=["No change approval workflow", "No rollback plan"],
            reasoning="Evidence does not demonstrate change management.",
            recommendations=["Implement change advisory board", "Document rollback procedures"],
            evidence_quality=EvidenceQuality.LOW,
            key_observations=["No formal process"],
        ),
    ]


def test_build_summary(mock_results):
    """Test summary calculation from results."""
    summary = _build_summary(mock_results)
    assert summary.total_controls_evaluated == 3
    assert summary.fully_met == 1
    assert summary.partially_met == 1
    assert summary.not_met == 1
    assert summary.not_applicable == 0
    assert summary.overall_readiness_score == 0.5  # (1.0 + 0.5 + 0.0) / 3


def test_build_summary_empty():
    """Test summary with no results."""
    summary = _build_summary([])
    assert summary.total_controls_evaluated == 0
    assert summary.overall_readiness_score == 0.0


def test_build_summary_all_not_applicable():
    """Test summary when all controls are N/A."""
    results = [
        AnalysisResult(
            control_id="CC6.4",
            assessment=Assessment.NOT_APPLICABLE,
            confidence=0.95,
            relevance_score=0.1,
            strengths=[],
            gaps=[],
            reasoning="Not applicable.",
            recommendations=[],
            evidence_quality=EvidenceQuality.LOW,
            key_observations=[],
        ),
    ]
    summary = _build_summary(results)
    assert summary.overall_readiness_score == 0.0
    assert summary.not_applicable == 1
