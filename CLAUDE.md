# kroki-mcp

MCP server wrapping a self-hosted Kroki instance for diagram rendering.

## Project Structure

```
src/kroki_mcp/
  mcp_server.py        -- FastMCP server factory + auth wiring (don't modify)
  config.py            -- env var loading; KROKI_MCP_KROKI_URL + read_only
  cli.py               -- CLI entry point (serve command)
  _server_deps.py      -- lifespan: httpx.AsyncClient → Kroki
  _server_tools.py     -- render_diagram, list_diagram_types
  _server_resources.py -- kroki://health resource
  _server_prompts.py   -- diagram_helper prompt
  _diagram_types.py    -- static registry of Kroki diagram types
```

## Conventions

- Python 3.11+
- `uv` for package management, `ruff` for linting/formatting (line length 88)
- `hatchling` build backend
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Google-style docstrings on all public functions
- `logging.getLogger(__name__)` throughout, no `print()`
- Type hints everywhere

## Key Patterns

- Service object is `httpx.AsyncClient` with `base_url` pointed at Kroki
- All tools are read-only — Kroki is a rendering service with no write operations
- Diagram type validation uses static `DIAGRAM_TYPES` registry in `_diagram_types.py`
- Auth: `_build_bearer_auth()` + `_build_oidc_auth()` called in `create_server()`; MultiAuth when both set
- `_ENV_PREFIX` in `config.py` is `KROKI_MCP` — controls all env var names
- FastMCP 3.x API: use `server._lifespan_manager()` (not `test_client()`) in tests; `result.content[0]` for tool results; `result.contents[0].content` for resource results
