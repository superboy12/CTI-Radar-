import asyncio
import os
import json
from uuid import uuid4
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.services.feature_service import FeatureExtractionService
from app.services.ml_service import MLService
from app.models.domain import Domain
from app.models.analysis import DomainAnalysis

async def test_domain():
    engine = create_async_engine("sqlite+aiosqlite:///./cti_dev.db")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as db:
        from sqlalchemy import select
        res = await db.execute(select(Domain).where(Domain.domain == "rokokbetkaca.com"))
        dom = res.scalar_one_or_none()
        if not dom:
            print("Tidak ditemukan di DB")
            return
        domain_id = dom.id
        
        print("Mengekstraksi fitur...")
        f_svc = FeatureExtractionService(db)
        res = await f_svc.extract_features(domain_id, "rokokbetkaca.com")
        
        print("Fitur yang didapat:")
        print(res)
        
        print("\nMenjalankan Prediksi ML...")
        ml_svc = MLService(db)
        ml_res = await ml_svc.predict(domain_id)
        
        print(f"Hasil ML: {ml_res}")

if __name__ == "__main__":
    asyncio.run(test_domain())
