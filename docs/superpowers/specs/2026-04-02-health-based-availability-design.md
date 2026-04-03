# Health-Based Availability Filtering & Public Default — Design Spec

## Overview

Two related improvements to `kroki-mcp`:

1. **Default URL**: make `KROKI_MCP_KROKI_URL` optional, defaulting to the public
   `https://kroki.io` instance, with a startup warning.
2. **Health-based filtering**: at startup, call `GET /health` on the configured
   Kroki instance and use the response to determine which diagram types are
   actually available. Only available types are exposed to the LLM — unavailable
   types are silently omitted.

## Motivation

- Self-hosted Kroki instances may not run all companion containers (mermaid, bpmn,
  excalidraw require separate services). Offering those types when they're not
  available wastes LLM tokens and produces confusing errors.
- The public `https://kroki.io` is a fully-functional zero-config default for
  development and evaluation, but should not be used silently — a warning makes
  it clear the server is using a third-party service.

## Health Endpoint

`GET /health` (same base URL as rendering requests) returns:

```json
{
  "status": "pass",
  "version": {
    "plantuml": "1.2026.1",
    "mermaid": "11.12.3",
    "dot": "9.0.0",
    "graphviz": "9.0.0",
    "kroki": { "number": "0.30.1", "build_hash": "e8fa380" },
    ...
  }
}
```

Keys in `version` correspond to running services. The special key `"kroki"` is
the server itself (value is a nested object, not a version string) and is ignored.

## Key Mapping

Health key names match `DIAGRAM_TYPES` keys directly, with one exception:

| Health key | DIAGRAM_TYPES key | Notes |
|------------|-------------------|-------|
| `dot` | — | Graphviz alias; ignored (health also reports `graphviz` directly) |
| `diagramsnet` | — | Not yet in registry; tracked in issue #4 |
| `typst` | `typst` | Not reported by health on tested instances; treated as unavailable |

All other health keys match `DIAGRAM_TYPES` keys 1:1.

## Configuration Changes

### `config.py`

`KROKI_MCP_KROKI_URL` becomes optional. Default: `"https://kroki.io"`.

```python
_PUBLIC_KROKI_URL = "https://kroki.io/"

raw_kroki_url = (_env("KROKI_URL") or "").strip()
using_public = not raw_kroki_url
kroki_url = (raw_kroki_url.rstrip("/") + "/") if raw_kroki_url else _PUBLIC_KROKI_URL
```

`ServerConfig` gains a `using_public_instance: bool` field so the lifespan can
log the appropriate warning.

## Lifespan Changes

### `_server_deps.py`

After creating the httpx client, the lifespan calls `GET health` (relative path)
and parses the response:

```python
available = await _probe_available_types(client)
yield {"service": client, "config": config, "available": available}
```

`_probe_available_types(client)` returns a `frozenset[str]` of `DIAGRAM_TYPES`
keys that are available on this instance:

- Parse `version` keys from the health response.
- Intersect with `DIAGRAM_TYPES` keys (ignores `dot`, `diagramsnet`, `kroki`, etc.).
- On any error (connection failure, non-200 response, malformed JSON): log a
  `WARNING` and return `frozenset(DIAGRAM_TYPES)` — i.e. fall back to the full
  static registry.

### Startup warnings

Logged at `WARNING` level:

- **Public instance in use**: `"KROKI_MCP_KROKI_URL not set — using public https://kroki.io. Not suitable for production; diagram source is sent to a third-party server."`
- **Health probe failed**: `"Could not reach GET /health at {url} — falling back to static type registry. All {n} types will be offered but some may not be available."`

## Tool Changes

### `get_available_types(ctx)` — new helper in `_server_deps.py`

```python
def get_available_types(ctx: Context = CurrentContext()) -> frozenset[str]:
    available = ctx.lifespan_context.get("available")
    if available is None:
        return frozenset(DIAGRAM_TYPES)
    return available
```

### `list_diagram_types`

Accepts `available: frozenset[str] = Depends(get_available_types)` and filters
`DIAGRAM_TYPES` to only include keys in `available`:

```python
entries = [
    {"type": dtype, "formats": formats}
    for dtype, formats in sorted(DIAGRAM_TYPES.items())
    if dtype in available
]
```

### `render_diagram`

Accepts `available: frozenset[str] = Depends(get_available_types)` and validates
against `available` instead of all of `DIAGRAM_TYPES`:

```python
if diagram_type not in available:
    return (
        f"Unknown diagram type '{diagram_type}'. "
        "Use list_diagram_types to see what is available on this instance."
    )
```

The existing `output_format` validation still checks `DIAGRAM_TYPES[diagram_type]`
(format support is static, not instance-dependent).

## Documentation Changes

- `README.md`: update config table — `KROKI_MCP_KROKI_URL` is now optional with
  default `https://kroki.io`.
- `server.json`: mark `KROKI_MCP_KROKI_URL` as `"required": false` in both
  pypi and oci packages, add `"default": "https://kroki.io"`.
- `CLAUDE.md`: note the `available` key in lifespan context.

## Testing

| Test | Description |
|------|-------------|
| `test_config.py` | `KROKI_MCP_KROKI_URL` unset → `kroki_url == "https://kroki.io/"`, `using_public_instance == True` |
| `test_server_deps.py` | Health probe succeeds → `available` is filtered frozenset |
| `test_server_deps.py` | Health probe fails → `available` == full `DIAGRAM_TYPES` keyset |
| `test_tools.py` | `list_diagram_types` respects `available` set |
| `test_tools.py` | `render_diagram` with type not in `available` → validation error |
| `test_tools.py` | `render_diagram` with type in `available` → renders normally |

## Out of Scope

- Re-probing health on every request (startup probe is sufficient).
- Periodic re-probing during server lifetime.
- Adding `diagramsnet` to `DIAGRAM_TYPES` (tracked in issue #4).
