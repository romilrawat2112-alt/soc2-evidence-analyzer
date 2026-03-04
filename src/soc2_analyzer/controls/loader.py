"""Loader for SOC 2 control definition YAML files."""

from pathlib import Path

import yaml

from soc2_analyzer.models import ControlDefinition


def get_default_controls_dir() -> Path:
    """Return the default controls directory relative to the project root.

    The controls directory is located at the top level of the project,
    three levels up from this module file:
        project_root/controls/
        project_root/src/soc2_analyzer/controls/loader.py
    """
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    return project_root / "controls"


def load_controls(controls_dir: Path) -> list[ControlDefinition]:
    """Load all control definitions from YAML files in the given directory.

    Args:
        controls_dir: Path to the directory containing control YAML files.

    Returns:
        A list of validated ControlDefinition instances.

    Raises:
        FileNotFoundError: If the controls directory does not exist.
        ValueError: If a YAML file contains invalid control data.
    """
    if not controls_dir.is_dir():
        raise FileNotFoundError(f"Controls directory not found: {controls_dir}")

    controls: list[ControlDefinition] = []

    for yaml_path in sorted(controls_dir.glob("*.yaml")):
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "controls" not in data:
            continue

        for entry in data["controls"]:
            try:
                control = ControlDefinition(**entry)
                controls.append(control)
            except Exception as exc:
                raise ValueError(
                    f"Invalid control definition in {yaml_path.name}: {exc}"
                ) from exc

    return controls


def get_control_by_id(
    controls: list[ControlDefinition], control_id: str
) -> ControlDefinition | None:
    """Look up a single control by its ID.

    Args:
        controls: List of loaded control definitions.
        control_id: The control identifier to search for (e.g. "CC6.1").

    Returns:
        The matching ControlDefinition, or None if not found.
    """
    for control in controls:
        if control.id == control_id:
            return control
    return None
