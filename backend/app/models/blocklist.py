"""
Blocklist and DNS filtering models.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, UUID, JSONB


class BlocklistEntry(Base, UUIDMixin, TimestampMixin):
    """An entry in the blocklist/whitelist for DNS filtering."""
    __tablename__ = "blocklist_entries"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    list_type: Mapped[str] = mapped_column(String(20), nullable=False, default="blocklist")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_review")
    added_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    domain = relationship("Domain", back_populates="blocklist_entries")

    def __repr__(self):
        return f"<BlocklistEntry(domain_id={self.domain_id}, type={self.list_type})>"


class FilterPolicy(Base, UUIDMixin, TimestampMixin):
    """A DNS filtering policy with configurable rules."""
    __tablename__ = "filter_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self):
        return f"<FilterPolicy(name={self.name}, active={self.is_active})>"


class ThreatSource(Base, UUIDMixin, TimestampMixin):
    """An external threat intelligence source."""
    __tablename__ = "threat_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<ThreatSource(name={self.name}, type={self.source_type})>"
