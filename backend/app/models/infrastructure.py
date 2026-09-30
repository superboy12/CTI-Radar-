"""
Infrastructure models - IP, Nameserver, Certificate and junction tables.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, UUID, JSONB


# ── IP Address ──────────────────────────────────────────────────────

class IP(Base, UUIDMixin, TimestampMixin):
    """An IP address associated with one or more domains."""
    __tablename__ = "ips"

    address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(4), nullable=False, default="IPv4")
    asn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asn_org: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    domain_ips = relationship("DomainIP", back_populates="ip", lazy="selectin")

    def __repr__(self):
        return f"<IP(address={self.address})>"


# ── Nameserver ──────────────────────────────────────────────────────

class Nameserver(Base, UUIDMixin, TimestampMixin):
    """A nameserver associated with one or more domains."""
    __tablename__ = "nameservers"

    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    domain_nameservers = relationship("DomainNameserver", back_populates="nameserver", lazy="selectin")

    def __repr__(self):
        return f"<Nameserver(hostname={self.hostname})>"


# ── Certificate ─────────────────────────────────────────────────────

class Certificate(Base, UUIDMixin, TimestampMixin):
    """A TLS/SSL certificate associated with domains."""
    __tablename__ = "certificates"

    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    issuer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    not_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fingerprint_sha256: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    san_domains: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    domain_certificates = relationship("DomainCertificate", back_populates="certificate", lazy="selectin")

    def __repr__(self):
        return f"<Certificate(subject={self.subject})>"


# ── Junction Tables ─────────────────────────────────────────────────

class DomainIP(Base, UUIDMixin):
    """Junction table linking domains to IP addresses."""
    __tablename__ = "domain_ips"

    domain_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("ips.id", ondelete="CASCADE"), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(10), nullable=False, default="A")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    domain = relationship("Domain", back_populates="domain_ips")
    ip = relationship("IP", back_populates="domain_ips")


class DomainNameserver(Base, UUIDMixin):
    """Junction table linking domains to nameservers."""
    __tablename__ = "domain_nameservers"

    domain_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True)
    nameserver_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("nameservers.id", ondelete="CASCADE"), nullable=False, index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    domain = relationship("Domain", back_populates="domain_nameservers")
    nameserver = relationship("Nameserver", back_populates="domain_nameservers")


class DomainCertificate(Base, UUIDMixin):
    """Junction table linking domains to certificates."""
    __tablename__ = "domain_certificates"

    domain_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True)
    certificate_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False, index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    domain = relationship("Domain", back_populates="domain_certificates")
    certificate = relationship("Certificate", back_populates="domain_certificates")
