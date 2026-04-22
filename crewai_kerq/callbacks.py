"""
CrewAI callback handler for Kerq telemetry and trust gating.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from crewai_kerq.client import KerqClient

logger = logging.getLogger(__name__)


class KerqTelemetryHandler:
    """
    Callback handler that reports tool execution telemetry to Kerq.

    Usage:
        handler = KerqTelemetryHandler(api_key="kerq_...")
        # Wire into your CrewAI task callbacks
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://kerq.dev",
    ) -> None:
        self._api_key = api_key or os.environ.get("KERQ_API_KEY", "")
        self._client = KerqClient(api_key=self._api_key, base_url=base_url)
        self._start_times: Dict[str, float] = {}

    def on_tool_start(self, tool_name: str, tool_input: Any = None) -> None:
        """Record the start time for a tool invocation."""
        self._start_times[tool_name] = time.monotonic()

    def on_tool_end(self, tool_name: str, tool_output: Any = None) -> None:
        """Report successful tool execution to Kerq telemetry."""
        latency = self._elapsed_ms(tool_name)
        self._client.report_telemetry(
            tool_id=tool_name,
            status_code=200,
            latency_ms=latency,
        )

    def on_tool_error(self, tool_name: str, error: Any = None) -> None:
        """Report failed tool execution to Kerq telemetry."""
        latency = self._elapsed_ms(tool_name)
        self._client.report_telemetry(
            tool_id=tool_name,
            status_code=500,
            latency_ms=latency,
        )

    def _elapsed_ms(self, tool_name: str) -> float:
        start = self._start_times.pop(tool_name, None)
        if start is None:
            return 0.0
        return (time.monotonic() - start) * 1000

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


class KerqGuard:
    """
    Pre-execution gate that blocks tools below a trust threshold.

    Usage:
        guard = KerqGuard(api_key="kerq_...", min_score=60)
        if guard.allow("some-tool"):
            # proceed
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://kerq.dev",
        min_score: float = 50.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("KERQ_API_KEY", "")
        self._client = KerqClient(api_key=self._api_key, base_url=base_url)
        self._min_score = min_score

    def allow(self, tool_id: str) -> bool:
        """
        Check whether a tool meets the minimum trust score.

        Args:
            tool_id: Tool slug or numeric ID.

        Returns:
            True if the tool's score >= min_score, False otherwise.
            Returns True on network errors (fail-open).
        """
        try:
            result = self._client.get_trust_score(tool_id)
            score = result.get("trust_score", 0)
            allowed = score >= self._min_score
            if not allowed:
                logger.warning(
                    "KerqGuard blocked %s (score=%s, min=%s)",
                    tool_id,
                    score,
                    self._min_score,
                )
            return allowed
        except Exception as exc:  # noqa: BLE001
            logger.warning("KerqGuard lookup failed for %s (fail-open): %s", tool_id, exc)
            return True

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
