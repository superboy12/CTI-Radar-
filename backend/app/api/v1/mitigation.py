"""
Mitigation API endpoints.
"""
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.mitigation_service import MitigationService

logger = get_logger(__name__)

# Note: We don't require specific roles for these endpoints because 
# they might be fetched automatically by routers/firewalls using a generic service account.
router = APIRouter(prefix="/mitigation", tags=["Mitigation"])

@router.get("/blocklist/hosts", response_class=Response)
async def get_hosts_blocklist(
    include_suspicious: bool = Query(False, description="Include domains marked as SUSPICIOUS"),
    db: AsyncSession = Depends(get_db),
    # Optional auth: current_user: User = Depends(get_current_user),
):
    """Get a blocklist in /etc/hosts format."""
    service = MitigationService(db)
    content = await service.generate_hosts_file(include_suspicious)
    return Response(content=content, media_type="text/plain")

@router.get("/blocklist/pihole", response_class=Response)
async def get_pihole_blocklist(
    include_suspicious: bool = Query(False, description="Include domains marked as SUSPICIOUS"),
    db: AsyncSession = Depends(get_db),
):
    """Get a blocklist for Pi-hole/AdGuard Home."""
    service = MitigationService(db)
    content = await service.generate_pihole_list(include_suspicious)
    return Response(content=content, media_type="text/plain")

@router.get("/blocklist/mikrotik", response_class=Response)
async def get_mikrotik_blocklist(
    include_suspicious: bool = Query(False, description="Include domains marked as SUSPICIOUS"),
    db: AsyncSession = Depends(get_db),
):
    """Get a blocklist in MikroTik RouterOS script format."""
    service = MitigationService(db)
    content = await service.generate_mikrotik_script(include_suspicious)
    return Response(content=content, media_type="text/plain")
