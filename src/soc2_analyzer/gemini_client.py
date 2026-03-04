"""Gemini API client for SOC 2 evidence analysis."""

import json
import os
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from soc2_analyzer.models import (
    AnalysisResult,
    ControlDefinition,
    EvidenceFile,
)

SYSTEM_INSTRUCTION = """You are an experienced SOC 2 auditor evaluating evidence artifacts against \
Trust Services Criteria. You will be given a control requirement and an \
evidence document. Your job is to:

1. Determine if the evidence is relevant to the specified control
2. Assess whether the evidence demonstrates the control is operating effectively
3. Identify specific strengths in the evidence
4. Identify gaps or weaknesses
5. Provide a confidence-calibrated assessment

Be thorough but concise. Base your assessment only on what the evidence shows, \
not on assumptions. If evidence is ambiguous, reflect that in a lower confidence score."""

MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


def _get_client() -> genai.Client:
    """Create a Gemini API client."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Get an API key at https://aistudio.google.com/apikey and set it:\n"
            "  export GOOGLE_API_KEY=your_key_here"
        )
    return genai.Client(api_key=api_key)


def _build_analysis_prompt(evidence: EvidenceFile, control: ControlDefinition) -> str:
    """Build the user prompt for evidence analysis."""
    return f"""Analyze the following evidence against the SOC 2 control requirement.

## Control Requirement

**ID:** {control.id}
**Category:** {control.category}
**Title:** {control.title}
**Description:** {control.description}

**Points of Focus:**
{chr(10).join(f"- {p}" for p in control.points_of_focus)}

**Evidence Expectations:**
{chr(10).join(f"- {e}" for e in control.evidence_expectations)}

**Scoring Guidance:**
- Fully Met: {control.scoring_guidance.get('fully_met', 'N/A')}
- Partially Met: {control.scoring_guidance.get('partially_met', 'N/A')}
- Not Met: {control.scoring_guidance.get('not_met', 'N/A')}
- Not Applicable: {control.scoring_guidance.get('not_applicable', 'N/A')}

## Evidence

**Filename:** {evidence.filename}
**File Type:** {evidence.file_type}

**Content:**
{evidence.extracted_text if evidence.extracted_text else "[Image evidence provided - analyze the image directly]"}

Evaluate this evidence against the control and provide your assessment."""


def _build_contents(evidence: EvidenceFile, prompt: str) -> list[Any]:
    """Build the contents list, including image parts for multimodal input."""
    parts: list[Any] = []

    if evidence.image_bytes and evidence.image_mime_type:
        parts.append(
            types.Part.from_bytes(
                data=evidence.image_bytes,
                mime_type=evidence.image_mime_type,
            )
        )

    parts.append(prompt)
    return parts


def _call_with_retry(client: genai.Client, contents: list[Any], config: types.GenerateContentConfig) -> Any:
    """Call Gemini API with exponential backoff retry on transient errors."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )
            return response
        except Exception as e:
            error_str = str(e)
            is_retryable = any(code in error_str for code in ["429", "500", "503"])
            if is_retryable and attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_BASE ** attempt
                time.sleep(wait)
                continue
            raise


def analyze_evidence(evidence: EvidenceFile, control: ControlDefinition) -> AnalysisResult:
    """Analyze an evidence file against a control using Gemini.

    Args:
        evidence: Parsed evidence file with extracted content.
        control: The control definition to evaluate against.

    Returns:
        AnalysisResult with assessment, confidence, and findings.
    """
    client = _get_client()
    prompt = _build_analysis_prompt(evidence, control)
    contents = _build_contents(evidence, prompt)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "control_id": {"type": "string"},
                "assessment": {"type": "string", "enum": ["FULLY_MET", "PARTIALLY_MET", "NOT_MET", "NOT_APPLICABLE"]},
                "confidence": {"type": "number"},
                "relevance_score": {"type": "number"},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "gaps": {"type": "array", "items": {"type": "string"}},
                "reasoning": {"type": "string"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "evidence_quality": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "key_observations": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "control_id", "assessment", "confidence", "relevance_score",
                "strengths", "gaps", "reasoning", "recommendations",
                "evidence_quality", "key_observations",
            ],
        },
    )

    response = _call_with_retry(client, contents, config)
    data = json.loads(response.text)
    return AnalysisResult(**data)


def identify_relevant_controls(
    evidence: EvidenceFile, controls: list[ControlDefinition]
) -> list[str]:
    """Identify which controls are relevant to the given evidence.

    Args:
        evidence: Parsed evidence file.
        controls: List of all available control definitions.

    Returns:
        List of control IDs that are relevant to the evidence.
    """
    client = _get_client()

    controls_list = "\n".join(
        f"- {c.id}: {c.title} — {c.description[:100]}..." for c in controls
    )

    prompt = f"""Given the following evidence file, identify which SOC 2 controls it is most relevant to.

**Evidence Filename:** {evidence.filename}
**File Type:** {evidence.file_type}

**Content:**
{evidence.extracted_text if evidence.extracted_text else "[Image evidence provided - analyze the image directly]"}

**Available Controls:**
{controls_list}

Return only the control IDs that this evidence is relevant to. Select 1-3 most relevant controls."""

    contents = _build_contents(evidence, prompt)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "relevant_control_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["relevant_control_ids"],
        },
    )

    response = _call_with_retry(client, contents, config)
    data = json.loads(response.text)
    return data["relevant_control_ids"]
