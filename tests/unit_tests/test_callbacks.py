"""Unit tests for KerqTelemetryHandler and KerqGuard."""

from unittest.mock import MagicMock, patch

import pytest

from crewai_kerq.callbacks import KerqGuard, KerqTelemetryHandler


class TestKerqTelemetryHandler:
    """Tests for the telemetry callback handler."""

    @patch("crewai_kerq.callbacks.KerqClient")
    def test_on_tool_end_reports_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        handler = KerqTelemetryHandler(api_key="test-key")
        handler.on_tool_start("my-tool")
        handler.on_tool_end("my-tool")

        mock_client.report_telemetry.assert_called_once()
        call_kwargs = mock_client.report_telemetry.call_args
        assert call_kwargs[1]["tool_id"] == "my-tool"
        assert call_kwargs[1]["status_code"] == 200

    @patch("crewai_kerq.callbacks.KerqClient")
    def test_on_tool_error_reports_failure(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        handler = KerqTelemetryHandler(api_key="test-key")
        handler.on_tool_start("my-tool")
        handler.on_tool_error("my-tool", error="something broke")

        call_kwargs = mock_client.report_telemetry.call_args
        assert call_kwargs[1]["status_code"] == 500


class TestKerqGuard:
    """Tests for the trust-gating guard."""

    @patch("crewai_kerq.callbacks.KerqClient")
    def test_allow_passes_above_threshold(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.get_trust_score.return_value = {"trust_score": 80}
        mock_client_cls.return_value = mock_client

        guard = KerqGuard(api_key="test-key", min_score=60)
        assert guard.allow("good-tool") is True

    @patch("crewai_kerq.callbacks.KerqClient")
    def test_allow_blocks_below_threshold(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.get_trust_score.return_value = {"trust_score": 30}
        mock_client_cls.return_value = mock_client

        guard = KerqGuard(api_key="test-key", min_score=60)
        assert guard.allow("bad-tool") is False

    @patch("crewai_kerq.callbacks.KerqClient")
    def test_allow_fail_open_on_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.get_trust_score.side_effect = RuntimeError("network down")
        mock_client_cls.return_value = mock_client

        guard = KerqGuard(api_key="test-key", min_score=60)
        assert guard.allow("unreachable-tool") is True
