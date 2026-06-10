from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DiagnosisRecord(Base):
    __tablename__ = "diagnosis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    total_columns: Mapped[int] = mapped_column(Integer, nullable=False)
    has_label: Mapped[bool] = mapped_column(nullable=False, default=False)
    label_distribution_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    dominant_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dominant_fault_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dominant_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction_distribution_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    model_result_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    maintenance_suggestions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="diagnosis",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    diagnosis_id: Mapped[int] = mapped_column(ForeignKey("diagnosis_records.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    diagnosis: Mapped[DiagnosisRecord] = relationship(back_populates="chat_messages")

