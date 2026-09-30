"""
Mitigation and Blocklist Generation Service.

Generates DNS filtering lists from domains classified as gambling.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.domain import Domain

logger = get_logger(__name__)

class MitigationService:
    """Service to generate mitigation blocklists."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_blocked_domains(self, include_suspicious: bool = False) -> List[str]:
        """Fetch all domains that should be blocked based on ML classification."""
        classifications = ["GAMBLING_INDICATED"]
        if include_suspicious:
            classifications.append("SUSPICIOUS")
            
        result = await self.db.execute(
            select(Domain.domain)
            .where(
                Domain.classification.in_(classifications),
                # We could also filter by risk level here if needed
            )
            .order_by(Domain.domain)
        )
        return list(result.scalars().all())

    async def generate_hosts_file(self, include_suspicious: bool = False) -> str:
        """Generate a standard /etc/hosts format blocklist."""
        domains = await self.get_blocked_domains(include_suspicious)
        
        lines = [
            "# Cyber Threat Intelligence Platform",
            "# Blocklist: Gambling Domains",
            f"# Generated at: {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}",
            f"# Total entries: {len(domains)}",
            ""
        ]
        
        for domain in domains:
            # Route to a blackhole IP (0.0.0.0)
            lines.append(f"0.0.0.0 {domain}")
            # Also block the www subdomain just in case
            lines.append(f"0.0.0.0 www.{domain}")
            
        return "\n".join(lines)

    async def generate_pihole_list(self, include_suspicious: bool = False) -> str:
        """Generate a basic list for Pi-hole / AdGuard Home (one domain per line)."""
        domains = await self.get_blocked_domains(include_suspicious)
        
        lines = [
            "# Cyber Threat Intelligence Platform",
            "# Format: Pi-hole / AdGuard Home Adlist",
            ""
        ]
        for domain in domains:
            lines.append(domain)
        
        return "\n".join(lines)

    async def generate_mikrotik_script(self, include_suspicious: bool = False) -> str:
        """Generate a RouterOS script to add static DNS entries."""
        domains = await self.get_blocked_domains(include_suspicious)
        
        lines = [
            "# Cyber Threat Intelligence Platform",
            "# Format: MikroTik RouterOS Static DNS Script",
            "/ip dns static"
        ]
        for domain in domains:
            # Route to loopback
            lines.append(f"add name={domain} address=127.0.0.1 comment=\"CTI Blocked Gambling\"")
            
        return "\n".join(lines)
