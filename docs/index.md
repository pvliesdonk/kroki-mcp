# Kroki MCP Server

MCP server wrapping a self-hosted [Kroki](https://kroki.io/) instance, exposing diagram rendering as MCP tools.

## What's included

- **`render_diagram`** — render any diagram type to SVG or PNG via Kroki
- **`list_diagram_types`** — discover all 29+ supported diagram types
- **`kroki://health`** — check Kroki instance reachability
- **`diagram_helper`** prompt — syntax guidance for popular diagram types
- **Authentication** — bearer token, OIDC, and multi-auth (both simultaneously)
- **CI/CD** — test matrix (Python 3.11–3.14), linting, type checking, dependency audit

## Quick start

See [README.md](https://github.com/pvliesdonk/kroki-mcp/blob/main/README.md)
for the quick-start guide and full configuration reference.

## Authentication

See [Authentication guide](guides/authentication.md) for bearer token, OIDC,
and multi-auth setup.
