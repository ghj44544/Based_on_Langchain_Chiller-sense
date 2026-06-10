import re

from app.schemas.rag import KnowledgeHit
from app.services.document_loader import split_knowledge_documents


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


def _query_terms(query: str) -> list[str]:
    raw = query.lower()
    terms = [term for term in re.split(r"[\s,，。；;:：()（）/\\[\]{}]+", raw) if term]
    for fault_name, keywords in FAULT_KEYWORDS.items():
        if fault_name in query:
            terms.extend(keyword.lower() for keyword in keywords)
    return list(dict.fromkeys(terms))


def keyword_search(query: str, top_k: int) -> list[KnowledgeHit]:
    terms = _query_terms(query)
    hits: list[KnowledgeHit] = []
    for chunk in split_knowledge_documents():
        haystack = f"{chunk.source}\n{chunk.content}".lower()
        score = float(sum(haystack.count(term) for term in terms))
        hits.append(
            KnowledgeHit(
                source=chunk.source,
                chunk_id=chunk.chunk_id,
                score=score,
                content=chunk.content,
            )
        )

    hits.sort(key=lambda item: item.score, reverse=True)
    positive = [hit for hit in hits if hit.score > 0]
    return (positive or hits)[:top_k]

