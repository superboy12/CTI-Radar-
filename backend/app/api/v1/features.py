"""
Feature Extraction API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.models.analysis import DomainAnalysis
from app.api.deps import get_current_user, require_role, audit_log
from app.services.domain_service import DomainService
from app.services.feature_service import FeatureExtractionService
from app.schemas.feature import FeatureExtractionResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/domains", tags=["Feature Extraction"])

@router.post("/{domain_id}/features/extract", response_model=FeatureExtractionResponse)
async def extract_domain_features(
    domain_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("RESEARCHER")),
):
    """Trigger website feature extraction for a domain."""
    domain_service = DomainService(db)
    try:
        domain = await domain_service.get_domain_by_id(domain_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    feature_service = FeatureExtractionService(db)
    
    # We await this directly. For a highly scalable system, this would be a background task (Celery).
    # Since this is a research prototype, direct awaiting is acceptable for MVP.
    result = await feature_service.extract_features(domain_id, domain.domain)
    
    await audit_log(
        request, "extract_features", "domain", str(domain_id), None, current_user, db,
    )
    
    return {
        "domain_id": str(domain_id),
        "domain": domain.domain,
        "features": result["features"],
        "error": result["error"]
    }

@router.get("/{domain_id}/features", response_model=FeatureExtractionResponse)
async def get_domain_features(
    domain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """Get the latest extracted features for a domain."""
    domain_service = DomainService(db)
    try:
        domain = await domain_service.get_domain_by_id(domain_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

    # Get the latest feature extraction analysis
    result = await db.execute(
        select(DomainAnalysis)
        .where(
            DomainAnalysis.domain_id == domain_id,
            DomainAnalysis.analysis_type == "feature_extraction",
            DomainAnalysis.status == "completed"
        )
        .order_by(DomainAnalysis.created_at.desc())
        .limit(1)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis or not analysis.website_features:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No features have been extracted for this domain yet."
        )
        
    return {
        "domain_id": str(domain_id),
        "domain": domain.domain,
        "features": analysis.website_features,
        "error": analysis.error_message
    }
