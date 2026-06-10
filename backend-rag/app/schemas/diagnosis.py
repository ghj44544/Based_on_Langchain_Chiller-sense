from pydantic import BaseModel


class RowPrediction(BaseModel):
    row_index: int
    predicted_label: str
    fault_name: str
    confidence: float | None = None


class ModelResult(BaseModel):
    total_rows: int
    dominant_label: str
    dominant_fault_name: str
    dominant_ratio: float
    avg_confidence: float | None = None
    severity: str
    prediction_distribution: dict[str, int]
    row_predictions_preview: list[RowPrediction]


class DiagnosisResponseData(BaseModel):
    diagnosis_id: int
    dataset_summary: dict
    model_result: dict
    explanation: str
    maintenance_suggestions: list[str]

