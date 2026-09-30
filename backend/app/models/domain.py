"""
Domain model - core entity of the CTI platform.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, UUID, JSONB


class Domain(Base, UUIDMixin, TimestampMixin):
    """A domain being tracked by the CTI platform."""
    __tablename__ = "domains"

    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    classification: Mapped[str | None] = mapped_column(String(30), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_analyzed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    domain_ips = relationship("DomainIP", back_populates="domain", lazy="selectin", cascade="all, delete-orphan")
    domain_nameservers = relationship("DomainNameserver", back_populates="domain", lazy="selectin", cascade="all, delete-orphan")
    domain_certificates = relationship("DomainCertificate", back_populates="domain", lazy="selectin", cascade="all, delete-orphan")
    analyses = relationship("DomainAnalysis", back_populates="domain", lazy="dynamic", cascade="all, delete-orphan")
    predictions = relationship("MLPrediction", back_populates="domain", lazy="dynamic", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="domain", lazy="dynamic", cascade="all, delete-orphan")
    blocklist_entries = relationship("BlocklistEntry", back_populates="domain", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Domain(domain={self.domain}, status={self.status})>"
