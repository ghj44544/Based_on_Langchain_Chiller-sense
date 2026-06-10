from app.schemas.rag import KnowledgeHit
from app.services.rag_service import format_context, retrieve


def load_knowledge_documents() -> list[tuple[str, str]]:
    from app.services.document_loader import load_markdown_files

    return load_markdown_files()


def retrieve_knowledge_hits(query: str, limit: int = 4) -> list[KnowledgeHit]:
    hits, _ = retrieve(query, top_k=limit)
    return hits


def format_knowledge_hits(hits: list[KnowledgeHit]) -> str:
    return format_context(hits)


def retrieve_knowledge(query: str, limit: int = 4) -> str:
    return format_knowledge_hits(retrieve_knowledge_hits(query, limit=limit))
