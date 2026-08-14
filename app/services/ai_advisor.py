"""
AI FinOps Advisor Service — Gemini API Integration.

Takes raw financial cost JSON and savings recommendations data and invokes
Google Gemini API to generate human-readable executive FinOps insights.

Function:
- ``generate_cost_summary(tenant_data)``: Formulates prompt & queries Gemini.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_cost_summary(tenant_data: dict[str, Any]) -> dict[str, Any]:
    """
    Generate an AI executive summary of cost drivers and recommendations.
    """
    total_cost = tenant_data.get("total_cost", 0.0)
    currency = tenant_data.get("currency", "USD")
    service_breakdown = tenant_data.get("service_breakdown", [])
    recos = tenant_data.get("recommendations", [])

    top_services = sorted(service_breakdown, key=lambda x: x.get("amount", 0), reverse=True)[:3]
    top_recos = sorted(recos, key=lambda x: x.get("estimated_savings_monthly", 0), reverse=True)[:3]

    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

    if api_key:
        try:
            ai_text = _call_gemini_api(api_key, total_cost, currency, top_services, top_recos)
            return {
                "success": True,
                "ai_provider": "Google Gemini (Live API)",
                "summary": ai_text,
                "top_cost_drivers": top_services,
                "top_recommendations": top_recos,
            }
        except Exception as exc:
            logger.warning("Gemini API call failed (%s); serving structured fallback", exc)

    fallback_summary = _generate_heuristic_fallback(total_cost, currency, top_services, top_recos)
    return {
        "success": True,
        "ai_provider": "FinOps Rules Engine (Fallback)",
        "summary": fallback_summary,
        "top_cost_drivers": top_services,
        "top_recommendations": top_recos,
    }


def _call_gemini_api(
    api_key: str,
    total_cost: float,
    currency: str,
    top_services: list[dict],
    top_recos: list[dict],
) -> str:
    """Call Google Gemini API using google-genai SDK with model fallback."""

    prompt = f"""Act as a Senior FinOps Consultant. Given this AWS usage data, summarize the top 3 biggest cost drivers and explain in plain English why the top 3 recommendations will save money.

--- AWS EXPENDITURE DATA ---
Total Monthly Cost: ${total_cost:,.2f} {currency}

Top 3 Cost-Driving AWS Services:
{json.dumps(top_services, indent=2)}

Top 3 Cost-Saving Recommendations:
{json.dumps(top_recos, indent=2)}

--- RESPONSE INSTRUCTIONS ---
- Write a professional, concise executive summary (3-4 bullet points).
- Clearly explain the top 3 cost drivers and their impact on the bill.
- Explain in simple, plain English why implementing the recommendations will save money without risking workload stability.
- Use clean Markdown bullet points.
"""

    candidate_models = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash-latest"]

    # 1. Try google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    logger.info("Successfully generated AI summary using model %s", model_name)
                    return response.text.strip()
            except Exception as m_err:
                logger.debug("Model %s failed: %s", model_name, m_err)
                continue
    except Exception as err1:
        logger.debug("google-genai SDK init failed: %s", err1)

    raise RuntimeError("Could not generate content from candidate Gemini models")


def _generate_heuristic_fallback(
    total_cost: float,
    currency: str,
    top_services: list[dict],
    top_recos: list[dict],
) -> str:
    """Generate structured Markdown summary when API key is unconfigured or unavailable."""

    lines = [
        f"### 💡 FinOps Executive Summary (${total_cost:,.2f} {currency}/month)",
        "",
        "**Top Cost Drivers:**",
    ]

    if top_services:
        for idx, srv in enumerate(top_services, 1):
            name = srv.get("service_name", "AWS Service")
            amt = srv.get("amount", 0.0)
            pct = srv.get("percentage", 0.0)
            lines.append(f"{idx}. **{name}**: ${amt:,.2f}/mo ({pct}% of total AWS expenditure).")
    else:
        lines.append("- No cost driver metrics available.")

    lines.extend(["", "**Top Savings Opportunities:**"])

    if top_recos:
        for idx, r in enumerate(top_recos, 1):
            res_id = r.get("resource_id", "Resource")
            rtype = r.get("type", "Optimization").replace("_", " ").title()
            savings = r.get("estimated_savings_monthly", 0.0)
            detail = r.get("detail", "")
            lines.append(f"{idx}. **{res_id} ({rtype})**: Save ~**${savings:,.2f}/mo**. {detail}")
    else:
        lines.append("- No high-impact savings recommendations detected yet.")

    return "\n".join(lines)
