"""
Domain schemas for request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re


class DomainAnalyzeRequest(BaseModel):
    """Request to submit a domain for analysis."""
    domain: str = Field(..., min_length=1, max_length=255)
    source: str = Field(default="manual", max_length=100)
    notes: Optional[str] = None

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v):
        v = v.strip().lower()
        # Remove protocol if present
        if "://" in v:
            v = v.split("://", 1)[1]
        # Remove trailing slashes and paths
        v = v.split("/")[0]
        # Basic domain validation
        pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid domain format: {v}")
        return v


class DomainResponse(BaseModel):
    """Domain information response."""
    id: UUID
    domain: str
    status: str
    source: str
    classification: Optional[str] = None
    confidence: Optional[float] = None
    risk_level: Optional[str] = None
    notes: Optional[str] = None
    first_seen: datetime
    last_analyzed: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DomainListResponse(BaseModel):
    """Simplified domain list item."""
    id: UUID
    domain: str
    status: str
    classification: Optional[str] = None
    confidence: Optional[float] = None
    risk_level: Optional[str] = None
    source: str
    first_seen: datetime
    last_analyzed: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DomainUpdateRequest(BaseModel):
    """Request to update domain classification."""
    classification: Optional[str] = Field(None, pattern=r"^(LEGITIMATE|SUSPICIOUS|GAMBLING_INDICATED)$")
    risk_level: Optional[str] = Field(None, pattern=r"^(LOW|MEDIUM|HIGH)$")
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(pending|analyzing|analyzed|error)$")


class DomainBulkRequest(BaseModel):
    """Request to submit multiple domains at once."""
    domains: List[str] = Field(..., min_length=1, max_length=100)
    source: str = Field(default="manual", max_length=100)

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, v):
        validated = []
        pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        for domain in v:
            d = domain.strip().lower()
            if "://" in d:
                d = d.split("://", 1)[1]
            d = d.split("/")[0]
            if not re.match(pattern, d):
                raise ValueError(f"Invalid domain format: {d}")
            validated.append(d)
        return validated


class DomainStatistics(BaseModel):
    """Dashboard statistics for domains."""
    total_domains: int = 0
    pending_domains: int = 0
    analyzed_domains: int = 0
    legitimate_domains: int = 0
    suspicious_domains: int = 0
    gambling_indicated_domains: int = 0
    unique_ips: int = 0
    unique_nameservers: int = 0
    total_alerts: int = 0
    unresolved_alerts: int = 0
    recent_analyses: int = 0
