"""
Analysis models - DomainAnalysis and ScanJob.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, UUID, JSONB


class DomainAnalysis(Base, UUIDMixin, TimestampMixin):
    """A single analysis snapshot of a domain."""
    __tablename__ = "domain_analyses"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("scan_jobs.id", ondelete="SET NULL"), nullable=True
    )
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False, default="full")
    dns_records: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    website_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    domain = relationship("Domain", back_populates="analyses")
    scan_job = relationship("ScanJob", back_populates="analyses")

    def __repr__(self):
        return f"<DomainAnalysis(domain_id={self.domain_id}, type={self.analysis_type})>"


class ScanJob(Base, UUIDMixin, TimestampMixin):
    """A batch scan job that can target multiple domains."""
    __tablename__ = "scan_jobs"

    job_type: Mapped[str] = mapped_column(String(30), nullable=False, default="analysis")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    targets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_targets: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    created_by_user = relationship("User", back_populates="scan_jobs")
    analyses = relationship("DomainAnalysis", back_populates="scan_job", lazy="dynamic")

    def __repr__(self):
        return f"<ScanJob(type={self.job_type}, status={self.status})>"
