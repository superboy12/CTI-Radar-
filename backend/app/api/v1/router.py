"""
API v1 router - aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.domains import router as domains_router
from app.api.v1.dns import router as dns_router
from app.api.v1.infrastructure import router as infrastructure_router
from app.api.v1.features import router as features_router
from app.api.v1.ml import router as ml_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.mitigation import router as mitigation_router
from app.api.v1.siblings import router as siblings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(domains_router)
api_router.include_router(dns_router)
api_router.include_router(infrastructure_router)
api_router.include_router(features_router)
api_router.include_router(ml_router)
api_router.include_router(dashboard_router)
api_router.include_router(mitigation_router)
api_router.include_router(siblings_router)

