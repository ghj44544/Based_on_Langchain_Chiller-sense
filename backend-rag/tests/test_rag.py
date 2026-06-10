from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_api():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["app"] == "Chiller Fault Diagnosis LangChain System"
    assert "model_loaded" in payload["data"]
    assert "rag_retriever" in payload["data"]
    assert payload["data"]["knowledge_chunks"] > 0


def test_keyword_search_returns_sources():
    response = client.post(
        "/api/rag/search",
        json={"query": "制冷剂泄漏 应该检查哪里", "retriever": "keyword", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["retriever"] == "keyword"
    assert data["hits"]
    assert any(hit["source"] == "refrigerant_leak.md" for hit in data["hits"])


def test_hybrid_search_falls_back_without_embedding_config():
    response = client.post(
        "/api/rag/search",
        json={"query": "冷凝器结垢 有什么表现", "retriever": "hybrid", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["retriever"] == "keyword_fallback"
    assert data["hits"]


def test_ask_without_llm_returns_retrieved_context():
    response = client.post(
        "/api/rag/ask",
        json={"question": "制冷剂泄漏有哪些维修建议？", "retriever": "keyword"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "当前未启用大语言模型" in data["answer"]
    assert "refrigerant_leak.md" in data["sources"]
