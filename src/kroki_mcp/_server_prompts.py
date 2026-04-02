"""MCP prompt registrations — diagram syntax helper.

Exposes ``diagram_helper`` which provides syntax guidance for a given
diagram type plus instructions to use ``render_diagram``.
"""

from __future__ import annotations

from fastmcp import FastMCP

_SYNTAX_HINTS: dict[str, str] = {
    "plantuml": (
        "PlantUML uses a text-based syntax for UML diagrams.\n\n"
        "Example (sequence diagram):\n"
        "```\n"
        "@startuml\n"
        "Alice -> Bob: Hello\n"
        "Bob --> Alice: Hi there\n"
        "@enduml\n"
        "```\n\n"
        "Supports: sequence, class, activity, component, state, "
        "use case, object, deployment, and more."
    ),
    "mermaid": (
        "Mermaid uses a Markdown-inspired syntax for diagrams.\n\n"
        "Example (flowchart):\n"
        "```\n"
        "graph TD\n"
        "    A[Start] --> B{Decision}\n"
        "    B -->|Yes| C[OK]\n"
        "    B -->|No| D[Cancel]\n"
        "```\n\n"
        "Supports: flowchart, sequence, class, state, ER, Gantt, pie, and more."
    ),
    "graphviz": (
        "GraphViz uses the DOT language for graph descriptions.\n\n"
        "Example (directed graph):\n"
        "```\n"
        "digraph {\n"
        "    rankdir=LR\n"
        "    A -> B -> C\n"
        "    A -> C\n"
        "}\n"
        "```\n\n"
        "Supports: digraph (directed), graph (undirected), subgraphs, "
        "rich node/edge styling."
    ),
    "d2": (
        "D2 is a modern declarative diagram language.\n\n"
        "Example:\n"
        "```\n"
        "server -> database: queries\n"
        "server -> cache: reads\n"
        "cache -> database: misses\n"
        "```\n\n"
        "Supports: shapes, connections, containers, classes, SQL tables, "
        "sequence diagrams, grid diagrams."
    ),
    "dbml": (
        "DBML (Database Markup Language) describes database schemas.\n\n"
        "Example:\n"
        "```\n"
        "Table users {\n"
        "  id integer [primary key]\n"
        "  username varchar\n"
        "  email varchar\n"
        "}\n\n"
        "Table posts {\n"
        "  id integer [primary key]\n"
        "  user_id integer [ref: > users.id]\n"
        "  title varchar\n"
        "}\n"
        "```"
    ),
    "erd": (
        "ERD uses a simple text syntax for entity-relationship diagrams.\n\n"
        "Example:\n"
        "```\n"
        "[Person]\n"
        "*name\n"
        "height\n"
        "weight\n\n"
        "[Pet]\n"
        "*name\n"
        "breed\n\n"
        "Person *--* Pet\n"
        "```"
    ),
    "c4plantuml": (
        "C4 PlantUML creates C4 architecture diagrams using PlantUML syntax.\n\n"
        "Example (context diagram):\n"
        "```\n"
        "@startuml\n"
        "!include <C4/C4_Context>\n\n"
        "Person(user, \"User\")\n"
        "System(system, \"My System\", \"Does things\")\n"
        "Rel(user, system, \"Uses\")\n"
        "@enduml\n"
        "```\n\n"
        "Supports: Context, Container, Component, and Deployment diagrams."
    ),
}

_GENERIC_HINT = (
    "Consult the {dtype} documentation for syntax details. "
    "You can find examples at https://kroki.io/examples.html"
)


def register_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts on *mcp*.

    Args:
        mcp: The :class:`~fastmcp.FastMCP` instance to register prompts on.
    """

    @mcp.prompt()
    def diagram_helper(diagram_type: str) -> str:
        """Get syntax guidance for a diagram type.

        Args:
            diagram_type: The diagram language (e.g. ``"mermaid"``,
                ``"plantuml"``).

        Returns:
            Instructions with syntax examples and how to render.
        """
        dtype = diagram_type.lower().strip()
        hint = _SYNTAX_HINTS.get(dtype, _GENERIC_HINT.format(dtype=dtype))

        return (
            f"## {dtype} diagram syntax\n\n"
            f"{hint}\n\n"
            "## Rendering\n\n"
            "Use the `render_diagram` tool to render your diagram:\n"
            f"- `diagram_type`: `\"{dtype}\"`\n"
            "- `source`: your diagram code\n"
            "- `output_format`: `\"svg\"` (default) or `\"png\"`"
        )
