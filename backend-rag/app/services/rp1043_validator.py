import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import get_settings


class ValidationError(ValueError):
    def __init__(self, message: str, summary: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.summary = summary or {}


def load_feature_columns() -> list[str]:
    path = get_settings().feature_columns_file
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_model_feature_columns() -> list[str]:
    path = get_settings().model_feature_columns_file
    if path and path.exists():
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    return []


def read_dataset(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path, sheet_name=0)
    else:
        raise ValidationError("仅支持 .xlsx、.xls、.csv 文件")

    df.columns = [str(column).strip() for column in df.columns]
    return df


def validate_rp1043_dataframe(df: pd.DataFrame, filename: str = "") -> tuple[pd.DataFrame, dict[str, Any]]:
    feature_columns = load_feature_columns()
    model_feature_columns = load_model_feature_columns()
    columns = list(df.columns)
    missing_full_columns = [column for column in feature_columns if column not in columns]
    missing_model_columns = [
        column for column in model_feature_columns if column not in columns
    ]

    has_all_full_features = not missing_full_columns
    has_all_model_features = bool(model_feature_columns) and not missing_model_columns
    model_ready_column_count = len(model_feature_columns) + int("label" in columns)

    if has_all_full_features:
        validation_mode = "rp1043_full"
        required_columns = feature_columns
        missing_columns: list[str] = []
    elif has_all_model_features and len(columns) <= model_ready_column_count:
        validation_mode = "model_features"
        required_columns = model_feature_columns
        missing_columns = []
    else:
        validation_mode = "rp1043_full"
        required_columns = feature_columns
        missing_columns = missing_full_columns

    allowed_columns = set(required_columns) | {"label"}
    extra_columns = [column for column in columns if column not in allowed_columns]

    has_label = "label" in columns
    label_distribution: dict[str, int] = {}
    if has_label:
        label_distribution = {
            str(key): int(value)
            for key, value in df["label"].value_counts(dropna=False).items()
        }

    null_summary = {
        str(column): int(count)
        for column, count in df.isna().sum().items()
        if int(count) > 0
    }

    non_numeric_columns: dict[str, int] = {}
    converted = df.copy()
    for column in required_columns:
        if column not in converted.columns:
            continue
        numeric_series = pd.to_numeric(converted[column], errors="coerce")
        invalid_count = int(numeric_series.isna().sum() - converted[column].isna().sum())
        if invalid_count > 0:
            non_numeric_columns[column] = invalid_count
        converted[column] = numeric_series

    feature_null_summary = {
        column: int(converted[column].isna().sum())
        for column in required_columns
        if column in converted.columns and int(converted[column].isna().sum()) > 0
    }

    summary = {
        "filename": filename,
        "total_rows": int(len(df)),
        "total_columns": int(len(columns)),
        "feature_columns_count": int(len(required_columns)),
        "validation_mode": validation_mode,
        "rp1043_feature_columns_count": int(len(feature_columns)),
        "model_feature_columns_count": int(len(model_feature_columns)),
        "has_label": has_label,
        "label_distribution": label_distribution,
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "null_summary": null_summary,
        "feature_null_summary": feature_null_summary,
        "non_numeric_columns": non_numeric_columns,
    }

    errors = []
    if missing_columns:
        errors.append(f"缺少必要特征字段: {', '.join(missing_columns)}")
    if non_numeric_columns:
        errors.append(f"以下特征字段存在无法转换为数值的内容: {', '.join(non_numeric_columns)}")
    if feature_null_summary:
        errors.append(f"以下特征字段存在空值或无效值: {', '.join(feature_null_summary)}")

    if errors:
        raise ValidationError("；".join(errors), summary=summary)
    return converted, summary


def validate_rp1043_file(file_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = read_dataset(file_path)
    return validate_rp1043_dataframe(df, filename=file_path.name)
