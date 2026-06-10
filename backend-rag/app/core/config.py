from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Chiller Fault Diagnosis LangChain System"
    app_env: str = "dev"
    database_url: str = "sqlite:///./chiller_fault_rag.db"

    upload_dir: str = "uploads"
    report_dir: str = "reports"

    model_path: str = "saved_models/ict_sklearn_baseline.joblib"
    scaler_path: str = "saved_models/scaler.pkl"
    feature_columns_path: str = "saved_models/feature_columns.json"
    model_feature_columns_path: str = "saved_models/model_feature_columns.json"
    label_map_path: str = "saved_models/label_map.json"
    matlab_project_dir: str = "M1DCNN-集成"
    matlab_predict_function_dir: str = "app/matlab"
    matlab_engine_mode: str = "auto"
    matlab_shared_engine_name: str = ""
    matlab_start_options: str = "-nodesktop -nosplash"

    llm_provider: str = "openai_compatible"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.2
    openai_timeout: int = 60

    enable_llm: bool = Field(default=False)
    enable_rag: bool = Field(default=True)

    knowledge_base_dir: str = "knowledge_base"
    rag_vector_dir: str = "chroma_db"
    rag_collection_name: str = "chiller_sense_kb"
    rag_retriever: str = "hybrid"
    rag_top_k: int = 4
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return BASE_DIR / path

    @property
    def upload_path(self) -> Path:
        return self.resolve_path(self.upload_dir)

    @property
    def report_path(self) -> Path:
        return self.resolve_path(self.report_dir)

    @property
    def knowledge_base_path(self) -> Path:
        return self.resolve_path(self.knowledge_base_dir)

    @property
    def vector_path(self) -> Path:
        return self.resolve_path(self.rag_vector_dir)

    @property
    def model_file(self) -> Path:
        return self.resolve_path(self.model_path)

    @property
    def scaler_file(self) -> Path:
        return self.resolve_path(self.scaler_path)

    @property
    def feature_columns_file(self) -> Path:
        return self.resolve_path(self.feature_columns_path)

    @property
    def model_feature_columns_file(self) -> Path | None:
        if not self.model_feature_columns_path:
            return None
        return self.resolve_path(self.model_feature_columns_path)

    @property
    def label_map_file(self) -> Path:
        return self.resolve_path(self.label_map_path)

    @property
    def matlab_project_path(self) -> Path:
        return self.resolve_path(self.matlab_project_dir)

    @property
    def matlab_predict_function_path(self) -> Path:
        return self.resolve_path(self.matlab_predict_function_dir)

    @property
    def database_uri(self) -> str:
        if self.database_url.startswith("sqlite:///./"):
            db_name = self.database_url.replace("sqlite:///./", "", 1)
            return f"sqlite:///{BASE_DIR / db_name}"
        return self.database_url

    @property
    def llm_configured(self) -> bool:
        return bool(self.enable_llm and self.openai_api_key and self.openai_model)

    @property
    def embedding_configured(self) -> bool:
        return bool(self.openai_api_key and self.openai_embedding_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
