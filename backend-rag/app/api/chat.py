import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.response import error, success
from app.db.models import ChatMessage, DiagnosisRecord
from app.db.session import get_db
from app.langchain_app.chains import LLMNotConfiguredError, generate_chat_answer
from app.langchain_app.rag import format_knowledge_hits, retrieve_knowledge_hits
from app.schemas.chat import ChatRequest
from app.services.explanation_service import LLM_DISABLED_MESSAGE


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.enable_llm:
        return error(LLM_DISABLED_MESSAGE, code=400)

    record = db.get(DiagnosisRecord, request.diagnosis_id)
    if record is None:
        return error("诊断记录不存在", code=404)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.diagnosis_id == request.diagnosis_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    chat_history = "\n".join(f"{message.role}: {message.content}" for message in messages[-10:])
    model_result = json.loads(record.model_result_json or "{}")
    diagnosis_context = {
        "diagnosis_id": record.id,
        "filename": record.filename,
        "model_result": model_result,
        "explanation": record.explanation,
        "maintenance_suggestions": json.loads(record.maintenance_suggestions_json or "[]"),
    }
    query = f"{model_result.get('dominant_label')} {model_result.get('dominant_fault_name')} {request.question}"
    hits = retrieve_knowledge_hits(query) if settings.enable_rag else []
    context = format_knowledge_hits(hits)

    try:
        answer = generate_chat_answer(diagnosis_context, chat_history, context, request.question)
    except LLMNotConfiguredError as exc:
        return error(str(exc), code=400)

    db.add(ChatMessage(diagnosis_id=request.diagnosis_id, role="user", content=request.question))
    db.add(ChatMessage(diagnosis_id=request.diagnosis_id, role="assistant", content=answer))
    db.commit()
    return success(
        data={
            "answer": answer,
            "sources": [hit.source for hit in hits],
        }
    )
