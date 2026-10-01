"""
Sibling Detection & Footprinting API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.session import get_db
from app.models.user import User
from app.api.deps import require_role, audit_log
from app.services.sibling_service import SiblingDetectionService

logger = get_logger(__name__)

router = APIRouter(prefix="/siblings", tags=["Sibling Detection & Footprinting"])


@router.post("/hunt/{domain_id}")
async def hunt_siblings(
    domain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("RESEARCHER")),
):
    """
    Jalankan footprinting & sibling detection untuk sebuah domain.
    Secara otomatis:
    1. Resolve DNS (IP & NS) -> simpan ke database
    2. Cari domain lain yang berbagi IP/NS yang sama
    3. Tandai domain saudara sebagai SUSPICIOUS
    4. Temukan kata kunci judi baru (TF-IDF)
    """
    service = SiblingDetectionService(db)
    result = await service.footprint_and_hunt(domain_id)

    if result.get("error"):
        if result.get("skipped"):
            return result
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/keywords")
async def get_dynamic_keywords(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """
    Dapatkan daftar kata kunci gabungan (baseline + dinamis yang ditemukan AI).
    Kata kunci dinamis ditemukan menggunakan analisis TF-IDF dari
    konten situs-situs judi yang sudah terdeteksi.
    """
    service = SiblingDetectionService(db)
    return await service.get_dynamic_keywords()


@router.get("/report")
async def get_hunting_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("VIEWER")),
):
    """
    Laporan lengkap tentang hasil perburuan domain saudara,
    infrastruktur yang di-share, dan kata kunci yang ditemukan.
    """
    service = SiblingDetectionService(db)
    return await service.get_hunting_report()
