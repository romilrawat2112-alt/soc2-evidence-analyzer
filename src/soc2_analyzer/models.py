"""Pydantic data models for SOC 2 evidence analysis."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Assessment(str, Enum):
    """Control assessment status."""
    FULLY_MET = "FULLY_MET"
    PARTIALLY_MET = "PARTIALLY_MET"
    NOT_MET = "NOT_MET"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceQuality(str, Enum):
    """Quality rating of the evidence provided."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ControlDefinition(BaseModel):
    """A SOC 2 Trust Services Criteria control definition."""
    id: str
    category: str
    title: str
    description: str
    points_of_focus: list[str]
    evidence_expectations: list[str]
    scoring_guidance: dict[str, str]


class AnalysisResult(BaseModel):
    """Result of analyzing evidence against a single control."""
    control_id: str
    assessment: Assessment
    confidence: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    strengths: list[str]
    gaps: list[str]
    reasoning: str
    recommendations: list[str]
    evidence_quality: EvidenceQuality
    key_observations: list[str]


class EvidenceFile(BaseModel):
    """Parsed evidence file with extracted content."""
    filename: str
    filepath: str
    file_type: str
    extracted_text: str
    parse_timestamp: datetime
    image_bytes: Optional[bytes] = Field(default=None, exclude=True)
    image_mime_type: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class ReportSummary(BaseModel):
    """Summary statistics for an analysis report."""
    total_controls_evaluated: int
    fully_met: int
    partially_met: int
    not_met: int
    not_applicable: int
    overall_readiness_score: float = Field(ge=0.0, le=1.0)
    top_recommendations: list[str]


class AnalysisReport(BaseModel):
    """Complete analysis report with all results and summary."""
    report_id: str
    generated_at: datetime
    evidence_files: list[EvidenceFile]
    analyses: list[AnalysisResult]
    summary: ReportSummary
