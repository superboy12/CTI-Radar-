"""
Machine Learning models - Dataset, MLModel, Experiment, MLPrediction.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, UUID, JSONB


class Dataset(Base, UUIDMixin, TimestampMixin):
    """A dataset used for training/evaluating ML models."""
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, default=0)
    class_distribution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    column_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    experiments = relationship("Experiment", back_populates="dataset", lazy="dynamic")

    def __repr__(self):
        return f"<Dataset(name={self.name}, version={self.version})>"


class MLModel(Base, UUIDMixin, TimestampMixin):
    """A trained ML model."""
    __tablename__ = "ml_models"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hyperparameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feature_columns: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    predictions = relationship("MLPrediction", back_populates="model", lazy="dynamic")
    experiments = relationship("Experiment", back_populates="model", lazy="dynamic")

    def __repr__(self):
        return f"<MLModel(name={self.name}, algorithm={self.algorithm})>"


class Experiment(Base, UUIDMixin, TimestampMixin):
    """A reproducible ML experiment."""
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confusion_matrix: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="experiments")
    model = relationship("MLModel", back_populates="experiments")

    def __repr__(self):
        return f"<Experiment(name={self.name}, status={self.status})>"


class MLPrediction(Base, UUIDMixin, TimestampMixin):
    """An ML prediction for a specific domain."""
    __tablename__ = "ml_predictions"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True
    )
    classification: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, default="LOW")
    feature_vector: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    probabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    domain = relationship("Domain", back_populates="predictions")
    model = relationship("MLModel", back_populates="predictions")

    def __repr__(self):
        return f"<MLPrediction(domain_id={self.domain_id}, class={self.classification})>"
