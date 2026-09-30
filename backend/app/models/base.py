"""
SQLAlchemy declarative base and common mixins.

Provides cross-database type compatibility (PostgreSQL JSONB/UUID vs SQLite TEXT/CHAR).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, TypeDecorator, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings

# ── Cross-database type compatibility ────────────────────────────

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    from sqlalchemy import JSON as JSONB
    
    class UUID(TypeDecorator):
        """UUID type that stores as CHAR(36) in SQLite."""
        impl = String(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is not None:
                return str(value)
            return value

        def process_result_value(self, value, dialect):
            if value is not None:
                return uuid.UUID(value)
            return value
else:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

    class UUID(TypeDecorator):
        """UUID type using PostgreSQL native UUID."""
        impl = PG_UUID(as_uuid=True)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            return value

        def process_result_value(self, value, dialect):
            return value


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )


class UUIDMixin:
    """Mixin that adds a UUID primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
