"""
Domain management API endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, DuplicateError
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.api.deps import get_current_user, require_role, audit_log
from app.services.domain_service import DomainService
from app.schemas.domain import (
    DomainAnalyzeRequest,
    DomainResponse,
    DomainListResponse,
    DomainUpdateRequest,
    DomainBulkRequest,
    DomainStatistics,
)
from app.schemas.common import MessageResponse, PaginatedResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.post("/analyze", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def analyze_domain(
    request: Request,
    body: DomainAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a domain for analysis. Creates a new domain entry if it doesn't exist."""
    service = DomainService(db)
    try:
        domain = await service.create_domain(body)
        await audit_log(
            request, "create", "domain", str(domain.id),
            {"domain": body.domain}, None, db,
        )
        return domain
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.post("/bulk", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def bulk_analyze_domains(
    request: Request,
    body: DomainBulkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("RESEARCHER")),
):
    """Submit multiple domains for analysis."""
    service = DomainService(db)
    result = await service.bulk_create_domains(body.domains, body.source)
    await audit_log(
        request, "bulk_create", "domain", None,
        {"count": len(body.domains), "created": len(result["created"])},
        current_user, db,
    )
    return MessageResponse(
        message=f"Created {len(result['created'])} domains, skipped {len(result['skipped'])} duplicates",
        details=result,
    )


@router.get("", response_model=PaginatedResponse[DomainListResponse])
async def list_domains(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=255),
    classification: Optional[str] = Query(None, pattern=r"^(LEGITIMATE|SUSPICIOUS|GAMBLING_INDICATED)$"),
    risk_level: Optional[str] = Query(None, pattern=r"^(LOW|MEDIUM|HIGH)$"),
    status_filter: Optional[str] = Query(None, alias="status", pattern=r"^(pending|analyzing|analyzed|error)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """List all tracked domains with pagination and filtering."""
    service = DomainService(db)
    result = await service.list_domains(
        page=page,
        page_size=page_size,
        search=search,
        classification=classification,
        risk_level=risk_level,
        status=status_filter,
    )
    return PaginatedResponse(
        items=[DomainListResponse.model_validate(d) for d in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/statistics", response_model=DomainStatistics)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get dashboard statistics."""
    service = DomainService(db)
    return await service.get_statistics()


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get detailed information about a specific domain."""
    service = DomainService(db)
    try:
        return await service.get_domain_by_id(domain_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.put("/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: UUID,
    body: DomainUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("RESEARCHER")),
):
    """Update a domain's classification or status."""
    service = DomainService(db)
    try:
        domain = await service.update_domain(domain_id, body)
        await audit_log(
            request, "update", "domain", str(domain_id),
            body.model_dump(exclude_none=True), current_user, db,
        )
        return domain
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/{domain_id}", response_model=MessageResponse)
async def delete_domain(
    domain_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    """Delete a domain and all associated data. Admin only."""
    service = DomainService(db)
    try:
        await service.delete_domain(domain_id)
        await audit_log(
            request, "delete", "domain", str(domain_id), None, current_user, db,
        )
        return MessageResponse(message=f"Domain {domain_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
