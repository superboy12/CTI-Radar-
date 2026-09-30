import asyncio
import sys
sys.path.append('d:/SS/backend')
from app.database.session import AsyncSessionLocal
from sqlalchemy import delete
from app.models.domain import Domain

async def run():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Domain).where(Domain.domain == 'caliskaniletisim.com'))
        await session.commit()
        print("Deleted")

asyncio.run(run())
