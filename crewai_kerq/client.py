"""
Shared HTTP client for Kerq API calls.
Sync and async variants using httpx.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

_KERQ_BASE_URL = "https://kerq.dev"
_TELEMETRY_URL = "https://kerq-mcp.polsia.app/v1/report"
_TIMEOUT = 2.0  # seconds — hardcoded, not configurable


class KerqClient:
    """Synchronous HTTP client for Kerq API."""

    def __init__(self, api_key: str, base_url: str = _KERQ_BASE_URL) -> None:
        """
        Initialize the Kerq sync client.

        Args:
            api_key: Your Kerq API key.
            base_url: Base URL for the Kerq API (default: https://kerq.dev).
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(timeout=_TIMEOUT)

    def get_trust_score(self, tool_id: str) -> Dict[str, Any]:
        """
        Retrieve the trust score for a tool.

        Args:
            tool_id: Tool slug or numeric ID.

        Returns:
            Dict with trust_score, tier, score_breakdown.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
            httpx.RequestError: On network errors.
        """
        url = f"{self._base_url}/api/tools/{tool_id}/score"
        response = self._client.get(url, headers=self._headers)
        response.raise_for_status()
        return response.json()

    def report_telemetry(
        self,
        tool_id: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        """
        Fire-and-forget telemetry report. Never raises.

        Args:
            tool_id: Tool slug or numeric ID.
            status_code: HTTP-style status code (200 = success, 500 = error).
            latency_ms: Tool execution latency in milliseconds.
        """
        try:
            payload = {
                "tool_id": tool_id,
                "status_code": status_code,
                "latency_ms": latency_ms,
            }
            self._client.post(_TELEMETRY_URL, json=payload, headers=self._headers)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Kerq telemetry error (ignored): %s", exc)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "KerqClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncKerqClient:
    """Asynchronous HTTP client for Kerq API."""

    def __init__(self, api_key: str, base_url: str = _KERQ_BASE_URL) -> None:
        """
        Initialize the Kerq async client.

        Args:
            api_key: Your Kerq API key.
            base_url: Base URL for the Kerq API (default: https://kerq.dev).
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def get_trust_score(self, tool_id: str) -> Dict[str, Any]:
        """
        Retrieve the trust score for a tool (async).

        Args:
            tool_id: Tool slug or numeric ID.

        Returns:
            Dict with trust_score, tier, score_breakdown.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
            httpx.RequestError: On network errors.
        """
        url = f"{self._base_url}/api/tools/{tool_id}/score"
        response = await self._client.get(url, headers=self._headers)
        response.raise_for_status()
        return response.json()

    async def report_telemetry(
        self,
        tool_id: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        """
        Fire-and-forget telemetry report (async). Never raises.

        Args:
            tool_id: Tool slug or numeric ID.
            status_code: HTTP-style status code (200 = success, 500 = error).
            latency_ms: Tool execution latency in milliseconds.
        """
        try:
            payload = {
                "tool_id": tool_id,
                "status_code": status_code,
                "latency_ms": latency_ms,
            }
            await self._client.post(_TELEMETRY_URL, json=payload, headers=self._headers)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Kerq telemetry error (ignored): %s", exc)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncKerqClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
