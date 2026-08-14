"""
Notifications Service — Webhook integration for remediation actions.

Dispatches structured Slack / Discord notifications when a remediation
action is executed or dry-run simulated.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def send_remediation_notification(
    webhook_url: str,
    action_result: dict[str, Any],
    reco_detail: str | None = None,
    savings: float = 0.0,
) -> bool:
    """
    Send an HTTP POST webhook notification for a remediation action.

    Parameters
    ----------
    webhook_url : str
        Target Slack / Discord webhook URL.
    action_result : dict
        Result dict returned by ``execute_remediation_action``.
    reco_detail : str | None
        Recommendation details explanation.
    savings : float
        Estimated monthly savings achieved.

    Returns
    -------
    bool
        True if webhook returned 2xx status code.
    """
    if not webhook_url:
        return False

    resource_id = action_result.get("resource_id", "Unknown")
    action_name = action_result.get("action", "remediation").replace("_", " ").title()
    dry_run = action_result.get("dry_run", False)
    status_text = "Simulated (Dry Run)" if dry_run else "Executed Successfully"

    # Construct rich Slack Block Kit payload
    payload = {
        "text": f"FinOps Remediation Alert: {action_name} on {resource_id}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚡ FinOps Remediation Action {status_text}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Resource ID:*\n`{resource_id}`"},
                    {"type": "mrkdwn", "text": f"*Action:*\n{action_name}"},
                    {"type": "mrkdwn", "text": f"*Estimated Savings:*\n*${savings:,.2f}/mo*"},
                    {"type": "mrkdwn", "text": f"*Execution Mode:*\n{'🧪 Dry Run (Test)' if dry_run else '🚀 Production Apply'}"},
                ],
            },
        ],
    }

    if reco_detail:
        payload["blocks"].append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Details:*\n_{reco_detail}_"},
        })

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(webhook_url, json=payload)
            if resp.status_code < 300:
                logger.info("Webhook notification sent successfully for %s", resource_id)
                return True
            else:
                logger.warning("Webhook returned status %d: %s", resp.status_code, resp.text)
                return False

    except Exception as exc:
        logger.error("Failed to post webhook notification to %s: %s", webhook_url, exc)
        return False
