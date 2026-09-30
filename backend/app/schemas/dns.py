"""
DNS intelligence schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class DNSRecordResponse(BaseModel):
    """A single DNS record."""
    type: str
    value: str
    ttl: Optional[int] = None
    priority: Optional[int] = None


class DNSSummary(BaseModel):
    """Summary of DNS resolution results."""
    total_records: int = 0
    ip_addresses: List[str] = []
    nameservers: List[str] = []
    mail_servers: List[dict] = []


class DNSResolveResponse(BaseModel):
    """Full DNS resolution result."""
    domain: str
    timestamp: str
    records: Dict[str, List[dict]]
    errors: Dict[str, str]
    summary: DNSSummary
    stored: Optional[Dict[str, Any]] = None


class IPResponse(BaseModel):
    """IP address information."""
    id: str
    address: str
    version: str
    asn: Optional[str] = None
    asn_org: Optional[str] = None
    country: Optional[str] = None
    record_type: str
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    is_active: bool = True


class NameserverResponse(BaseModel):
    """Nameserver information."""
    id: str
    hostname: str
    ip_address: Optional[str] = None
    provider: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    is_active: bool = True


class DomainDNSResponse(BaseModel):
    """Stored DNS information for a domain."""
    domain: str
    domain_id: str
    last_analyzed: Optional[str] = None
    ip_addresses: List[IPResponse] = []
    nameservers: List[NameserverResponse] = []
