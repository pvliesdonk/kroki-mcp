"""Static registry of Kroki diagram types and their supported output formats.

Kroki does not expose a discovery endpoint, so this mapping is maintained
manually.  Used by :func:`list_diagram_types`, :func:`render_diagram`
(input validation), and :func:`diagram_helper`.

See https://kroki.io/#support for the canonical list.
"""

from __future__ import annotations

DIAGRAM_TYPES: dict[str, list[str]] = {
    "actdiag": ["svg", "png"],
    "blockdiag": ["svg", "png"],
    "bpmn": ["svg", "png"],
    "bytefield": ["svg", "png"],
    "c4plantuml": ["svg", "png"],
    "d2": ["svg", "png"],
    "dbml": ["svg", "png"],
    "ditaa": ["svg", "png"],
    "erd": ["svg", "png"],
    "excalidraw": ["svg", "png"],
    "graphviz": ["svg", "png"],
    "mermaid": ["svg", "png"],
    "nomnoml": ["svg", "png"],
    "nwdiag": ["svg", "png"],
    "packetdiag": ["svg", "png"],
    "pikchr": ["svg", "png"],
    "plantuml": ["svg", "png"],
    "rackdiag": ["svg", "png"],
    "seqdiag": ["svg", "png"],
    "structurizr": ["svg", "png"],
    "svgbob": ["svg"],
    "symbolator": ["svg", "png"],
    "tikz": ["svg", "png"],
    "typst": ["svg", "png"],
    "umlet": ["svg", "png"],
    "vega": ["svg", "png"],
    "vegalite": ["svg", "png"],
    "wavedrom": ["svg", "png"],
    "wireviz": ["svg", "png"],
}
