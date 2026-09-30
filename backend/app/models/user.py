"""
User model for authentication and authorization.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, UUID


class User(Base, UUIDMixin, TimestampMixin):
    """User account for the CTI platform."""
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="VIEWER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")
    scan_jobs = relationship("ScanJob", back_populates="created_by_user", lazy="dynamic")

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role})>"
