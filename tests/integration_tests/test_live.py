"""
Integration tests that hit the real Kerq API.

Skipped unless KERQ_API_KEY is set in the environment.
Run with: pytest tests/integration_tests -v
"""

import os

import pytest

from crewai_kerq.client import KerqClient

KERQ_API_KEY = os.environ.get("KERQ_API_KEY", "")
SKIP_REASON = "KERQ_API_KEY not set — skipping live integration tests"


@pytest.mark.skipif(not KERQ_API_KEY, reason=SKIP_REASON)
class TestLiveKerqAPI:
    """Integration tests against the real Kerq API."""

    def test_get_trust_score_returns_valid_response(self):
        client = KerqClient(api_key=KERQ_API_KEY)
        try:
            result = client.get_trust_score("openai")
            assert "trust_score" in result
            assert isinstance(result["trust_score"], (int, float))
        finally:
            client.close()

    def test_report_telemetry_does_not_raise(self):
        client = KerqClient(api_key=KERQ_API_KEY)
        try:
            # Should never raise — fire-and-forget
            client.report_telemetry(
                tool_id="integration-test",
                status_code=200,
                latency_ms=42.0,
            )
        finally:
            client.close()
