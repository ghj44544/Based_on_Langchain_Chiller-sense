import shutil

from app.core.config import get_settings
from app.schemas.rag import KnowledgeHit
from app.services.document_loader import split_knowledge_documents


class VectorRetrieverError(RuntimeError):
    pass


def _build_embeddings():
    settings = get_settings()
    if not settings.embedding_configured:
        raise VectorRetrieverError("Embedding 参数不完整，请配置 OPENAI_API_KEY 和 OPENAI_EMBEDDING_MODEL。")

    try:
        from langchain_openai import OpenAIEmbeddings
    except ImportError as exc:
        raise VectorRetrieverError("未安装 langchain-openai，请先安装 requirements.txt。") from exc

    kwargs = {
        "api_key": settings.openai_api_key,
        "model": settings.openai_embedding_model,
        "timeout": settings.openai_timeout,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAIEmbeddings(**kwargs)


def _build_vector_store(rebuild: bool = False):
    settings = get_settings()
    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise VectorRetrieverError("未安装 LangChain 文档依赖，请先安装 requirements.txt。") from exc

    try:
        from langchain_chroma import Chroma
    except ImportError:
        try:
            from langchain_community.vectorstores import Chroma
        except ImportError as exc:
            raise VectorRetrieverError("未安装 Chroma 向量库依赖，请先安装 requirements.txt。") from exc

    embeddings = _build_embeddings()
    if rebuild and settings.vector_path.exists():
        shutil.rmtree(settings.vector_path)

    has_index = settings.vector_path.exists() and any(settings.vector_path.iterdir())
    if has_index:
        return Chroma(
            collection_name=settings.rag_collection_name,
            embedding_function=embeddings,
            persist_directory=str(settings.vector_path),
        )

    chunks = split_knowledge_documents()
    if not chunks:
        raise VectorRetrieverError("知识库为空，请先在 knowledge_base 中添加 Markdown 文件。")

    documents = [
        Document(
            page_content=chunk.content,
            metadata={"source": chunk.source, "chunk_id": chunk.chunk_id},
        )
        for chunk in chunks
    ]
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=settings.rag_collection_name,
        persist_directory=str(settings.vector_path),
    )


def rebuild_vector_index(force: bool = True) -> dict[str, int | str]:
    try:
        store = _build_vector_store(rebuild=force)
    except Exception as exc:
        if isinstance(exc, VectorRetrieverError):
            raise
        raise VectorRetrieverError(f"向量库构建失败：{exc}") from exc

    settings = get_settings()
    return {
        "collection": settings.rag_collection_name,
        "persist_directory": str(settings.vector_path),
        "chunks": store._collection.count(),
    }


def vector_search(query: str, top_k: int) -> list[KnowledgeHit]:
    try:
        store = _build_vector_store(rebuild=False)
        results = store.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception as exc:
        if isinstance(exc, VectorRetrieverError):
            raise
        raise VectorRetrieverError(f"向量检索失败：{exc}") from exc

    hits: list[KnowledgeHit] = []
    for document, score in results:
        hits.append(
            KnowledgeHit(
                source=str(document.metadata.get("source", "unknown")),
                chunk_id=str(document.metadata.get("chunk_id", "")),
                score=float(score),
                content=document.page_content,
            )
        )
    return hits
