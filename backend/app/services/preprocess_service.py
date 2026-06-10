import pandas as pd

from app.core.config import get_settings
from app.services.rp1043_validator import load_feature_columns


def load_model_feature_columns() -> list[str]:
    settings = get_settings()
    model_feature_path = settings.model_feature_columns_file
    if model_feature_path and model_feature_path.exists():
        import json

        with model_feature_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    return load_feature_columns()


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    feature_columns = load_model_feature_columns()
    missing = [column for column in feature_columns if column not in df.columns]
    if missing:
        raise ValueError(f"模型输入特征缺失: {', '.join(missing)}")

    matrix = df[feature_columns].copy()
    for column in feature_columns:
        matrix[column] = pd.to_numeric(matrix[column], errors="coerce")

    if matrix.isna().any().any():
        bad_columns = [column for column in matrix.columns if matrix[column].isna().any()]
        raise ValueError(f"特征矩阵存在空值或无效值: {', '.join(bad_columns)}")
    return matrix
