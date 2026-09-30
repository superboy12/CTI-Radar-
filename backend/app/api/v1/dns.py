"""
DNS API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.api.deps import get_current_user, require_role, audit_log
from app.services.dns_service import DNSService
from app.services.domain_service import DomainService
from app.schemas.dns import DNSResolveResponse, DomainDNSResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/domains", tags=["DNS Intelligence"])

@router.post("/{domain_id}/dns/resolve", response_model=DNSResolveResponse)
async def resolve_domain_dns(
    domain_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("RESEARCHER")),
):
    """Resolve DNS for a domain and store the results."""
    # First get the domain to ensure it exists
    domain_service = DomainService(db)
    try:
        domain = await domain_service.get_domain_by_id(domain_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    dns_service = DNSService(db)
    try:
        results = await dns_service.resolve_and_store(domain_id, domain.domain)
        await audit_log(
            request, "resolve_dns", "domain", str(domain_id), None, current_user, db,
        )
        return results
    except Exception as e:
        logger.error("dns_resolve_error", domain_id=str(domain_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve DNS: {str(e)}"
        )

@router.get("/{domain_id}/dns", response_model=DomainDNSResponse)
async def get_domain_dns(
    domain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get stored DNS information for a domain."""
    dns_service = DNSService(db)
    results = await dns_service.get_domain_dns(domain_id)
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain not found or no DNS records stored: {domain_id}"
        )
    return results
