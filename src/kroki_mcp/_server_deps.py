"""Shared dependency injection and lifespan for the MCP server.

Provides :func:`get_service` and :func:`make_service_lifespan` which are
imported by the tool, resource, and prompt registration modules.

The service object is an :class:`httpx.AsyncClient` pointed at the
self-hosted Kroki instance.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.server.lifespan import lifespan

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from kroki_mcp.config import ServerConfig

logger = logging.getLogger(__name__)


def make_service_lifespan(config: ServerConfig) -> Any:
    """Create a lifespan function that closes over a pre-loaded config.

    Args:
        config: A fully-loaded :class:`~kroki_mcp.config.ServerConfig`
            instance produced by a single :func:`load_config` call in
            :func:`~kroki_mcp.mcp_server.create_server`.

    Returns:
        A FastMCP lifespan coroutine that initialises the httpx client and
        yields ``{"service": client, "config": config}`` to the lifespan
        context.
    """

    @lifespan
    async def _service_lifespan(
        server: FastMCP,  # noqa: ARG001
    ) -> AsyncIterator[dict[str, Any]]:
        """Initialise the httpx client at startup, close on shutdown."""
        logger.info(
            "Kroki client starting (base_url=%s, read_only=%s)",
            config.kroki_base_url,
            config.read_only,
        )

        client = httpx.AsyncClient(
            base_url=config.kroki_base_url,
            timeout=30.0,
        )

        try:
            yield {"service": client, "config": config}
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
    return service
