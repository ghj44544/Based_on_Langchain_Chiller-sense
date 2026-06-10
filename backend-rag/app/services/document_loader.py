from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    chunk_id: str
    content: str


def load_markdown_files(kb_dir: Path | None = None) -> list[tuple[str, str]]:
    settings = get_settings()
    base_dir = kb_dir or settings.knowledge_base_path
    if not base_dir.exists():
        return []

    documents: list[tuple[str, str]] = []
    for path in sorted(base_dir.glob("*.md")):
        documents.append((path.name, path.read_text(encoding="utf-8")))
    return documents


def _fallback_split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - chunk_overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def split_knowledge_documents() -> list[KnowledgeChunk]:
    settings = get_settings()
    documents = load_markdown_files()
    chunks: list[KnowledgeChunk] = []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", "。", ".", " ", ""],
        )
        split_fn = splitter.split_text
    except ImportError:
        split_fn = lambda text: _fallback_split_text(
            text,
            settings.rag_chunk_size,
            settings.rag_chunk_overlap,
        )

    for source, content in documents:
        for index, chunk in enumerate(split_fn(content)):
            chunk_id = f"{source}#{index}"
            chunks.append(KnowledgeChunk(source=source, chunk_id=chunk_id, content=chunk))
    return chunks

