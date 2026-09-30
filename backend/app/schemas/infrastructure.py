"""
Infrastructure intelligence schemas.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class SharedDomain(BaseModel):
    """Domain sharing some infrastructure."""
    id: str
    domain: str
    classification: Optional[str] = None

class InfraIPResponse(BaseModel):
    """IP address with shared domains information."""
    id: str
    address: str
    version: str
    asn: Optional[str] = None
    asn_org: Optional[str] = None
    country: Optional[str] = None
    record_type: str
    is_active: bool
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    shared_domains: List[SharedDomain] = []
    shared_count: int = 0

class InfraNameserverResponse(BaseModel):
    """Nameserver with shared domains information."""
    id: str
    hostname: str
    ip_address: Optional[str] = None
    provider: Optional[str] = None
    is_active: bool
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    shared_domains: List[SharedDomain] = []
    shared_count: int = 0

class InfraCertificateResponse(BaseModel):
    """Certificate information."""
    id: str
    serial_number: Optional[str] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    not_before: Optional[str] = None
    not_after: Optional[str] = None
    fingerprint_sha256: Optional[str] = None
    san_domains: Optional[Dict[str, Any]] = None
    is_active: bool

class InfraSummary(BaseModel):
    """Summary of infrastructure relationships."""
    total_ips: int = 0
    total_nameservers: int = 0
    total_certificates: int = 0
    shared_ip_domains: int = 0
    shared_ns_domains: int = 0

class DomainInfrastructureResponse(BaseModel):
    """Complete infrastructure profile for a domain."""
    domain: str
    domain_id: str
    classification: Optional[str] = None
    risk_level: Optional[str] = None
    ip_addresses: List[InfraIPResponse] = []
    nameservers: List[InfraNameserverResponse] = []
    certificates: List[InfraCertificateResponse] = []
    infrastructure_summary: InfraSummary

class GraphNodeData(BaseModel):
    """Data for a graph node."""
    id: str
    label: str
    type: str
    classification: Optional[str] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    asn: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None

class GraphNode(BaseModel):
    """Cytoscape.js compatible node."""
    data: GraphNodeData

class GraphEdgeData(BaseModel):
    """Data for a graph edge."""
    id: str
    source: str
    target: str
    type: str
    record_type: Optional[str] = None

class GraphEdge(BaseModel):
    """Cytoscape.js compatible edge."""
    data: GraphEdgeData

class GraphSummary(BaseModel):
    """Summary of graph data."""
    total_nodes: int
    total_edges: int
    domain_count: int
    ip_count: int
    ns_count: int

class GraphDataResponse(BaseModel):
    """Full graph data response."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    summary: GraphSummary

class RelatedDomain(BaseModel):
    """Domain related by shared infrastructure."""
    id: str
    domain: str
    classification: Optional[str] = None
    risk_level: Optional[str] = None
    shared_ips: List[str] = []
    shared_nameservers: List[str] = []
    relationship_strength: int = 0

class SharedInfrastructureResponse(BaseModel):
    """Response showing domains with shared infrastructure."""
    domain_id: str
    total_related: int
    related_domains: List[RelatedDomain]

class IPDetailDomain(BaseModel):
    """Domain associated with an IP detail view."""
    id: str
    domain: str
    classification: Optional[str] = None
    risk_level: Optional[str] = None
    record_type: str
    first_seen: Optional[str] = None
    is_active: bool

class IPDetailResponse(BaseModel):
    """Detailed view of an IP address."""
    id: str
    address: str
    version: str
    asn: Optional[str] = None
    asn_org: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    first_seen: Optional[str] = None
    domain_count: int
    domains: List[IPDetailDomain]

class NameserverDetailDomain(BaseModel):
    """Domain associated with a Nameserver detail view."""
    id: str
    domain: str
    classification: Optional[str] = None
    risk_level: Optional[str] = None
    first_seen: Optional[str] = None
    is_active: bool

class NameserverDetailResponse(BaseModel):
    """Detailed view of a Nameserver."""
    id: str
    hostname: str
    ip_address: Optional[str] = None
    provider: Optional[str] = None
    first_seen: Optional[str] = None
    domain_count: int
    domains: List[NameserverDetailDomain]
