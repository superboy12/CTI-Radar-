"""
Infrastructure API endpoints.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.api.deps import require_role
from app.services.infrastructure_service import InfrastructureService
from app.schemas.infrastructure import (
    DomainInfrastructureResponse,
    GraphDataResponse,
    SharedInfrastructureResponse,
    IPDetailResponse,
    NameserverDetailResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["Infrastructure Intelligence"])

@router.get("/domains/{domain_id}/infrastructure", response_model=DomainInfrastructureResponse)
async def get_domain_infrastructure(
    domain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get complete infrastructure profile for a domain including shared resources."""
    service = InfrastructureService(db)
    result = await service.get_domain_infrastructure(domain_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain not found: {domain_id}"
        )
    return result

@router.get("/domains/{domain_id}/related", response_model=SharedInfrastructureResponse)
async def get_related_domains(
    domain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Find other domains that share infrastructure with this domain."""
    service = InfrastructureService(db)
    result = await service.find_shared_infrastructure(domain_id)
    return result

@router.get("/infrastructure/graph", response_model=GraphDataResponse)
async def get_threat_graph(
    limit: int = Query(100, ge=10, le=500),
    node_types: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get infrastructure graph data for visualization (Cytoscape.js format)."""
    service = InfrastructureService(db)
    return await service.get_graph_data(limit=limit, node_types=node_types)

@router.get("/infrastructure/ips/{ip_id}", response_model=IPDetailResponse)
async def get_ip_details(
    ip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get detailed information about an IP address and all associated domains."""
    service = InfrastructureService(db)
    result = await service.get_ip_details(ip_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IP not found: {ip_id}"
        )
    return result

@router.get("/infrastructure/nameservers/{ns_id}", response_model=NameserverDetailResponse)
async def get_nameserver_details(
    ns_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get detailed information about a nameserver and all associated domains."""
    service = InfrastructureService(db)
    result = await service.get_nameserver_details(ns_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nameserver not found: {ns_id}"
        )
    return result
