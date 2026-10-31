"""
Ask Brightloop AI Assistant API Endpoints (Member 2).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user
from app.models.user import User
from app.schemas.ai_assistant import AIAssistantQueryRequest, AIAssistantQueryResponse
from app.services.ai_assistant_service import AIAssistantService

router = APIRouter()


@router.post("/query", response_model=AIAssistantQueryResponse, summary="Ask natural language question grounded in DB metrics")
def query_ai_assistant(
    data: AIAssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return AIAssistantService.answer_query(db, data.query)

