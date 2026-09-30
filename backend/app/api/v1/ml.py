"""
Machine Learning API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.models.ml import MLModel
from app.api.deps import require_role, audit_log
from app.services.ml_service import MLService
from app.schemas.ml import PredictionResponse, ModelResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.post("/predict/{domain_id}", response_model=PredictionResponse)
async def predict_domain(
    domain_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("RESEARCHER")),
):
    """Run ML prediction on a domain based on extracted features."""
    service = MLService(db)
    
    try:
        result = await service.predict(domain_id)
        
        await audit_log(
            request, "ml_predict", "domain", str(domain_id), None, current_user, db,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("ml_api_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

@router.get("/models", response_model=list[ModelResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """List all trained ML models in the system."""
    result = await db.execute(select(MLModel).order_by(MLModel.trained_at.desc()))
    models = result.scalars().all()
    
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "algorithm": m.algorithm,
            "version": m.version,
            "status": m.status,
            "trained_at": m.trained_at.isoformat() if m.trained_at else None
        }
        for m in models
    ]
