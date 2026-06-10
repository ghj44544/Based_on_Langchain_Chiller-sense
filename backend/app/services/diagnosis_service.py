import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import DiagnosisRecord
from app.services.explanation_service import generate_explanation
from app.services.model_predictor import ModelPredictor
from app.services.preprocess_service import build_feature_matrix
from app.services.rp1043_validator import validate_rp1043_file


def run_diagnosis(file_path: Path, db: Session, predictor: ModelPredictor | None = None) -> dict[str, Any]:
    df, dataset_summary = validate_rp1043_file(file_path)
    features = build_feature_matrix(df)
    model_result = (predictor or ModelPredictor()).predict(features)
    explanation, suggestions = generate_explanation(model_result, dataset_summary)

    record = DiagnosisRecord(
        filename=file_path.name,
        file_path=str(file_path),
        total_rows=dataset_summary["total_rows"],
        total_columns=dataset_summary["total_columns"],
        has_label=dataset_summary["has_label"],
        label_distribution_json=json.dumps(dataset_summary["label_distribution"], ensure_ascii=False),
        dominant_label=model_result["dominant_label"],
        dominant_fault_name=model_result["dominant_fault_name"],
        dominant_ratio=model_result["dominant_ratio"],
        avg_confidence=model_result["avg_confidence"],
        prediction_distribution_json=json.dumps(model_result["prediction_distribution"], ensure_ascii=False),
        model_result_json=json.dumps(model_result, ensure_ascii=False),
        explanation=explanation,
        maintenance_suggestions_json=json.dumps(suggestions, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "diagnosis_id": record.id,
        "dataset_summary": dataset_summary,
        "model_result": model_result,
        "explanation": explanation,
        "maintenance_suggestions": suggestions,
    }

