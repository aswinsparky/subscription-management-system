"""
Pydantic v2 Schemas for Ask Brightloop AI Assistant.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AIAssistantQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, example="How much revenue is overdue this month?")


class AIAssistantQueryResponse(BaseModel):
    query: str
    answer: str
    grounded_data: Dict[str, Any]
    provider: str  # "gemini" or "deterministic_engine"
    suggested_followups: List[str]

