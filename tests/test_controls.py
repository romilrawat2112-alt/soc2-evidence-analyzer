"""Tests for control definition loading and lookup."""

from pathlib import Path

import pytest

from soc2_analyzer.controls.loader import get_default_controls_dir, load_controls, get_control_by_id


@pytest.fixture
def controls():
    """Load all controls from the default directory."""
    controls_dir = Path(__file__).parent.parent / "controls"
    return load_controls(controls_dir)


def test_load_controls_returns_list(controls):
    """Test that controls are loaded as a list."""
    assert isinstance(controls, list)
    assert len(controls) >= 14


def test_control_has_required_fields(controls):
    """Test that each control has all required fields."""
    for c in controls:
        assert c.id
        assert c.category
        assert c.title
        assert c.description
        assert len(c.points_of_focus) > 0
        assert len(c.evidence_expectations) > 0
        assert "fully_met" in c.scoring_guidance


def test_get_control_by_id(controls):
    """Test looking up a specific control by ID."""
    control = get_control_by_id(controls, "CC6.1")
    assert control is not None
    assert control.id == "CC6.1"
    assert "access" in control.title.lower() or "access" in control.description.lower()


def test_get_control_by_id_not_found(controls):
    """Test that looking up a non-existent control returns None."""
    result = get_control_by_id(controls, "FAKE.99")
    assert result is None


def test_load_controls_invalid_dir():
    """Test that loading from a non-existent directory raises an error."""
    with pytest.raises(FileNotFoundError):
        load_controls(Path("/nonexistent/path"))
