from app.core.config import get_settings
from app.schemas.rag import ChatTurn, KnowledgeHit, RetrieverMode
from app.services.keyword_retriever import keyword_search
from app.services.llm_service import LLMNotConfiguredError, generate_rag_answer
from app.services.vector_retriever import VectorRetrieverError, vector_search


def get_top_k(top_k: int | None = None) -> int:
    settings = get_settings()
    return top_k or settings.rag_top_k


def get_retriever_mode(retriever: RetrieverMode | None = None) -> RetrieverMode:
    settings = get_settings()
    mode = (retriever or settings.rag_retriever).lower()
    if mode not in {"keyword", "vector", "hybrid"}:
        return "hybrid"
    return mode  # type: ignore[return-value]


def _merge_hits(*hit_groups: list[KnowledgeHit], top_k: int) -> list[KnowledgeHit]:
    merged: dict[str, KnowledgeHit] = {}
    for hits in hit_groups:
        for hit in hits:
            current = merged.get(hit.chunk_id)
            if current is None or hit.score > current.score:
                merged[hit.chunk_id] = hit
    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:top_k]


def retrieve(query: str, top_k: int | None = None, retriever: RetrieverMode | None = None) -> tuple[list[KnowledgeHit], str]:
    settings = get_settings()
    if not settings.enable_rag:
        return [], "disabled"

    limit = get_top_k(top_k)
    mode = get_retriever_mode(retriever)

    if mode == "keyword":
        return keyword_search(query, limit), "keyword"

    if mode == "vector":
        try:
            return vector_search(query, limit), "vector"
        except VectorRetrieverError:
            return keyword_search(query, limit), "keyword_fallback"

    try:
        vector_hits = vector_search(query, limit)
        keyword_hits = keyword_search(query, limit)
        return _merge_hits(vector_hits, keyword_hits, top_k=limit), "hybrid"
    except VectorRetrieverError:
        return keyword_search(query, limit), "keyword_fallback"


def format_context(hits: list[KnowledgeHit]) -> str:
    chunks = []
    for hit in hits:
        chunks.append(f"## 来源：{hit.source}\n{hit.content}")
    return "\n\n".join(chunks)


def ask(
    question: str,
    top_k: int | None = None,
    retriever: RetrieverMode | None = None,
    chat_history: list[ChatTurn] | None = None,
) -> dict:
    hits, actual_retriever = retrieve(question, top_k=top_k, retriever=retriever)
    context = format_context(hits)
    settings = get_settings()

    if settings.llm_configured:
        try:
            answer = generate_rag_answer(question, context, chat_history or [])
        except LLMNotConfiguredError as exc:
            answer = f"{exc}\n\n以下为知识库检索结果：\n\n{context}"
    else:
        answer = (
            "当前未启用大语言模型，以下是根据知识库检索到的参考片段。\n\n"
            f"{context or '未检索到相关知识库片段。'}"
        )

    return {
        "answer": answer,
        "retriever": actual_retriever,
        "sources": [hit.source for hit in hits],
        "hits": [hit.model_dump() for hit in hits],
    }

