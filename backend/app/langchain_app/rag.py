from pathlib import Path
import re
from dataclasses import dataclass

from app.core.config import BASE_DIR


KB_DIR = BASE_DIR / "knowledge_base"


@dataclass
class KnowledgeHit:
    source: str
    score: int
    content: str


FAULT_KEYWORDS = {
    "制冷剂过量": ["制冷剂过量", "制冷剂过充", "overcharge", "ro", "refrigerant overcharge"],
    "制冷剂泄漏": ["制冷剂泄漏", "泄漏", "leak", "rl", "refrigerant leak"],
    "润滑油加注过量": ["润滑油", "油过量", "oil", "eo", "excess oil"],
    "不凝性气体": ["不凝性气体", "non-condensable", "non condensable", "nc"],
    "冷凝器结垢": ["冷凝器结垢", "冷凝器污垢", "fouling", "cf", "condenser fouling"],
    "冷却水流量不足": ["冷却水流量不足", "冷凝水流量降低", "冷却水", "fwc", "condenser water flow"],
    "冷冻水流量不足": ["冷冻水流量不足", "蒸发器水流量降低", "冷冻水", "fwe", "evaporator water flow"],
    "正常": ["正常", "normal", "healthy"],
}


def load_knowledge_documents() -> list[tuple[str, str]]:
    if not KB_DIR.exists():
        return []
    documents = []
    for path in sorted(KB_DIR.glob("*.md")):
        documents.append((path.name, path.read_text(encoding="utf-8")))
    return documents


def _query_terms(query: str) -> list[str]:
    raw = query.lower()
    terms = [term for term in re.split(r"[\s,，。；;:：()（）/\\[\]{}]+", raw) if term]
    for fault_name, keywords in FAULT_KEYWORDS.items():
        if fault_name in query:
            terms.extend(keyword.lower() for keyword in keywords)
    return list(dict.fromkeys(terms))


def retrieve_knowledge_hits(query: str, limit: int = 4) -> list[KnowledgeHit]:
    query_terms = _query_terms(query)
    documents = load_knowledge_documents()
    scored: list[KnowledgeHit] = []
    for filename, content in documents:
        haystack = f"{filename}\n{content}".lower()
        score = sum(haystack.count(term) for term in query_terms)
        scored.append(KnowledgeHit(source=filename, score=score, content=content))

    scored.sort(key=lambda item: item.score, reverse=True)
    positive = [hit for hit in scored if hit.score > 0]
    if positive:
        return positive[:limit]
    return scored[:limit]


def format_knowledge_hits(hits: list[KnowledgeHit]) -> str:
    chunks = []
    for hit in hits:
        chunks.append(f"## 来源：{hit.source}\n{hit.content[:2000]}")
    return "\n\n".join(chunks)


def retrieve_knowledge(query: str, limit: int = 4) -> str:
    return format_knowledge_hits(retrieve_knowledge_hits(query, limit=limit))
