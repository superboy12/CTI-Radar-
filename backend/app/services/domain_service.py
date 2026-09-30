"""
Domain service - business logic for domain management.
"""
import math
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, DuplicateError
from app.core.logging import get_logger
from app.models.domain import Domain
from app.models.infrastructure import IP, Nameserver, DomainIP
from app.models.alert import Alert
from app.schemas.domain import (
    DomainAnalyzeRequest,
    DomainResponse,
    DomainUpdateRequest,
    DomainStatistics,
)

logger = get_logger(__name__)


class DomainService:
    """Service for domain management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_domain(self, request: DomainAnalyzeRequest) -> Domain:
        """Create a new domain entry."""
        # Check for duplicate
        existing = await self.db.execute(
            select(Domain).where(Domain.domain == request.domain)
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("Domain", request.domain)

        domain = Domain(
            domain=request.domain,
            source=request.source,
            status="pending",
            notes=request.notes,
        )
        self.db.add(domain)
        await self.db.flush()
        await self.db.refresh(domain)

        logger.info("domain_created", domain=request.domain, source=request.source)
        return domain

    async def get_domain_by_id(self, domain_id: UUID) -> Domain:
        """Get a domain by its UUID."""
        result = await self.db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise NotFoundError("Domain", str(domain_id))
        return domain

    async def get_domain_by_name(self, domain_name: str) -> Domain:
        """Get a domain by its name."""
        result = await self.db.execute(
            select(Domain).where(Domain.domain == domain_name.lower().strip())
        )
        domain = result.scalar_one_or_none()
        if not domain:
            raise NotFoundError("Domain", domain_name)
        return domain

    async def list_domains(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """List domains with pagination and filtering."""
        query = select(Domain)
        count_query = select(func.count(Domain.id))

        # Apply filters
        if search:
            search_filter = Domain.domain.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if classification:
            query = query.where(Domain.classification == classification)
            count_query = count_query.where(Domain.classification == classification)

        if risk_level:
            query = query.where(Domain.risk_level == risk_level)
            count_query = count_query.where(Domain.risk_level == risk_level)

        if status:
            query = query.where(Domain.status == status)
            count_query = count_query.where(Domain.status == status)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Domain.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        domains = result.scalars().all()

        return {
            "items": domains,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    async def update_domain(self, domain_id: UUID, request: DomainUpdateRequest) -> Domain:
        """Update a domain's classification or status."""
        domain = await self.get_domain_by_id(domain_id)

        if request.classification is not None:
            domain.classification = request.classification
        if request.risk_level is not None:
            domain.risk_level = request.risk_level
        if request.notes is not None:
            domain.notes = request.notes
        if request.status is not None:
            domain.status = request.status

        domain.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(domain)

        logger.info("domain_updated", domain_id=str(domain_id))
        return domain

    async def delete_domain(self, domain_id: UUID) -> None:
        """Delete a domain and all associated data."""
        domain = await self.get_domain_by_id(domain_id)
        await self.db.delete(domain)
        logger.info("domain_deleted", domain_id=str(domain_id))

    async def bulk_create_domains(self, domains: List[str], source: str = "manual") -> dict:
        """Create multiple domain entries, skipping duplicates."""
        created = []
        skipped = []

        for domain_name in domains:
            existing = await self.db.execute(
                select(Domain).where(Domain.domain == domain_name)
            )
            if existing.scalar_one_or_none():
                skipped.append(domain_name)
                continue

            domain = Domain(domain=domain_name, source=source, status="pending")
            self.db.add(domain)
            created.append(domain_name)

        await self.db.flush()
        logger.info("bulk_domains_created", created=len(created), skipped=len(skipped))

        return {"created": created, "skipped": skipped}

    async def get_statistics(self) -> DomainStatistics:
        """Get dashboard statistics."""
        # Domain counts
        total = (await self.db.execute(select(func.count(Domain.id)))).scalar()
        pending = (await self.db.execute(
            select(func.count(Domain.id)).where(Domain.status == "pending")
        )).scalar()
        analyzed = (await self.db.execute(
            select(func.count(Domain.id)).where(Domain.status == "analyzed")
        )).scalar()
        legitimate = (await self.db.execute(
            select(func.count(Domain.id)).where(Domain.classification == "LEGITIMATE")
        )).scalar()
        suspicious = (await self.db.execute(
            select(func.count(Domain.id)).where(Domain.classification == "SUSPICIOUS")
        )).scalar()
        gambling = (await self.db.execute(
            select(func.count(Domain.id)).where(Domain.classification == "GAMBLING_INDICATED")
        )).scalar()

        # Infrastructure counts
        unique_ips = (await self.db.execute(select(func.count(IP.id)))).scalar()
        unique_ns = (await self.db.execute(select(func.count(Nameserver.id)))).scalar()

        # Alert counts
        total_alerts = (await self.db.execute(select(func.count(Alert.id)))).scalar()
        unresolved = (await self.db.execute(
            select(func.count(Alert.id)).where(Alert.is_resolved == False)
        )).scalar()

        return DomainStatistics(
            total_domains=total or 0,
            pending_domains=pending or 0,
            analyzed_domains=analyzed or 0,
            legitimate_domains=legitimate or 0,
            suspicious_domains=suspicious or 0,
            gambling_indicated_domains=gambling or 0,
            unique_ips=unique_ips or 0,
            unique_nameservers=unique_ns or 0,
            total_alerts=total_alerts or 0,
            unresolved_alerts=unresolved or 0,
        )
