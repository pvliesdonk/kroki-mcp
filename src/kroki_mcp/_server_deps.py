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

        async with httpx.AsyncClient(
            base_url=config.kroki_url,
            timeout=30.0,
        ) as probe_client:
            available = await _probe_available_types(probe_client)

        client = httpx.AsyncClient(
            base_url=config.kroki_url,
            timeout=30.0,
        )

        try:
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
