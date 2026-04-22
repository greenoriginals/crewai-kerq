"""
CrewAI-compatible tools for Kerq trust verification.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_kerq.client import KerqClient


class KerqTrustToolInput(BaseModel):
    """Input schema for KerqTrustTool."""

    tool_id: str = Field(
        ...,
        description="The tool slug or numeric ID to look up in Kerq's trust index.",
    )


class KerqTrustTool(BaseTool):
    """
    Look up the Kerq trust score for an AI tool.

    Returns the composite score (0-100), tier label,
    and the seven-dimension breakdown so an agent can
    decide whether to connect.
    """

    name: str = "kerq_trust_score"
    description: str = (
        "Retrieve the Kerq trust score for an AI tool. "
        "Returns composite score, tier, and seven-dimension breakdown."
    )
    args_schema: Type[BaseModel] = KerqTrustToolInput

    api_key: str = Field(default_factory=lambda: os.environ.get("KERQ_API_KEY", ""))
    base_url: str = Field(default="https://kerq.dev")
    min_score: Optional[float] = Field(
        default=None,
        description="If set, the tool returns a warning when score < min_score.",
    )

    def _run(self, tool_id: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Synchronous trust-score lookup.

        Args:
            tool_id: Tool slug or numeric ID.

        Returns:
            Dict with trust_score, tier, score_breakdown, and optional warning.
        """
        client = KerqClient(api_key=self.api_key, base_url=self.base_url)
        try:
            result = client.get_trust_score(tool_id)
        finally:
            client.close()

        if self.min_score is not None and result.get("trust_score", 0) < self.min_score:
            result["warning"] = (
                f"Score {result.get('trust_score')} is below the minimum threshold "
                f"of {self.min_score}. Proceed with caution."
            )

        return result
