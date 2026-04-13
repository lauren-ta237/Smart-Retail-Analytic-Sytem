# this service allows your system to ask AI questions about store data

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from ai.prompts.retail_prompts import interactive_store_prompt
from ai.tools.analytics_tools import AnalyticsTools
from backend.app.utils.logger import setup_logger

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logger = setup_logger()


class LLMService:
    """
    Service responsible for communicating with
    the Large Language Model (LLM).
    """

    def __init__(self, model: str = None, temperature: float = 0.2):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        ) if self.api_key else None
        
        # Use provided model, then env var, then a guaranteed working default
        env_model = os.getenv("LLM_MODEL")
        self.model = model or (env_model if env_model and ":" in env_model else "google/gemini-2.0-flash-lite-001")
        self.temperature = temperature
        self.timeout = float(os.getenv("OPENAI_TIMEOUT", "20"))

        if self.api_key:
            logger.info("LLMService initialized with API key present; model=%s", self.model)
        else:
            logger.warning("LLMService initialized without API key; fallback responses will be used")

    def generate_response(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns the response.
        """
        if not self.client:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        logger.info("Sending request to OpenRouter model=%s", self.model)
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            timeout=self.timeout,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI retail analytics expert. "
                        "Answer only from the provided live and historical store context. "
                        "Base every answer on the supplied evidence and clearly mention trends, changes, and gaps."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content or ""

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured": bool(self.api_key),
            "model": self.model,
            "timeout": self.timeout,
            "mode": "openrouter" if self.client else "fallback",
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Forces a minimal OpenRouter call and logs the exact result immediately.
        """
        try:
            reply = self.generate_response("Reply with exactly: OK").strip()
            logger.info("OpenRouter connectivity test succeeded; model=%s; reply=%s", self.model, reply)
            return {
                "ok": True,
                "model": self.model,
                "reply": reply,
                "message": "OpenRouter key is working inside the backend.",
            }
        except Exception as exc:
            logger.exception("OpenRouter connectivity test failed for model=%s: %s", self.model, exc)
            return {
                "ok": False,
                "model": self.model,
                "error": str(exc),
                "message": "OpenRouter key test failed inside the backend.",
            }

    def answer_live_question(self, question: str, db: Session) -> Dict[str, Any]:
        """
        Builds live + historical context from the running store data,
        then answers the user's question.
        """
        tools = AnalyticsTools(db)
        combined_context = tools.build_ai_context()
        live_data = combined_context["live"]
        historical_data = combined_context["historical"]
        recommended_actions = combined_context.get("recommended_actions", [])
        prompt = interactive_store_prompt(question, live_data, historical_data, recommended_actions)

        try:
            answer = self.generate_response(prompt).strip()
            source = "openrouter_live_historical_store_data"
            logger.info("OpenRouter response generated successfully for retail question")
        except Exception as exc:
            logger.exception("OpenRouter request failed; using fallback response instead: %s", exc)
            answer = self._build_fallback_answer(question, live_data, historical_data)
            source = "store_data_fallback"

        return {
            "question": question,
            "answer": answer,
            "source": source,
            "live_data": live_data,
            "historical_data": historical_data,
        }

    def _build_fallback_answer(
        self,
        question: str,
        live_data: Dict[str, Any],
        historical_data: Dict[str, Any],
    ) -> str:
        customers = live_data.get("customers", {})
        top_products = live_data.get("top_products", [])
        peak_hours = historical_data.get("peak_hours_history", [])
        repeat_customers = historical_data.get("repeat_customers", [])
        avg_duration = historical_data.get("average_visit_duration", {})
        recent_logs = live_data.get("recent_logs", [])

        lines = [
            "Your assistant now uses live and historical store intelligence:",
            f"- Total tracked customers: {customers.get('total_customers', 0)}",
            f"- Active customers in store now: {customers.get('active_customers', 0)}",
            f"- Average visit duration: {avg_duration.get('avg_minutes', 0)} minutes",
        ]

        if top_products:
            labels = ", ".join(str(item.get("product")) for item in top_products[:3])
            lines.append(f"- Strongest product interest: {labels}")

        if peak_hours:
            hours = ", ".join(str(item.get("hour")) for item in peak_hours[:3])
            lines.append(f"- Historical peak hours: {hours}")

        if repeat_customers:
            lines.append(f"- Returning-customer signals detected: {len(repeat_customers)}")

        if recent_logs:
            lines.append(f"- Latest system log: {recent_logs[-1]}")

        lines.append(f"- Question asked: {question}")
        return "\n".join(lines)


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """
    Returns a single shared LLM service instance for the app process.
    """
    return LLMService()