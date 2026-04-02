# kroki-mcp

MCP server wrapping a self-hosted [Kroki](https://kroki.io/) instance, exposing diagram rendering as MCP tools.

Supports 29+ diagram types including PlantUML, Mermaid, GraphViz, D2, DBML, ERD, and more. See [Kroki's diagram support list](https://kroki.io/#support) for the full list.

## Quick start

```bash
# Set the Kroki instance URL
export KROKI_MCP_BASE_URL=http://localhost:8000

# Install and run (stdio transport)
pip install kroki-mcp[mcp]
kroki-mcp serve
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KROKI_MCP_BASE_URL` | **Yes** | — | URL of your self-hosted Kroki instance (e.g. `http://localhost:8000`) |
| `KROKI_MCP_READ_ONLY` | No | `true` | Disable write tools |
| `KROKI_MCP_LOG_LEVEL` | No | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `KROKI_MCP_SERVER_NAME` | No | `kroki-mcp` | Server name shown to clients |
| `KROKI_MCP_INSTRUCTIONS` | No | (dynamic) | System instructions for LLM context |

## Tools

### `render_diagram`

Render a diagram using Kroki.

**Parameters:**
- `diagram_type` — diagram language (e.g. `"plantuml"`, `"mermaid"`, `"graphviz"`)
- `source` — diagram source code
- `output_format` — `"svg"` (default) or `"png"`
- `as_base64` — when `true` and format is PNG, return base64 string instead of MCP Image

### `list_diagram_types`

List all supported diagram types and their output formats. Returns a JSON array.

## Resources

### `kroki://health`

Check if the Kroki instance is reachable. Returns JSON with `status` (`"ok"` or `"unreachable"`).

## Prompts

### `diagram_helper`

Get syntax guidance and a basic example for a given diagram type, plus instructions to use `render_diagram`.

**Parameter:** `diagram_type` — e.g. `"mermaid"`, `"plantuml"`, `"graphviz"`

## Authentication

The server supports bearer token and OIDC auth for HTTP transport:

| Variable | Description |
|----------|-------------|
| `KROKI_MCP_BEARER_TOKEN` | Static bearer token |
| `KROKI_MCP_OIDC_CONFIG_URL` | OIDC discovery endpoint |
| `KROKI_MCP_OIDC_CLIENT_ID` | OIDC client ID |
| `KROKI_MCP_OIDC_CLIENT_SECRET` | OIDC client secret |
| `KROKI_MCP_OIDC_JWT_SIGNING_KEY` | JWT signing key — **required on Linux/Docker** to survive restarts |

See [Authentication guide](docs/guides/authentication.md) for full setup details.

## Docker

```bash
export KROKI_MCP_BASE_URL=http://kroki:8000
docker compose up -d
```

See [Docker deployment](docs/deployment/docker.md) for volumes, UID/GID, and Traefik setup.

## Development

```bash
uv sync --all-extras
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
```

## License

MIT
