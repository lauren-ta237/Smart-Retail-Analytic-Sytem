# The schemas folder defines how data is shaped when it enters or leaves your API
from typing import Any, Dict

from pydantic import BaseModel, Field


class AIQuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        description="Natural language question about live customers, products, and store activity."
    )


class AIQuestionResponse(BaseModel):
    question: str
    answer: str
    source: str
    live_data: Dict[str, Any]
    historical_data: Dict[str, Any]
