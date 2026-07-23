"""
AI Analysis Engine — Insight step.

Calls the Anthropic API with the prompt built from engine output (trend +
indicators + confidence + entry/SL/TP) and returns a structured AIAnalysis.
This is the ONLY place in the codebase that talks to the AI model.
"""

import httpx
from typing import Union
from app.config import settings
from app.schemas.market import TradeSignal, IndexTrendSignal, AIAnalysis
from app.engines.ai.prompt import build_prompt
from app.engines.ai.formatter import parse_ai_response
from app.utils.logger import get_logger

logger = get_logger("ai_engine")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


async def generate_ai_analysis(result: Union[TradeSignal, IndexTrendSignal]) -> AIAnalysis:
    prompt = build_prompt(result)

    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ANTHROPIC_MODEL,
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        raw_text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        parsed = parse_ai_response(raw_text)

        return AIAnalysis(
            instrument=result.instrument,
            professional_analysis=parsed.get("professional_analysis") or "Analysis unavailable.",
            trade_summary=parsed.get("trade_summary") or "Summary unavailable.",
            risk_summary=parsed.get("risk_summary") or "Risk summary unavailable.",
            why_buy=parsed.get("why_buy"),
            why_sell=parsed.get("why_sell"),
        )

    except Exception as e:
        logger.error(f"AI analysis generation failed for {result.instrument}: {e}")
        # Graceful fallback — never block signal delivery because AI narration failed
        return AIAnalysis(
            instrument=result.instrument,
            professional_analysis="AI analysis temporarily unavailable.",
            trade_summary="See raw signal data.",
            risk_summary="Trade at your own discretion; AI commentary could not be generated.",
        )
