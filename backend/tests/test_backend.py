import io
import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.model_predictor import ModelNotFoundError, ModelPredictor
from app.services.rp1043_validator import (
    ValidationError,
    load_feature_columns,
    validate_rp1043_dataframe,
    validate_rp1043_file,
)


client = TestClient(app)


def sample_dataframe(include_label: bool = True) -> pd.DataFrame:
    data = {column: [1.0, 2.0] for column in load_feature_columns()}
    if include_label:
        data["label"] = [1, 2]
    return pd.DataFrame(data)


def test_read_excel_and_csv(tmp_path: Path):
    df = sample_dataframe()
    excel_path = tmp_path / "sample.xlsx"
    csv_path = tmp_path / "sample.csv"
    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False)

    _, excel_summary = validate_rp1043_file(excel_path)
    _, csv_summary = validate_rp1043_file(csv_path)

    assert excel_summary["total_rows"] == 2
    assert csv_summary["total_columns"] == 65


def test_field_validation_success():
    _, summary = validate_rp1043_dataframe(sample_dataframe(), filename="ok.csv")

    assert summary["missing_columns"] == []
    assert summary["has_label"] is True
    assert summary["label_distribution"] == {"1": 1, "2": 1}


def test_label_optional():
    _, summary = validate_rp1043_dataframe(sample_dataframe(include_label=False), filename="no_label.csv")

    assert summary["has_label"] is False
    assert summary["total_columns"] == 64


def test_missing_field_raises_clear_error():
    df = sample_dataframe().drop(columns=["TEI"])

    with pytest.raises(ValidationError) as exc:
        validate_rp1043_dataframe(df, filename="missing.csv")

    assert "缺少必要特征字段" in str(exc.value)
    assert exc.value.summary["missing_columns"] == ["TEI"]


def test_model_missing_returns_clear_error(tmp_path: Path):
    predictor = ModelPredictor(
        model_path=tmp_path / "fault_model.pkl",
        scaler_path=tmp_path / "scaler.pkl",
        label_map_path=Path("saved_models/label_map.json"),
    )

    with pytest.raises(ModelNotFoundError) as exc:
        predictor.predict(sample_dataframe(include_label=False))

    assert "模型文件不存在" in str(exc.value)


def test_health_api():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["app"] == "Chiller Fault Diagnosis LangChain System"
    assert "llm_configured" in payload["data"]


def test_chat_returns_clear_error_when_llm_disabled(monkeypatch):
    import app.api.chat as chat_api

    class DisabledLLMSettings:
        enable_llm = False

    monkeypatch.setattr(chat_api, "get_settings", lambda: DisabledLLMSettings())
    response = client.post(
        "/api/chat",
        json={"diagnosis_id": 1, "question": "为什么判断为这个故障？"},
    )

    assert response.status_code == 400
    assert "当前未启用大语言模型" in response.json()["message"]


def test_report_generate_and_download():
    response = client.post("/api/report/generate/1")
    if response.status_code == 404:
        pytest.skip("No diagnosis record fixture is available.")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    data = payload["data"]
    assert data["report_filename"].endswith(".md")
    assert data["download_url"].startswith("/api/report/download/")

    latest_response = client.get("/api/report/latest/1")
    assert latest_response.status_code == 200
    assert latest_response.json()["data"]["report_filename"].endswith(".md")

    download_response = client.get(data["download_url"])
    assert download_response.status_code == 200
    assert "冷水机组故障诊断报告" in download_response.text
    assert "attachment" in download_response.headers.get("content-disposition", "")


def test_report_generate_html_and_download():
    response = client.post("/api/report/generate/1?report_format=html")
    if response.status_code == 404:
        pytest.skip("No diagnosis record fixture is available.")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["report_format"] == "html"
    assert data["report_filename"].endswith(".html")

    latest_response = client.get("/api/report/latest/1?report_format=html")
    assert latest_response.status_code == 200
    assert latest_response.json()["data"]["report_format"] == "html"

    download_response = client.get(data["download_url"])
    assert download_response.status_code == 200
    assert "<html" in download_response.text
    assert "冷水机组故障诊断报告" in download_response.text


def test_diagnosis_upload_returns_clear_model_runtime_error():
    df = sample_dataframe()
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)

    response = client.post(
        "/api/diagnosis/upload",
        files={"file": ("sample.csv", buffer.getvalue(), "text/csv")},
    )

    assert response.status_code == 400
    assert any(
        phrase in response.json()["message"]
        for phrase in ["MATLAB Engine", "模型文件不存在", "模型期望 12 个输入特征"]
    )
