# Health-Based Availability Filtering & Public Default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `KROKI_MCP_KROKI_URL` optional (defaulting to public `https://kroki.io`), probe `GET /health` at startup to discover which diagram types are available on the instance, and filter both tools to only offer those types.

**Architecture:** `config.py` defaults the URL and adds a `using_public_instance` flag; `_server_deps.py` adds a `_probe_available_types()` coroutine called in the lifespan that stores the result in lifespan context, plus a `get_available_types()` DI helper; both tools in `_server_tools.py` depend on `get_available_types()` and filter against the returned frozenset.

**Tech Stack:** Python 3.11+, httpx, FastMCP 3.x (`Depends`, `CurrentContext`), pytest + respx

---

## File Map

| File | Change |
|------|--------|
| `src/kroki_mcp/config.py` | Make `KROKI_MCP_KROKI_URL` optional; add `using_public_instance: bool` to `ServerConfig` |
| `src/kroki_mcp/_server_deps.py` | Add `_probe_available_types()`, update lifespan to call it, add `get_available_types()` DI helper |
| `src/kroki_mcp/_server_tools.py` | Add `available` param via `Depends(get_available_types)` to both tools; filter accordingly |
| `tests/test_config.py` | Update two tests that expected raises; add tests for public-default behaviour |
| `tests/test_server_deps.py` | Add tests for `_probe_available_types` success/failure and lifespan context |
| `tests/test_tools.py` | Update `mock_kroki` fixture to mock health; add filtering tests |
| `README.md` | Mark `KROKI_MCP_KROKI_URL` as optional with default `https://kroki.io` |

---

### Task 1: Config — optional URL and `using_public_instance` flag

**Files:**
- Modify: `src/kroki_mcp/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Replace the two `raises` tests and add two new ones. The final `TestKrokiUrl` class in `tests/test_config.py`:

```python
class TestKrokiUrl:
    def test_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://localhost:8000")
        config = load_config()
        assert config.kroki_url == "http://localhost:8000/"

    def test_url_normalises_trailing_slash(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://localhost:8000/")
        config = load_config()
        assert config.kroki_url == "http://localhost:8000/"

    def test_url_missing_uses_public_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("KROKI_MCP_KROKI_URL", raising=False)
        config = load_config()
        assert config.kroki_url == "https://kroki.io/"

    def test_url_empty_uses_public_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "  ")
        config = load_config()
        assert config.kroki_url == "https://kroki.io/"

    def test_using_public_instance_true_when_no_url(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("KROKI_MCP_KROKI_URL", raising=False)
        config = load_config()
        assert config.using_public_instance is True

    def test_using_public_instance_false_when_url_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://localhost:8000")
        config = load_config()
        assert config.using_public_instance is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /mnt/code/kroki-mcp
uv run pytest tests/test_config.py -v
```

Expected: `test_url_missing_uses_public_default`, `test_url_empty_uses_public_default`, `test_using_public_instance_true_when_no_url`, `test_using_public_instance_false_when_url_set` all FAIL.

- [ ] **Step 3: Implement config changes**

In `src/kroki_mcp/config.py`, make these exact changes:

1. Add the public URL constant after the `_ENV_PREFIX` line and before `get_log_level`:

```python
_PUBLIC_KROKI_URL = "https://kroki.io/"
```

2. Add `using_public_instance` to `ServerConfig`:

```python
@dataclass
class ServerConfig:
    """Server configuration loaded from environment variables.

    Attributes:
        read_only: When ``True`` (default), write-tagged tools are hidden via
            ``mcp.disable(tags={"write"})``.
        kroki_url: Base URL of the Kroki instance, always with a trailing slash
            so httpx resolves subpath-relative requests correctly.
        using_public_instance: ``True`` when ``KROKI_MCP_KROKI_URL`` was not
            set and the server is using the public ``https://kroki.io`` fallback.
    """

    read_only: bool = True
    kroki_url: str = ""
    using_public_instance: bool = False
```

3. Replace the `load_config` body (the URL section only — keep the `read_only` part unchanged):

```python
def load_config() -> ServerConfig:
    """Load configuration from environment variables.

    Reads:

    - ``KROKI_MCP_READ_ONLY``: disable write tools; default ``true``.
    - ``KROKI_MCP_KROKI_URL``: base URL of the Kroki instance. When unset or
      empty, defaults to the public ``https://kroki.io`` instance and sets
      ``using_public_instance=True``.

    Returns:
        A populated :class:`ServerConfig` instance.
    """
    raw_read_only = _env("READ_ONLY")
    read_only = _parse_bool(raw_read_only) if raw_read_only is not None else True
    logger.debug("load_config: read_only=%s (raw=%r)", read_only, raw_read_only)

    raw_kroki_url = (_env("KROKI_URL") or "").strip()
    using_public = not raw_kroki_url
    if using_public:
        kroki_url = _PUBLIC_KROKI_URL
    else:
        kroki_url = raw_kroki_url.rstrip("/") + "/"

    return ServerConfig(
        read_only=read_only,
        kroki_url=kroki_url,
        using_public_instance=using_public,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/kroki_mcp/config.py tests/test_config.py
git commit -m "feat: make KROKI_MCP_KROKI_URL optional, default to public https://kroki.io"
```

---

### Task 2: Health probe and `get_available_types` DI helper

**Files:**
- Modify: `src/kroki_mcp/_server_deps.py`
- Modify: `tests/test_server_deps.py`

- [ ] **Step 1: Write failing tests**

Replace the entire `tests/test_server_deps.py` with:

```python
"""Tests for service lifespan and dependency injection."""

from __future__ import annotations

import httpx
import pytest
import respx

from kroki_mcp._diagram_types import DIAGRAM_TYPES
from kroki_mcp.config import ServerConfig


class TestServiceLifespan:
    async def test_lifespan_creates_httpx_client(self) -> None:
        """The lifespan should yield an httpx.AsyncClient as the service."""
        from kroki_mcp.mcp_server import create_server

        server = create_server()
        async with server._lifespan_manager():
            assert server._lifespan_result is not None
            assert isinstance(server._lifespan_result.get("service"), httpx.AsyncClient)

    async def test_service_is_httpx_client(self) -> None:
        """get_service() should return an httpx.AsyncClient."""
        from kroki_mcp._server_deps import make_service_lifespan

        config = ServerConfig(kroki_url="http://kroki.test:8000/")
        lifespan_fn = make_service_lifespan(config)

        from fastmcp import FastMCP

        mcp = FastMCP("test")
        mcp._lifespan = lifespan_fn

        async with mcp._lifespan_manager():
            assert mcp._lifespan_result is not None
            assert isinstance(mcp._lifespan_result.get("service"), httpx.AsyncClient)

    async def test_lifespan_context_contains_available(self) -> None:
        """The lifespan context should expose an 'available' frozenset."""
        from kroki_mcp._server_deps import make_service_lifespan

        health_body = {
            "status": "pass",
            "version": {"graphviz": "9.0.0", "mermaid": "11.0.0", "plantuml": "1.2026.1"},
        }
        config = ServerConfig(kroki_url="http://kroki.test:8000/")
        lifespan_fn = make_service_lifespan(config)

        from fastmcp import FastMCP

        mcp = FastMCP("test")
        mcp._lifespan = lifespan_fn

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            async with mcp._lifespan_manager():
                available = mcp._lifespan_result.get("available")
                assert isinstance(available, frozenset)
                assert "graphviz" in available
                assert "mermaid" in available
                assert "plantuml" in available


class TestProbeAvailableTypes:
    async def test_success_returns_filtered_frozenset(self) -> None:
        """Health probe success → frozenset of DIAGRAM_TYPES keys present in version."""
        from kroki_mcp._server_deps import _probe_available_types

        health_body = {
            "status": "pass",
            "version": {
                "graphviz": "9.0.0",
                "mermaid": "11.0.0",
                "plantuml": "1.2026.1",
                "dot": "9.0.0",      # graphviz alias — should be ignored
                "kroki": {"number": "0.30.1"},  # server itself — should be ignored
                "diagramsnet": "21.0",  # not in registry — should be ignored
            },
        }
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert isinstance(result, frozenset)
        assert "graphviz" in result
        assert "mermaid" in result
        assert "plantuml" in result
        assert "dot" not in result
        assert "kroki" not in result
        assert "diagramsnet" not in result

    async def test_connection_failure_returns_full_registry(self) -> None:
        """Health probe connection error → full DIAGRAM_TYPES keyset returned."""
        from kroki_mcp._server_deps import _probe_available_types

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(side_effect=httpx.ConnectError("refused"))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert result == frozenset(DIAGRAM_TYPES)

    async def test_non_200_response_returns_full_registry(self) -> None:
        """Health probe non-200 → full DIAGRAM_TYPES keyset returned."""
        from kroki_mcp._server_deps import _probe_available_types

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(503, text="unavailable"))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert result == frozenset(DIAGRAM_TYPES)

    async def test_malformed_json_returns_full_registry(self) -> None:
        """Health probe malformed JSON → full DIAGRAM_TYPES keyset returned."""
        from kroki_mcp._server_deps import _probe_available_types

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(
                return_value=httpx.Response(200, text="not-json")
            )
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert result == frozenset(DIAGRAM_TYPES)

    async def test_only_known_types_returned(self) -> None:
        """Probe only returns keys that exist in DIAGRAM_TYPES."""
        from kroki_mcp._server_deps import _probe_available_types

        # Return a superset of DIAGRAM_TYPES including unknown keys
        version_keys = {k: "1.0" for k in DIAGRAM_TYPES}
        version_keys["unknown_future_type"] = "2.0"
        health_body = {"status": "pass", "version": version_keys}

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert "unknown_future_type" not in result
        assert result.issubset(frozenset(DIAGRAM_TYPES))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_server_deps.py -v
```

Expected: `TestProbeAvailableTypes` tests all FAIL with `ImportError` or `AttributeError` (function doesn't exist yet). `TestServiceLifespan::test_lifespan_context_contains_available` also FAIL.

- [ ] **Step 3: Implement `_probe_available_types`, `get_available_types`, and update lifespan**

Replace the entire `src/kroki_mcp/_server_deps.py` with:

```python
"""Shared dependency injection and lifespan for the MCP server.

Provides :func:`get_service`, :func:`get_available_types`, and
:func:`make_service_lifespan` which are imported by the tool, resource, and
prompt registration modules.

The service object is an :class:`httpx.AsyncClient` pointed at the Kroki
instance.  At startup the lifespan probes ``GET /health`` to discover which
diagram types are actually running, storing the result as
``available: frozenset[str]`` in the lifespan context.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.server.lifespan import lifespan

from ._diagram_types import DIAGRAM_TYPES

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from kroki_mcp.config import ServerConfig

logger = logging.getLogger(__name__)


async def _probe_available_types(client: httpx.AsyncClient) -> frozenset[str]:
    """Call ``GET /health`` and return the set of available diagram type keys.

    Intersects the ``version`` keys from the health response with
    :data:`~kroki_mcp._diagram_types.DIAGRAM_TYPES`.  Keys ``dot`` (graphviz
    alias), ``kroki`` (the server itself), and any key not in ``DIAGRAM_TYPES``
    are silently ignored.

    Args:
        client: An :class:`httpx.AsyncClient` with ``base_url`` pointing at the
            Kroki instance.

    Returns:
        A :class:`frozenset` of ``DIAGRAM_TYPES`` keys available on this
        instance.  On any error (connection failure, non-200 response,
        malformed JSON) returns ``frozenset(DIAGRAM_TYPES)`` — the full static
        registry — so the server degrades gracefully.
    """
    try:
        response = await client.get("health")
        response.raise_for_status()
        data = response.json()
        version_keys = set(data.get("version", {}).keys())
        available = frozenset(k for k in version_keys if k in DIAGRAM_TYPES)
        logger.info(
            "Health probe: %d/%d diagram types available on this instance",
            len(available),
            len(DIAGRAM_TYPES),
        )
        return available
    except Exception:
        logger.warning(
            "Could not reach GET /health at %s — falling back to static type registry. "
            "All %d types will be offered but some may not be available.",
            str(client.base_url),
            len(DIAGRAM_TYPES),
        )
        return frozenset(DIAGRAM_TYPES)


def make_service_lifespan(config: ServerConfig) -> Any:
    """Create a lifespan function that closes over a pre-loaded config.

    Args:
        config: A fully-loaded :class:`~kroki_mcp.config.ServerConfig`
            instance produced by a single :func:`load_config` call in
            :func:`~kroki_mcp.mcp_server.create_server`.

    Returns:
        A FastMCP lifespan coroutine that initialises the httpx client,
        probes ``GET /health``, and yields
        ``{"service": client, "config": config, "available": frozenset[str]}``
        to the lifespan context.
    """

    @lifespan
    async def _service_lifespan(
        server: FastMCP,  # noqa: ARG001
    ) -> AsyncIterator[dict[str, Any]]:
        """Initialise the httpx client at startup, close on shutdown."""
        if config.using_public_instance:
            logger.warning(
                "KROKI_MCP_KROKI_URL not set — using public https://kroki.io. "
                "Not suitable for production; diagram source is sent to a "
                "third-party server."
            )
        logger.info(
            "Kroki client starting (base_url=%s, read_only=%s)",
            config.kroki_url,
            config.read_only,
        )

        client = httpx.AsyncClient(
            base_url=config.kroki_url,
            timeout=30.0,
        )

        try:
            available = await _probe_available_types(client)
            yield {"service": client, "config": config, "available": available}
        finally:
            await client.aclose()
            logger.info("Kroki client shut down")

    return _service_lifespan


def get_service(ctx: Context = CurrentContext()) -> httpx.AsyncClient:
    """Resolve the httpx client from lifespan context.

    Used as a ``Depends()`` default in tool/resource/prompt signatures.

    Raises:
        RuntimeError: If the server lifespan has not run.
    """
    service: Any = ctx.lifespan_context.get("service")
    if service is None:
        msg = "Service not initialised — server lifespan has not run"
        raise RuntimeError(msg)
    return service  # type: ignore[no-any-return]


def get_available_types(ctx: Context = CurrentContext()) -> frozenset[str]:
    """Resolve the available diagram types frozenset from lifespan context.

    Returns the set of diagram type keys confirmed available by the health
    probe at startup.  Falls back to the full :data:`DIAGRAM_TYPES` keyset
    if the lifespan context does not contain the key (e.g. in unit tests that
    bypass the lifespan).

    Used as a ``Depends()`` default in tool signatures.
    """
    available = ctx.lifespan_context.get("available")
    if available is None:
        return frozenset(DIAGRAM_TYPES)
    return available  # type: ignore[return-value]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_server_deps.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Run full test suite to verify no regressions**

```bash
uv run pytest -v
```

Expected: all existing tests still PASS (health probe failures in non-mocked tests fall back gracefully to full registry).

- [ ] **Step 6: Commit**

```bash
git add src/kroki_mcp/_server_deps.py tests/test_server_deps.py
git commit -m "feat: probe GET /health at startup to discover available diagram types"
```

---

### Task 3: Update tools to filter by available types

**Files:**
- Modify: `src/kroki_mcp/_server_tools.py`
- Modify: `tests/test_tools.py`

- [ ] **Step 1: Write failing tests**

Add these tests to `tests/test_tools.py`. First, update the imports at the top to include `DIAGRAM_TYPES`:

```python
from kroki_mcp._diagram_types import DIAGRAM_TYPES
```

Then update the `mock_kroki` fixture to also mock `GET /health` so the lifespan probe succeeds in tool tests (returning all types — same behaviour as before):

```python
@pytest.fixture()
def mock_kroki() -> respx.MockRouter:
    """Create a respx mock router for Kroki API calls."""
    health_body = {
        "status": "pass",
        "version": {k: "1.0.0" for k in DIAGRAM_TYPES},
    }
    with respx.mock(base_url="http://kroki.test:8000") as router:
        router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
        yield router
```

Then add a new test class at the end of the file:

```python
class TestAvailableFiltering:
    async def test_list_diagram_types_respects_available(self) -> None:
        """list_diagram_types only returns types present in the health response."""
        health_body = {
            "status": "pass",
            "version": {"graphviz": "9.0.0", "mermaid": "11.0.0"},
        }
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            server = create_server()
            async with server._lifespan_manager():
                result = await server.call_tool("list_diagram_types", {})
                data = json.loads(result.content[0].text)
                types = {entry["type"] for entry in data}
                assert types == {"graphviz", "mermaid"}

    async def test_render_diagram_type_not_in_available(self) -> None:
        """render_diagram rejects a type absent from the health-derived available set."""
        health_body = {
            "status": "pass",
            "version": {"graphviz": "9.0.0"},
        }
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            server = create_server()
            async with server._lifespan_manager():
                result = await server.call_tool(
                    "render_diagram",
                    {"diagram_type": "mermaid", "source": "graph TD; A-->B"},
                )
                assert "Unknown diagram type" in result.content[0].text

    async def test_render_diagram_type_in_available(
        self, mock_kroki: respx.MockRouter
    ) -> None:
        """render_diagram succeeds for a type present in the available set."""
        mock_kroki.post("/graphviz/svg").mock(
            return_value=httpx.Response(200, text="<svg>ok</svg>")
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {"diagram_type": "graphviz", "source": "digraph { a -> b }"},
            )
            assert result.content[0].text == "<svg>ok</svg>"
```

- [ ] **Step 2: Run tests to verify new tests fail**

```bash
uv run pytest tests/test_tools.py::TestAvailableFiltering -v
```

Expected: all 3 FAIL (tools don't filter yet).

- [ ] **Step 3: Update `_server_tools.py` to use `get_available_types`**

Replace `src/kroki_mcp/_server_tools.py` with:

```python
"""MCP tool registrations — Kroki diagram rendering.

Exposes :func:`list_diagram_types` and :func:`render_diagram` tools.
"""

from __future__ import annotations

import base64
import json
import logging

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.utilities.types import Image

from ._diagram_types import DIAGRAM_TYPES
from ._server_deps import get_available_types, get_service

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, *, transport: str = "stdio") -> None:
    """Register all MCP tools on *mcp*.

    Args:
        mcp: The :class:`~fastmcp.FastMCP` instance to register tools on.
        transport: Active transport (``"stdio"``, ``"sse"``, or ``"http"``).
    """

    @mcp.tool()
    def list_diagram_types(
        available: frozenset[str] = Depends(get_available_types),
    ) -> str:
        """List all supported diagram types and their output formats.

        Returns:
            JSON array of objects with ``type`` and ``formats`` keys, filtered
            to only include types available on this Kroki instance.
        """
        entries = [
            {"type": dtype, "formats": formats}
            for dtype, formats in sorted(DIAGRAM_TYPES.items())
            if dtype in available
        ]
        return json.dumps(entries)

    @mcp.tool()
    async def render_diagram(
        diagram_type: str,
        source: str,
        output_format: str = "svg",
        as_base64: bool = False,
        client: httpx.AsyncClient = Depends(get_service),
        available: frozenset[str] = Depends(get_available_types),
    ) -> str | Image:
        """Render a diagram using Kroki.

        Args:
            diagram_type: Diagram language (e.g. ``"plantuml"``, ``"mermaid"``,
                ``"graphviz"``). Use ``list_diagram_types`` to see all options.
            source: The diagram source code.
            output_format: Output format — ``"svg"`` (default) or ``"png"``.
            as_base64: When True and format is ``"png"``, return a base64
                string instead of an MCP Image.

        Returns:
            SVG string, MCP Image (PNG), or base64 string (PNG + as_base64).
        """
        diagram_type = diagram_type.lower().strip()

        if diagram_type not in available:
            return (
                f"Unknown diagram type '{diagram_type}'. "
                "Use list_diagram_types to see what is available on this instance."
            )

        supported = DIAGRAM_TYPES[diagram_type]
        if output_format not in supported:
            return (
                f"'{output_format}' is not supported for '{diagram_type}'. "
                f"Supported: {', '.join(supported)}"
            )

        try:
            response = await client.post(
                f"{diagram_type}/{output_format}",
                content=source,
                headers={"Content-Type": "text/plain"},
            )
        except httpx.TransportError as exc:
            base_url = str(client.base_url)
            if isinstance(exc, httpx.TimeoutException):
                return "Kroki did not respond within 30s"
            return f"Cannot reach Kroki at {base_url} — is it running?"

        if response.status_code == 400:
            return response.text
        if response.status_code >= 400:
            return f"Kroki returned an error: {response.status_code} {response.text}"

        if output_format == "svg":
            return response.text

        # PNG
        png_bytes = response.content
        if as_base64:
            return base64.b64encode(png_bytes).decode()
        return Image(data=png_bytes, format="png")
```

- [ ] **Step 4: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/kroki_mcp/_server_tools.py tests/test_tools.py
git commit -m "feat: filter diagram types by health-probed availability in both tools"
```

---

### Task 4: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the config table row for `KROKI_MCP_KROKI_URL`**

Find this line in `README.md`:
```
| `KROKI_MCP_KROKI_URL` | **Yes** | — | URL of your self-hosted Kroki instance (e.g. `http://localhost:8000`) |
```

Replace with:
```
| `KROKI_MCP_KROKI_URL` | No | `https://kroki.io` | URL of your Kroki instance. Defaults to the public instance — **not suitable for production** (diagram source is sent to a third-party server). |
```

- [ ] **Step 2: Run lint to verify no formatting issues**

```bash
uv run ruff check README.md 2>/dev/null || true
```

(Ruff doesn't lint markdown; this is a no-op. Just verifying the suite still passes.)

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: mark KROKI_MCP_KROKI_URL as optional with public instance default"
```

---

### Task 5: Lint, type-check, and final verification

- [ ] **Step 1: Run ruff**

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Fix any issues reported. Common fixes: missing blank lines, import order. Re-run until clean.

- [ ] **Step 2: Run mypy**

```bash
uv run mypy src/
```

Expected: no errors. If `get_available_types` reports a return-type issue, add `# type: ignore[return-value]` on the `return available` line (already in the plan above).

- [ ] **Step 3: Run full test suite one final time**

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 4: Final commit (if lint/type fixes were needed)**

```bash
git add -p
git commit -m "chore: fix lint/type issues after health-based availability implementation"
```

(Skip if no changes were needed.)
