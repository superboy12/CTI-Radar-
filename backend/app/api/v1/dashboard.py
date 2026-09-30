"""
Dashboard and Reporting API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.api.deps import require_role
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardStatsResponse, RecentActivityResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get high-level statistics for the dashboard."""
    service = DashboardService(db)
    return await service.get_stats()

@router.get("/recent", response_model=List[RecentActivityResponse])
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get recent domain analysis activity."""
    service = DashboardService(db)
    return await service.get_recent_activity(limit=limit)
