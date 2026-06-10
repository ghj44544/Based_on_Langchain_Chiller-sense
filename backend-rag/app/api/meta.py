import json

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.response import success
from app.services.document_loader import split_knowledge_documents
from app.services.model_predictor import ModelPredictor


router = APIRouter(tags=["meta"])


@router.get("/meta/features")
def features():
    path = get_settings().feature_columns_file
    return success(data=json.loads(path.read_text(encoding="utf-8")))


@router.get("/meta/labels")
def labels():
    path = get_settings().label_map_file
    return success(data=json.loads(path.read_text(encoding="utf-8")))


@router.get("/health")
def health():
    settings = get_settings()
    predictor = ModelPredictor()
    knowledge_chunks = split_knowledge_documents()
    matlab_engine_available = None
    matlab_shared_engines = None
    if predictor.model_path.suffix.lower() == ".mat":
        try:
            import matlab.engine

            matlab_engine_available = True
            matlab_shared_engines = list(matlab.engine.find_matlab())
        except ImportError:
            matlab_engine_available = False

    return success(
        data={
            "app": settings.app_name,
            "model_loaded": predictor.model_loaded,
            "scaler_loaded": predictor.scaler_loaded,
            "model_path": str(predictor.model_path),
            "model_type": predictor.model_path.suffix.lower().lstrip(".") or "unknown",
            "matlab_engine_available": matlab_engine_available,
            "matlab_shared_engines": matlab_shared_engines,
            "llm_enabled": settings.enable_llm,
            "llm_configured": bool(settings.openai_api_key and settings.openai_model),
            "llm_provider": settings.llm_provider,
            "llm_model": settings.openai_model or None,
            "rag_enabled": settings.enable_rag,
            "rag_retriever": settings.rag_retriever,
            "embedding_configured": settings.embedding_configured,
            "knowledge_base_dir": str(settings.knowledge_base_path),
            "knowledge_chunks": len(knowledge_chunks),
        }
    )
