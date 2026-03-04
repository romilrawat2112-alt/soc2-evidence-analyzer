"""Mapper utilities for formatting control definitions for LLM prompts."""

from soc2_analyzer.models import ControlDefinition


def format_controls_for_mapping(controls: list[ControlDefinition]) -> str:
    """Format control IDs and titles into a string for the mapping prompt.

    This produces a numbered list of controls that can be embedded in an LLM
    prompt so the model can identify which controls are relevant to a piece
    of evidence.

    Args:
        controls: List of loaded control definitions.

    Returns:
        A formatted string listing each control's ID, title, and category.
    """
    if not controls:
        return "No controls defined."

    lines: list[str] = []
    for idx, control in enumerate(controls, start=1):
        lines.append(
            f"{idx}. {control.id}: {control.title} ({control.category})"
        )

    return "\n".join(lines)
