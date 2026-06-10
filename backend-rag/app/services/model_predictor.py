import json
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.config import BASE_DIR
from app.core.config import get_settings


class ModelNotFoundError(FileNotFoundError):
    pass


class MatlabEngineError(RuntimeError):
    pass


class ModelPredictor:
    _matlab_engine: Any | None = None

    def __init__(
        self,
        model_path: Path | None = None,
        scaler_path: Path | None = None,
        label_map_path: Path | None = None,
    ) -> None:
        settings = get_settings()
        self.model_path = model_path or settings.model_file
        self.scaler_path = scaler_path or settings.scaler_file
        self.label_map_path = label_map_path or settings.label_map_file
        self._model: Any | None = None
        self._scaler: Any | None = None
        self._label_map: dict[str, str] | None = None
        self._model_feature_columns: list[str] | None = None

    @property
    def model_loaded(self) -> bool:
        return self.model_path.exists()

    @property
    def scaler_loaded(self) -> bool:
        return self.scaler_path.exists()

    def load_label_map(self) -> dict[str, str]:
        if self._label_map is None:
            with self.label_map_path.open("r", encoding="utf-8") as file:
                self._label_map = json.load(file)
        return self._label_map

    def load(self) -> None:
        suffix = self.model_path.suffix.lower()
        if suffix == ".m":
            raise ModelNotFoundError(
                "检测到 MATLAB .m 脚本，但 .m 文件是训练/实验代码，不能被 Python 后端直接当作模型预测。"
                "请先在 MATLAB 中运行脚本并导出可推理模型，再转换为 saved_models/fault_model.pkl，"
                "或提供 MATLAB Engine/ONNX 推理方案。"
            )
        if suffix == ".mat":
            if not self.model_path.exists():
                raise ModelNotFoundError(f"MATLAB 模型文件不存在: {self.model_path}")
            return
        if not self.model_path.exists():
            matlab_scripts = sorted(path.name for path in BASE_DIR.glob("*.m"))
            hint = ""
            if matlab_scripts:
                hint = (
                    f" 已检测到 MATLAB 脚本: {', '.join(matlab_scripts)}；"
                    "它看起来是训练/对比实验脚本，不是 Python 可直接加载的预测模型。"
                )
            raise ModelNotFoundError(
                "模型文件不存在，请将训练好的模型放到 saved_models/fault_model.pkl。"
                f"{hint}"
            )
        if self._model is None:
            loaded_model = joblib.load(self.model_path)
            if isinstance(loaded_model, dict) and "model" in loaded_model:
                self._model = loaded_model["model"]
                feature_columns = loaded_model.get("feature_columns")
                if feature_columns:
                    self._model_feature_columns = [str(column) for column in feature_columns]
                artifact_label_map = loaded_model.get("label_map")
                if artifact_label_map and self._label_map is None:
                    self._label_map = {
                        str(key): str(value)
                        for key, value in artifact_label_map.items()
                    }
            else:
                self._model = loaded_model
        if self.scaler_path.exists() and self._scaler is None:
            self._scaler = joblib.load(self.scaler_path)

    def predict(self, features: pd.DataFrame) -> dict[str, Any]:
        if features.empty:
            raise ValueError("输入数据为空，无法进行模型预测")

        self.load()
        if self.model_path.suffix.lower() == ".mat":
            expected_count = self._get_matlab_expected_feature_count()
            if expected_count and features.shape[1] != expected_count:
                raise ValueError(
                    f"MATLAB ultra 模型期望 {expected_count} 个输入特征，"
                    f"当前后端提供了 {features.shape[1]} 个。"
                    "请在 saved_models/model_feature_columns.json 中配置训练该模型时使用的特征列名，"
                    "并在 .env 中设置 MODEL_FEATURE_COLUMNS_PATH=saved_models/model_feature_columns.json。"
                )
            predicted_labels, confidences = self._predict_with_matlab(features)
            return self._build_result(predicted_labels, confidences)

        label_map = self.load_label_map()
        model = self._model
        scaler = self._scaler

        model_features = self._align_model_features(features)
        transformed = scaler.transform(model_features) if scaler is not None else model_features
        predictions = model.predict(transformed)
        predicted_labels = [str(item) for item in predictions]

        confidences: list[float | None] = [None] * len(predicted_labels)
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(transformed)
            confidences = [round(float(np.max(row)), 6) for row in probabilities]

        return self._build_result(predicted_labels, confidences)

    def _align_model_features(self, features: pd.DataFrame) -> pd.DataFrame:
        if not self._model_feature_columns:
            return features

        missing = [
            column
            for column in self._model_feature_columns
            if column not in features.columns
        ]
        if missing:
            raise ValueError(f"模型输入特征缺失: {', '.join(missing)}")
        return features.loc[:, self._model_feature_columns]

    def _build_result(
        self,
        predicted_labels: list[str],
        confidences: list[float | None],
    ) -> dict[str, Any]:
        label_map = self.load_label_map()
        distribution = dict(sorted(Counter(predicted_labels).items(), key=lambda item: item[0]))
        dominant_label, dominant_count = Counter(predicted_labels).most_common(1)[0]
        dominant_ratio = dominant_count / len(predicted_labels) if predicted_labels else 0

        valid_confidences = [value for value in confidences if value is not None]
        avg_confidence = (
            round(float(np.mean(valid_confidences)), 6)
            if valid_confidences
            else None
        )

        row_preview = []
        for index, (label, confidence) in enumerate(zip(predicted_labels[:20], confidences[:20]), start=1):
            row_preview.append(
                {
                    "row_index": index,
                    "predicted_label": label,
                    "fault_name": label_map.get(label, f"未知类别_{label}"),
                    "confidence": confidence,
                }
            )

        return {
            "total_rows": int(len(predicted_labels)),
            "dominant_label": dominant_label,
            "dominant_fault_name": label_map.get(dominant_label, f"未知类别_{dominant_label}"),
            "dominant_ratio": round(float(dominant_ratio), 6),
            "avg_confidence": avg_confidence,
            "severity": self._infer_severity(dominant_ratio, avg_confidence),
            "prediction_distribution": {str(key): int(value) for key, value in distribution.items()},
            "row_predictions_preview": row_preview,
        }

    def _predict_with_matlab(self, features: pd.DataFrame) -> tuple[list[str], list[float | None]]:
        try:
            import matlab
            import matlab.engine
        except ImportError as exc:
            raise MatlabEngineError(
                "当前模型是 MATLAB .mat 文件，需要安装 MATLAB Engine for Python。"
                "请在 MATLAB 安装目录的 extern/engines/python 下执行安装，"
                "并确认当前虚拟环境可运行: python -c \"import matlab.engine\"。"
            ) from exc

        settings = get_settings()
        if ModelPredictor._matlab_engine is None:
            ModelPredictor._matlab_engine = self._get_matlab_engine(matlab.engine)

            engine = ModelPredictor._matlab_engine
            engine.addpath(str(settings.matlab_predict_function_path), nargout=0)
            engine.addpath(engine.genpath(str(settings.matlab_project_path)), nargout=0)

        engine = ModelPredictor._matlab_engine
        matrix = matlab.double(features.astype(float).values.tolist())
        try:
            raw_labels, raw_probabilities = engine.chiller_ultra_predict(
                str(self.model_path),
                matrix,
                nargout=2,
            )
        except Exception as exc:
            raise MatlabEngineError(f"MATLAB ultra 模型预测失败: {exc}") from exc

        labels_array = np.asarray(raw_labels, dtype=float).reshape(-1)
        predicted_labels = [str(int(value)) for value in labels_array]

        probabilities_array = np.asarray(raw_probabilities, dtype=float)
        if probabilities_array.ndim == 1:
            probabilities_array = probabilities_array.reshape(1, -1)

        confidences = [round(float(np.max(row)), 6) for row in probabilities_array]
        if len(confidences) != len(predicted_labels):
            confidences = [None] * len(predicted_labels)
        return predicted_labels, confidences

    def _get_matlab_expected_feature_count(self) -> int | None:
        try:
            from scipy.io import loadmat
        except ImportError:
            return None

        try:
            data = loadmat(self.model_path, squeeze_me=True, struct_as_record=False)
            config = data.get("config")
            value = getattr(getattr(config, "cnn", None), "numFeatures", None)
            if value is None:
                return None
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _get_matlab_engine(matlab_engine_module: Any) -> Any:
        settings = get_settings()
        mode = settings.matlab_engine_mode.lower()
        shared_name = settings.matlab_shared_engine_name.strip()
        shared_engines = tuple(matlab_engine_module.find_matlab())

        if mode not in {"auto", "start", "connect"}:
            raise MatlabEngineError("MATLAB_ENGINE_MODE 只能是 auto、start 或 connect。")

        if mode in {"auto", "connect"}:
            target = shared_name or (shared_engines[0] if shared_engines else "")
            if target:
                try:
                    return matlab_engine_module.connect_matlab(target)
                except Exception as exc:
                    if mode == "connect":
                        raise MatlabEngineError(
                            f"连接共享 MATLAB Engine 失败: {type(exc).__name__}({exc!r})。"
                            "请确认 MATLAB 中已执行 matlab.engine.shareEngine。"
                        ) from exc
            elif mode == "connect":
                raise MatlabEngineError(
                    "没有发现共享 MATLAB Engine。请先打开 MATLAB 并执行: matlab.engine.shareEngine"
                )

        try:
            return matlab_engine_module.start_matlab(settings.matlab_start_options)
        except Exception as exc:
            raise MatlabEngineError(
                f"启动 MATLAB Engine 失败: {type(exc).__name__}({exc!r})。"
                "可尝试手动打开 MATLAB 后执行: matlab.engine.shareEngine，"
                "再将 .env 设置为 MATLAB_ENGINE_MODE=connect。"
            ) from exc

    @staticmethod
    def _infer_severity(dominant_ratio: float, avg_confidence: float | None) -> str:
        if dominant_ratio >= 0.85 and (avg_confidence is None or avg_confidence >= 0.85):
            return "high"
        if dominant_ratio >= 0.6:
            return "medium"
        return "low"


def get_predictor() -> ModelPredictor:
    return ModelPredictor()
