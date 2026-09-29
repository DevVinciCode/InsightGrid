"""
PowerBIService — STAGE 5, SCAFFOLDED, NOT FAKED.

What Microsoft's Power BI REST API actually supports today:
  - Real, automatable: acquiring an Azure AD app-only token, listing
    workspaces/reports/datasets, generating an embed token for a report you
    already published, and (if the dataset is Push/Streaming) pushing new
    rows into it.
  - NOT automatable via API: creating a brand-new report's visual layout, or
    changing which chart types/fields a visual uses. Report *design* is done
    in Power BI Desktop or the Power BI service UI — there is no supported
    API to programmatically add a bar chart to a report page.

So this system's honest integration boundary is:
  MVP mode  (default): native React/Recharts rendering of `visualization/
             planner.py`'s spec — fully dynamic, fully automated.
  PowerBI mode (ENABLE_POWERBI=true, requires real Azure AD app registration
             + a pre-built report in your workspace): this service fetches an
             embed token and the frontend embeds that existing report. Any
             *filtering* passed through is done via Power BI's supported
             "basic filter" embed parameters — it cannot rewrite the report's
             visuals themselves.

Do not extend this file to pretend dynamic visual creation is happening.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config.settings import Settings

AAD_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
POWERBI_API = "https://api.powerbi.com/v1.0/myorg"


@dataclass
class EmbedConfig:
    report_id: str
    embed_url: str
    access_token: str


class PowerBIService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        s = self._settings
        return bool(s.POWERBI_TENANT_ID and s.POWERBI_CLIENT_ID and s.POWERBI_CLIENT_SECRET
                    and s.POWERBI_WORKSPACE_ID and s.POWERBI_REPORT_ID)

    def _get_aad_token(self) -> str:
        s = self._settings
        url = AAD_TOKEN_URL.format(tenant=s.POWERBI_TENANT_ID)
        resp = httpx.post(url, data={
            "grant_type": "client_credentials",
            "client_id": s.POWERBI_CLIENT_ID,
            "client_secret": s.POWERBI_CLIENT_SECRET,
            "scope": "https://analysis.windows.net/powerbi/api/.default",
        }, timeout=15)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def get_embed_config(self) -> EmbedConfig:
        """
        Real, working call — requires the Azure AD app + workspace/report IDs to
        actually exist (see docs/powerbi_setup.md). Raises if not configured.
        """
        if not self.is_configured():
            raise RuntimeError(
                "Power BI is not configured. Set POWERBI_TENANT_ID, POWERBI_CLIENT_ID, "
                "POWERBI_CLIENT_SECRET, POWERBI_WORKSPACE_ID, POWERBI_REPORT_ID in .env, "
                "and see docs/powerbi_setup.md for the Azure AD app registration steps."
            )
        s = self._settings
        aad_token = self._get_aad_token()

        report_resp = httpx.get(
            f"{POWERBI_API}/groups/{s.POWERBI_WORKSPACE_ID}/reports/{s.POWERBI_REPORT_ID}",
            headers={"Authorization": f"Bearer {aad_token}"}, timeout=15,
        )
        report_resp.raise_for_status()
        report = report_resp.json()

        embed_resp = httpx.post(
            f"{POWERBI_API}/groups/{s.POWERBI_WORKSPACE_ID}/reports/{s.POWERBI_REPORT_ID}/GenerateToken",
            headers={"Authorization": f"Bearer {aad_token}"},
            json={"accessLevel": "View"}, timeout=15,
        )
        embed_resp.raise_for_status()
        embed_token = embed_resp.json()["token"]

        return EmbedConfig(
            report_id=s.POWERBI_REPORT_ID,
            embed_url=report["embedUrl"],
            access_token=embed_token,
        )
