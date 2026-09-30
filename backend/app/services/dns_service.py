"""
DNS Intelligence Service - resolves DNS records for domains.

Uses dnspython for passive DNS resolution. No aggressive scanning.
All queries use standard public DNS resolution.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID

import dns.resolver
import dns.rdatatype
import dns.exception

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.config import settings
from app.models.domain import Domain
from app.models.infrastructure import IP, Nameserver, DomainIP, DomainNameserver

logger = get_logger(__name__)


class DNSService:
    """Service for DNS resolution and intelligence gathering."""

    # Record types to query
    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA"]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = settings.DNS_TIMEOUT
        self.resolver.lifetime = settings.DNS_TIMEOUT * 2
        # Use system default nameservers (or configure custom ones)
        # self.resolver.nameservers = ['8.8.8.8', '8.8.4.4']

    async def resolve_domain(self, domain_name: str) -> Dict[str, Any]:
        """
        Resolve all DNS records for a domain.
        Returns a dict with all record types and their values.
        """
        results = {
            "domain": domain_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "records": {},
            "errors": {},
            "summary": {
                "total_records": 0,
                "ip_addresses": [],
                "nameservers": [],
                "mail_servers": [],
            },
        }

        for rtype in self.RECORD_TYPES:
            try:
                records = await self._query_record(domain_name, rtype)
                if records:
                    results["records"][rtype] = records
                    results["summary"]["total_records"] += len(records)
            except dns.resolver.NXDOMAIN:
                results["errors"][rtype] = "Domain does not exist (NXDOMAIN)"
            except dns.resolver.NoAnswer:
                # No records of this type - this is normal
                pass
            except dns.resolver.NoNameservers:
                results["errors"][rtype] = "No nameservers available"
            except dns.exception.Timeout:
                results["errors"][rtype] = "DNS query timed out"
            except Exception as e:
                results["errors"][rtype] = str(e)

        # Extract summary data
        if "A" in results["records"]:
            results["summary"]["ip_addresses"].extend(
                [r["value"] for r in results["records"]["A"]]
            )
        if "AAAA" in results["records"]:
            results["summary"]["ip_addresses"].extend(
                [r["value"] for r in results["records"]["AAAA"]]
            )
        if "NS" in results["records"]:
            results["summary"]["nameservers"] = [
                r["value"] for r in results["records"]["NS"]
            ]
        if "MX" in results["records"]:
            results["summary"]["mail_servers"] = [
                {"priority": r["priority"], "host": r["value"]}
                for r in results["records"]["MX"]
            ]

        return results

    async def _query_record(
        self, domain_name: str, record_type: str
    ) -> Optional[List[Dict]]:
        """Query a specific DNS record type. Runs in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        try:
            answers = await loop.run_in_executor(
                None,
                lambda: self.resolver.resolve(domain_name, record_type),
            )
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
            raise
        except Exception:
            return None

        records = []
        for rdata in answers:
            record = {"type": record_type, "ttl": answers.rrset.ttl}

            if record_type == "MX":
                record["value"] = str(rdata.exchange).rstrip(".")
                record["priority"] = rdata.preference
            elif record_type == "SOA":
                record["value"] = str(rdata.mname).rstrip(".")
                record["mname"] = str(rdata.mname).rstrip(".")
                record["rname"] = str(rdata.rname).rstrip(".")
                record["serial"] = rdata.serial
                record["refresh"] = rdata.refresh
                record["retry"] = rdata.retry
                record["expire"] = rdata.expire
                record["minimum"] = rdata.minimum
            elif record_type == "TXT":
                record["value"] = " ".join(
                    s.decode("utf-8", errors="replace") if isinstance(s, bytes) else s
                    for s in rdata.strings
                )
            else:
                record["value"] = str(rdata).rstrip(".")

            records.append(record)

        return records if records else None

    async def resolve_and_store(self, domain_id: UUID, domain_name: str) -> Dict[str, Any]:
        """
        Resolve DNS for a domain and store results in the database.
        Creates/updates IP and Nameserver records and their relationships.
        """
        logger.info("dns_resolution_start", domain=domain_name)

        # Resolve DNS
        dns_results = await self.resolve_domain(domain_name)

        now = datetime.now(timezone.utc)

        # Store IP addresses (A and AAAA records)
        stored_ips = []
        for record_type in ["A", "AAAA"]:
            records = dns_results["records"].get(record_type, [])
            for record in records:
                ip_address = record["value"]
                ip_version = "IPv4" if record_type == "A" else "IPv6"

                # Find or create IP
                ip_obj = await self._get_or_create_ip(ip_address, ip_version)

                # Create domain-IP relationship
                await self._link_domain_ip(domain_id, ip_obj.id, record_type, now)

                stored_ips.append({
                    "id": str(ip_obj.id),
                    "address": ip_address,
                    "version": ip_version,
                    "record_type": record_type,
                })

        # Store Nameservers (NS records)
        stored_ns = []
        ns_records = dns_results["records"].get("NS", [])
        for record in ns_records:
            ns_hostname = record["value"]

            # Find or create Nameserver
            ns_obj = await self._get_or_create_nameserver(ns_hostname)

            # Create domain-nameserver relationship
            await self._link_domain_nameserver(domain_id, ns_obj.id, now)

            stored_ns.append({
                "id": str(ns_obj.id),
                "hostname": ns_hostname,
            })

        # Update domain last_analyzed
        result = await self.db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = result.scalar_one_or_none()
        if domain:
            domain.last_analyzed = now
            if domain.status == "pending":
                domain.status = "analyzed"

        await self.db.flush()

        dns_results["stored"] = {
            "ips": stored_ips,
            "nameservers": stored_ns,
        }

        logger.info(
            "dns_resolution_complete",
            domain=domain_name,
            ips=len(stored_ips),
            nameservers=len(stored_ns),
        )

        return dns_results

    async def _get_or_create_ip(self, address: str, version: str = "IPv4") -> IP:
        """Find an existing IP or create a new one."""
        result = await self.db.execute(
            select(IP).where(IP.address == address)
        )
        ip_obj = result.scalar_one_or_none()

        if not ip_obj:
            ip_obj = IP(address=address, version=version)
            self.db.add(ip_obj)
            await self.db.flush()
            await self.db.refresh(ip_obj)
            logger.info("ip_created", address=address)

        return ip_obj

    async def _get_or_create_nameserver(self, hostname: str) -> Nameserver:
        """Find an existing Nameserver or create a new one."""
        hostname = hostname.lower().rstrip(".")
        result = await self.db.execute(
            select(Nameserver).where(Nameserver.hostname == hostname)
        )
        ns_obj = result.scalar_one_or_none()

        if not ns_obj:
            ns_obj = Nameserver(hostname=hostname)
            self.db.add(ns_obj)
            await self.db.flush()
            await self.db.refresh(ns_obj)
            logger.info("nameserver_created", hostname=hostname)

        return ns_obj

    async def _link_domain_ip(
        self, domain_id: UUID, ip_id: UUID, record_type: str, timestamp: datetime
    ) -> None:
        """Create or update a domain-IP relationship."""
        result = await self.db.execute(
            select(DomainIP).where(
                DomainIP.domain_id == domain_id,
                DomainIP.ip_id == ip_id,
                DomainIP.record_type == record_type,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.last_seen = timestamp
            existing.is_active = True
        else:
            link = DomainIP(
                domain_id=domain_id,
                ip_id=ip_id,
                record_type=record_type,
                first_seen=timestamp,
                last_seen=timestamp,
                is_active=True,
            )
            self.db.add(link)

    async def _link_domain_nameserver(
        self, domain_id: UUID, nameserver_id: UUID, timestamp: datetime
    ) -> None:
        """Create or update a domain-nameserver relationship."""
        result = await self.db.execute(
            select(DomainNameserver).where(
                DomainNameserver.domain_id == domain_id,
                DomainNameserver.nameserver_id == nameserver_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.last_seen = timestamp
            existing.is_active = True
        else:
            link = DomainNameserver(
                domain_id=domain_id,
                nameserver_id=nameserver_id,
                first_seen=timestamp,
                last_seen=timestamp,
                is_active=True,
            )
            self.db.add(link)

    async def get_domain_dns(self, domain_id: UUID) -> Dict[str, Any]:
        """Get stored DNS information for a domain."""
        # Get domain
        result = await self.db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = result.scalar_one_or_none()
        if not domain:
            return None

        # Get IP relationships
        ip_result = await self.db.execute(
            select(DomainIP, IP)
            .join(IP, DomainIP.ip_id == IP.id)
            .where(DomainIP.domain_id == domain_id)
            .order_by(DomainIP.first_seen.desc())
        )
        ip_records = []
        for domain_ip, ip in ip_result.all():
            ip_records.append({
                "id": str(ip.id),
                "address": ip.address,
                "version": ip.version,
                "asn": ip.asn,
                "asn_org": ip.asn_org,
                "country": ip.country,
                "record_type": domain_ip.record_type,
                "first_seen": domain_ip.first_seen.isoformat() if domain_ip.first_seen else None,
                "last_seen": domain_ip.last_seen.isoformat() if domain_ip.last_seen else None,
                "is_active": domain_ip.is_active,
            })

        # Get NS relationships
        ns_result = await self.db.execute(
            select(DomainNameserver, Nameserver)
            .join(Nameserver, DomainNameserver.nameserver_id == Nameserver.id)
            .where(DomainNameserver.domain_id == domain_id)
            .order_by(DomainNameserver.first_seen.desc())
        )
        ns_records = []
        for domain_ns, ns in ns_result.all():
            ns_records.append({
                "id": str(ns.id),
                "hostname": ns.hostname,
                "ip_address": ns.ip_address,
                "provider": ns.provider,
                "first_seen": domain_ns.first_seen.isoformat() if domain_ns.first_seen else None,
                "last_seen": domain_ns.last_seen.isoformat() if domain_ns.last_seen else None,
                "is_active": domain_ns.is_active,
            })

        return {
            "domain": domain.domain,
            "domain_id": str(domain.id),
            "last_analyzed": domain.last_analyzed.isoformat() if domain.last_analyzed else None,
            "ip_addresses": ip_records,
            "nameservers": ns_records,
        }
