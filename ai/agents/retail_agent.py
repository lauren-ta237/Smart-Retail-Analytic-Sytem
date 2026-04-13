# decision makers e.g what data to fetch, how to structure requests, when to include history
# Let me gather everything before asking ai. that's how it thinks
import logging
import time
from functools import lru_cache
from ai.prompts.retail_prompts import store_analysis_prompt
from ai.tools.analytics_tools import AnalyticsTools
from ai.llm_service import LLMService, get_llm_service

# -------------------------------
# UPGRADED LLM SERVICE
# -------------------------------
class RobustLLMService(LLMService):
    """
    LLM wrapper with retries, memory, logging, and safe fallback
    """
    def __init__(self, model="gpt-4o-mini", temperature=0.7, max_retries=3, timeout=10.0):
        shared_service = get_llm_service()
        self.api_key = shared_service.api_key
        self.client = shared_service.client
        self.model = model or shared_service.model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.memory = []  # store conversation context

    def generate_response(self, prompt: str, use_memory: bool = True) -> str:
        if use_memory and self.memory:
            context = "\n".join(self.memory[-10:])  # last 10 messages
            full_prompt = f"{context}\n{prompt}"
        else:
            full_prompt = prompt

        logging.info(f"LLM Prompt: {prompt[:200]}...")  # first 200 chars

        for attempt in range(1, self.max_retries + 1):
            try:
                response = super().generate_response(full_prompt)
                text_response = response.strip()

                if use_memory:
                    self.memory.append(f"Prompt: {prompt}")
                    self.memory.append(f"Response: {text_response}")

                logging.info(f"LLM Response: {text_response[:200]}...")
                return text_response

            except Exception as e:
                logging.warning(f"LLM attempt {attempt}/{self.max_retries} failed: {e}")
                time.sleep(1)  # could implement exponential backoff

        logging.error("LLM failed after all retries. Returning fallback message.")
        return "⚠️ Error: Unable to generate AI response at this time."

    def reset_memory(self):
        self.memory = []
        logging.info("LLM memory cleared.")


@lru_cache(maxsize=1)
def get_retail_llm() -> "RobustLLMService":
    """Reuse one robust LLM wrapper for retail-agent analysis."""
    return RobustLLMService(model="gpt-4o-mini", temperature=0.7)


# -------------------------------
# RETAIL AGENT
# -------------------------------
class RetailAgent:
    """
    AI agent generating intelligent insights from retail analytics
    """
    def __init__(self, db):
        self.db = db
        self.tools = AnalyticsTools(db)
        self.llm = get_retail_llm()

    def analyze_store(self):
        analytics_data = {
            "live_context": self.tools.build_live_context(),
            "historical_context": self.tools.build_historical_context(),
            "zone_traffic": self.tools.get_zone_traffic(),
            "product_interactions": self.tools.get_top_products(),
            "peak_hours": self.tools.get_peak_hours()
        }

        prompt = store_analysis_prompt(analytics_data)
        insights = self.llm.generate_response(prompt)

        return insights