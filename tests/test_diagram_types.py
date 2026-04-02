"""Tests for the diagram types registry."""

from __future__ import annotations


def test_diagram_types_is_non_empty_dict() -> None:
    from kroki_mcp._diagram_types import DIAGRAM_TYPES

    assert isinstance(DIAGRAM_TYPES, dict)
    assert len(DIAGRAM_TYPES) > 20


def test_all_types_have_svg() -> None:
    """Every diagram type must support at least SVG."""
    from kroki_mcp._diagram_types import DIAGRAM_TYPES

    for dtype, formats in DIAGRAM_TYPES.items():
        assert "svg" in formats, f"{dtype} is missing 'svg' format"


def test_formats_are_within_allowed_set() -> None:
    from kroki_mcp._diagram_types import DIAGRAM_TYPES

    allowed = {"svg", "png"}
    for dtype, formats in DIAGRAM_TYPES.items():
        for fmt in formats:
            assert fmt in allowed, f"{dtype} has unexpected format '{fmt}'"


def test_known_types_present() -> None:
    """Spot-check the most commonly used types."""
    from kroki_mcp._diagram_types import DIAGRAM_TYPES

    for expected in ("plantuml", "mermaid", "graphviz", "d2", "erd"):
        assert expected in DIAGRAM_TYPES, f"Missing expected type '{expected}'"
