"""
Infrastructure Intelligence Service - analyzes relationships between domains, IPs, and nameservers.

Provides graph-like queries to find shared infrastructure.
"""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.domain import Domain
from app.models.infrastructure import (
    IP, Nameserver, Certificate,
    DomainIP, DomainNameserver, DomainCertificate,
)

logger = get_logger(__name__)


class InfrastructureService:
    """Service for infrastructure relationship analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_domain_infrastructure(self, domain_id: UUID) -> Dict[str, Any]:
        """Get complete infrastructure information for a domain."""
        # Get domain
        result = await self.db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = result.scalar_one_or_none()
        if not domain:
            return None

        # Get IPs
        ip_result = await self.db.execute(
            select(DomainIP, IP)
            .join(IP, DomainIP.ip_id == IP.id)
            .where(DomainIP.domain_id == domain_id)
        )
        ips = []
        for domain_ip, ip in ip_result.all():
            # Find other domains sharing this IP
            shared_result = await self.db.execute(
                select(Domain.domain, Domain.id, Domain.classification)
                .join(DomainIP, Domain.id == DomainIP.domain_id)
                .where(
                    DomainIP.ip_id == ip.id,
                    Domain.id != domain_id,
                )
            )
            shared_domains = [
                {"id": str(row[1]), "domain": row[0], "classification": row[2]}
                for row in shared_result.all()
            ]

            ips.append({
                "id": str(ip.id),
                "address": ip.address,
                "version": ip.version,
                "asn": ip.asn,
                "asn_org": ip.asn_org,
                "country": ip.country,
                "record_type": domain_ip.record_type,
                "is_active": domain_ip.is_active,
                "first_seen": domain_ip.first_seen.isoformat() if domain_ip.first_seen else None,
                "last_seen": domain_ip.last_seen.isoformat() if domain_ip.last_seen else None,
                "shared_domains": shared_domains,
                "shared_count": len(shared_domains),
            })

        # Get Nameservers
        ns_result = await self.db.execute(
            select(DomainNameserver, Nameserver)
            .join(Nameserver, DomainNameserver.nameserver_id == Nameserver.id)
            .where(DomainNameserver.domain_id == domain_id)
        )
        nameservers = []
        for domain_ns, ns in ns_result.all():
            # Find other domains using this nameserver
            shared_result = await self.db.execute(
                select(Domain.domain, Domain.id, Domain.classification)
                .join(DomainNameserver, Domain.id == DomainNameserver.domain_id)
                .where(
                    DomainNameserver.nameserver_id == ns.id,
                    Domain.id != domain_id,
                )
            )
            shared_domains = [
                {"id": str(row[1]), "domain": row[0], "classification": row[2]}
                for row in shared_result.all()
            ]

            nameservers.append({
                "id": str(ns.id),
                "hostname": ns.hostname,
                "ip_address": ns.ip_address,
                "provider": ns.provider,
                "is_active": domain_ns.is_active,
                "first_seen": domain_ns.first_seen.isoformat() if domain_ns.first_seen else None,
                "last_seen": domain_ns.last_seen.isoformat() if domain_ns.last_seen else None,
                "shared_domains": shared_domains,
                "shared_count": len(shared_domains),
            })

        # Get Certificates
        cert_result = await self.db.execute(
            select(DomainCertificate, Certificate)
            .join(Certificate, DomainCertificate.certificate_id == Certificate.id)
            .where(DomainCertificate.domain_id == domain_id)
        )
        certificates = []
        for domain_cert, cert in cert_result.all():
            certificates.append({
                "id": str(cert.id),
                "serial_number": cert.serial_number,
                "issuer": cert.issuer,
                "subject": cert.subject,
                "not_before": cert.not_before.isoformat() if cert.not_before else None,
                "not_after": cert.not_after.isoformat() if cert.not_after else None,
                "fingerprint_sha256": cert.fingerprint_sha256,
                "san_domains": cert.san_domains,
                "is_active": domain_cert.is_active,
            })

        return {
            "domain": domain.domain,
            "domain_id": str(domain.id),
            "classification": domain.classification,
            "risk_level": domain.risk_level,
            "ip_addresses": ips,
            "nameservers": nameservers,
            "certificates": certificates,
            "infrastructure_summary": {
                "total_ips": len(ips),
                "total_nameservers": len(nameservers),
                "total_certificates": len(certificates),
                "shared_ip_domains": sum(ip["shared_count"] for ip in ips),
                "shared_ns_domains": sum(ns["shared_count"] for ns in nameservers),
            },
        }

    async def get_graph_data(
        self,
        limit: int = 100,
        node_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build graph data for visualization.
        Returns nodes and edges in a Cytoscape.js-compatible format.
        """
        if node_types is None:
            node_types = ["domain", "ip", "nameserver"]

        nodes = []
        edges = []
        seen_nodes = set()

        # Get domains with their relationships
        domains_result = await self.db.execute(
            select(Domain)
            .order_by(Domain.created_at.desc())
            .limit(limit)
        )
        domains = domains_result.scalars().all()

        for domain in domains:
            if "domain" in node_types:
                node_id = f"domain-{domain.id}"
                if node_id not in seen_nodes:
                    nodes.append({
                        "data": {
                            "id": node_id,
                            "label": domain.domain,
                            "type": "domain",
                            "classification": domain.classification,
                            "risk_level": domain.risk_level,
                            "status": domain.status,
                        }
                    })
                    seen_nodes.add(node_id)

            # Get IP relationships
            if "ip" in node_types:
                ip_result = await self.db.execute(
                    select(DomainIP, IP)
                    .join(IP, DomainIP.ip_id == IP.id)
                    .where(DomainIP.domain_id == domain.id)
                )
                for domain_ip, ip in ip_result.all():
                    ip_node_id = f"ip-{ip.id}"
                    if ip_node_id not in seen_nodes:
                        nodes.append({
                            "data": {
                                "id": ip_node_id,
                                "label": ip.address,
                                "type": "ip",
                                "version": ip.version,
                                "asn": ip.asn,
                                "country": ip.country,
                            }
                        })
                        seen_nodes.add(ip_node_id)

                    edges.append({
                        "data": {
                            "id": f"edge-{domain.id}-{ip.id}",
                            "source": f"domain-{domain.id}",
                            "target": ip_node_id,
                            "type": "RESOLVES_TO",
                            "record_type": domain_ip.record_type,
                        }
                    })

            # Get NS relationships
            if "nameserver" in node_types:
                ns_result = await self.db.execute(
                    select(DomainNameserver, Nameserver)
                    .join(Nameserver, DomainNameserver.nameserver_id == Nameserver.id)
                    .where(DomainNameserver.domain_id == domain.id)
                )
                for domain_ns, ns in ns_result.all():
                    ns_node_id = f"ns-{ns.id}"
                    if ns_node_id not in seen_nodes:
                        nodes.append({
                            "data": {
                                "id": ns_node_id,
                                "label": ns.hostname,
                                "type": "nameserver",
                                "provider": ns.provider,
                            }
                        })
                        seen_nodes.add(ns_node_id)

                    edges.append({
                        "data": {
                            "id": f"edge-{domain.id}-ns-{ns.id}",
                            "source": f"domain-{domain.id}",
                            "target": ns_node_id,
                            "type": "USES_NAMESERVER",
                        }
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "domain_count": sum(1 for n in nodes if n["data"]["type"] == "domain"),
                "ip_count": sum(1 for n in nodes if n["data"]["type"] == "ip"),
                "ns_count": sum(1 for n in nodes if n["data"]["type"] == "nameserver"),
            },
        }

    async def find_shared_infrastructure(self, domain_id: UUID) -> Dict[str, Any]:
        """Find domains that share infrastructure with the given domain."""
        related_domains = {}

        # Find domains sharing IPs
        ip_result = await self.db.execute(
            select(DomainIP.ip_id).where(DomainIP.domain_id == domain_id)
        )
        ip_ids = [row[0] for row in ip_result.all()]

        if ip_ids:
            shared_ip_result = await self.db.execute(
                select(Domain, IP.address)
                .join(DomainIP, Domain.id == DomainIP.domain_id)
                .join(IP, DomainIP.ip_id == IP.id)
                .where(
                    DomainIP.ip_id.in_(ip_ids),
                    Domain.id != domain_id,
                )
            )
            for domain, ip_address in shared_ip_result.all():
                key = str(domain.id)
                if key not in related_domains:
                    related_domains[key] = {
                        "id": str(domain.id),
                        "domain": domain.domain,
                        "classification": domain.classification,
                        "risk_level": domain.risk_level,
                        "shared_ips": [],
                        "shared_nameservers": [],
                        "relationship_strength": 0,
                    }
                related_domains[key]["shared_ips"].append(ip_address)
                related_domains[key]["relationship_strength"] += 2  # IP sharing = strong link

        # Find domains sharing nameservers
        ns_result = await self.db.execute(
            select(DomainNameserver.nameserver_id)
            .where(DomainNameserver.domain_id == domain_id)
        )
        ns_ids = [row[0] for row in ns_result.all()]

        if ns_ids:
            shared_ns_result = await self.db.execute(
                select(Domain, Nameserver.hostname)
                .join(DomainNameserver, Domain.id == DomainNameserver.domain_id)
                .join(Nameserver, DomainNameserver.nameserver_id == Nameserver.id)
                .where(
                    DomainNameserver.nameserver_id.in_(ns_ids),
                    Domain.id != domain_id,
                )
            )
            for domain, ns_hostname in shared_ns_result.all():
                key = str(domain.id)
                if key not in related_domains:
                    related_domains[key] = {
                        "id": str(domain.id),
                        "domain": domain.domain,
                        "classification": domain.classification,
                        "risk_level": domain.risk_level,
                        "shared_ips": [],
                        "shared_nameservers": [],
                        "relationship_strength": 0,
                    }
                related_domains[key]["shared_nameservers"].append(ns_hostname)
                related_domains[key]["relationship_strength"] += 1  # NS sharing = weaker link

        # Sort by relationship strength
        related = sorted(
            related_domains.values(),
            key=lambda x: x["relationship_strength"],
            reverse=True,
        )

        return {
            "domain_id": str(domain_id),
            "related_domains": related,
            "total_related": len(related),
        }

    async def get_ip_details(self, ip_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed information about an IP address and all its domains."""
        result = await self.db.execute(select(IP).where(IP.id == ip_id))
        ip = result.scalar_one_or_none()
        if not ip:
            return None

        # Get all domains for this IP
        domain_result = await self.db.execute(
            select(Domain, DomainIP.record_type, DomainIP.first_seen, DomainIP.is_active)
            .join(DomainIP, Domain.id == DomainIP.domain_id)
            .where(DomainIP.ip_id == ip_id)
            .order_by(DomainIP.first_seen.desc())
        )
        domains = [
            {
                "id": str(d.id),
                "domain": d.domain,
                "classification": d.classification,
                "risk_level": d.risk_level,
                "record_type": record_type,
                "first_seen": first_seen.isoformat() if first_seen else None,
                "is_active": is_active,
            }
            for d, record_type, first_seen, is_active in domain_result.all()
        ]

        return {
            "id": str(ip.id),
            "address": ip.address,
            "version": ip.version,
            "asn": ip.asn,
            "asn_org": ip.asn_org,
            "country": ip.country,
            "city": ip.city,
            "first_seen": ip.first_seen.isoformat() if ip.first_seen else None,
            "domains": domains,
            "domain_count": len(domains),
        }

    async def get_nameserver_details(self, ns_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed information about a nameserver and all its domains."""
        result = await self.db.execute(select(Nameserver).where(Nameserver.id == ns_id))
        ns = result.scalar_one_or_none()
        if not ns:
            return None

        # Get all domains for this nameserver
        domain_result = await self.db.execute(
            select(Domain, DomainNameserver.first_seen, DomainNameserver.is_active)
            .join(DomainNameserver, Domain.id == DomainNameserver.domain_id)
            .where(DomainNameserver.nameserver_id == ns_id)
            .order_by(DomainNameserver.first_seen.desc())
        )
        domains = [
            {
                "id": str(d.id),
                "domain": d.domain,
                "classification": d.classification,
                "risk_level": d.risk_level,
                "first_seen": first_seen.isoformat() if first_seen else None,
                "is_active": is_active,
            }
            for d, first_seen, is_active in domain_result.all()
        ]

        return {
            "id": str(ns.id),
            "hostname": ns.hostname,
            "ip_address": ns.ip_address,
            "provider": ns.provider,
            "first_seen": ns.first_seen.isoformat() if ns.first_seen else None,
            "domains": domains,
            "domain_count": len(domains),
        }
