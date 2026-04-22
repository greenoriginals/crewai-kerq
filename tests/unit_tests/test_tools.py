"""Unit tests for KerqTrustTool."""

from unittest.mock import MagicMock, patch

import pytest

from crewai_kerq.tools import KerqTrustTool


@pytest.fixture
def tool():
    return KerqTrustTool(api_key="test-key")


class TestKerqTrustTool:
    """Tests for the KerqTrustTool."""

    @patch("crewai_kerq.tools.KerqClient")
    def test_run_returns_score(self, mock_client_cls, tool):
        mock_client = MagicMock()
        mock_client.get_trust_score.return_value = {
            "trust_score": 85,
            "tier": "high",
            "score_breakdown": {},
        }
        mock_client_cls.return_value = mock_client

        result = tool._run(tool_id="test-tool")

        assert result["trust_score"] == 85
        assert result["tier"] == "high"
        mock_client.get_trust_score.assert_called_once_with("test-tool")
        mock_client.close.assert_called_once()

    @patch("crewai_kerq.tools.KerqClient")
    def test_run_adds_warning_below_min_score(self, mock_client_cls):
        tool = KerqTrustTool(api_key="test-key", min_score=70.0)
        mock_client = MagicMock()
        mock_client.get_trust_score.return_value = {
            "trust_score": 45,
            "tier": "low",
            "score_breakdown": {},
        }
        mock_client_cls.return_value = mock_client

        result = tool._run(tool_id="risky-tool")

        assert "warning" in result
        assert "below the minimum threshold" in result["warning"]

    @patch("crewai_kerq.tools.KerqClient")
    def test_run_no_warning_above_min_score(self, mock_client_cls):
        tool = KerqTrustTool(api_key="test-key", min_score=70.0)
        mock_client = MagicMock()
        mock_client.get_trust_score.return_value = {
            "trust_score": 85,
            "tier": "high",
            "score_breakdown": {},
        }
        mock_client_cls.return_value = mock_client

        result = tool._run(tool_id="good-tool")

        assert "warning" not in result

    @patch("crewai_kerq.tools.KerqClient")
    def test_client_closed_on_exception(self, mock_client_cls, tool):
        mock_client = MagicMock()
        mock_client.get_trust_score.side_effect = RuntimeError("boom")
        mock_client_cls.return_value = mock_client

        with pytest.raises(RuntimeError):
            tool._run(tool_id="bad-tool")

        mock_client.close.assert_called_once()
