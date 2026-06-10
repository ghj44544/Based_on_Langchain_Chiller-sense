from fastapi import APIRouter

from app.core.response import error, success
from app.schemas.rag import AskRequest, ReindexRequest, SearchRequest
from app.services.document_loader import load_markdown_files
from app.services.rag_service import ask, retrieve
from app.services.vector_retriever import VectorRetrieverError, rebuild_vector_index


router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/sources")
def sources():
    documents = load_markdown_files()
    return success(
        data={
            "count": len(documents),
            "sources": [{"source": source, "characters": len(content)} for source, content in documents],
        }
    )


@router.post("/search")
def search(request: SearchRequest):
    hits, retriever = retrieve(request.query, top_k=request.top_k, retriever=request.retriever)
    return success(
        data={
            "query": request.query,
            "retriever": retriever,
            "hits": [hit.model_dump() for hit in hits],
        }
    )


@router.post("/ask")
def ask_question(request: AskRequest):
    return success(
        data=ask(
            request.question,
            top_k=request.top_k,
            retriever=request.retriever,
            chat_history=request.chat_history,
        )
    )


@router.post("/reindex")
def reindex(request: ReindexRequest):
    try:
        result = rebuild_vector_index(force=request.force)
    except VectorRetrieverError as exc:
        return error(str(exc), code=400)
    return success(data=result)
