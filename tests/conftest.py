"""
Test configuration and fixtures.
"""
import asyncio
import os
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Ensure the backend is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.models.base import Base
from app.database.session import get_db
from app.core.security import hash_password
from app.models.user import User

# Use SQLite for testing (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def admin_token(client: AsyncClient, db_session: AsyncSession):
    """Create an admin user and return an auth token."""
    # Register first user (auto-admin)
    response = await client.post("/api/v1/auth/register", json={
        "username": "testadmin",
        "email": "admin@test.com",
        "password": "TestAdmin123!",
    })
    assert response.status_code == 201

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "TestAdmin123!",
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def researcher_token(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Create a researcher user and return an auth token."""
    # Register second user (auto-viewer)
    response = await client.post("/api/v1/auth/register", json={
        "username": "testresearcher",
        "email": "researcher@test.com",
        "password": "TestResearcher123!",
    })
    assert response.status_code == 201

    # Update to researcher role via DB
    from sqlalchemy import select, update
    await db_session.execute(
        update(User).where(User.username == "testresearcher").values(role="RESEARCHER")
    )
    await db_session.commit()

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": "testresearcher",
        "password": "TestResearcher123!",
    })
    assert response.status_code == 200
    return response.json()["access_token"]
