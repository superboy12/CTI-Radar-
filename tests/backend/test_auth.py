"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_first_user_is_admin(client: AsyncClient, db_session):
    """First registered user should be assigned ADMIN role."""
    response = await client.post("/api/v1/auth/register", json={
        "username": "firstuser",
        "email": "first@test.com",
        "password": "FirstUser123!",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "firstuser"
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_second_user_is_viewer(client: AsyncClient, db_session):
    """Second registered user should be assigned VIEWER role."""
    # First user
    await client.post("/api/v1/auth/register", json={
        "username": "firstuser",
        "email": "first@test.com",
        "password": "FirstUser123!",
    })
    # Second user
    response = await client.post("/api/v1/auth/register", json={
        "username": "seconduser",
        "email": "second@test.com",
        "password": "SecondUser123!",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "VIEWER"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, db_session):
    """Should reject duplicate username."""
    await client.post("/api/v1/auth/register", json={
        "username": "dupuser",
        "email": "dup1@test.com",
        "password": "DupUser123!",
    })
    response = await client.post("/api/v1/auth/register", json={
        "username": "dupuser",
        "email": "dup2@test.com",
        "password": "DupUser123!",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient, db_session):
    """Should reject weak passwords."""
    response = await client.post("/api/v1/auth/register", json={
        "username": "weakuser",
        "email": "weak@test.com",
        "password": "weak",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session):
    """Should return JWT tokens on successful login."""
    # Register
    await client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@test.com",
        "password": "LoginUser123!",
    })
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "LoginUser123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session):
    """Should reject wrong password."""
    await client.post("/api/v1/auth/register", json={
        "username": "wrongpw",
        "email": "wrongpw@test.com",
        "password": "WrongPw123!",
    })
    response = await client.post("/api/v1/auth/login", json={
        "username": "wrongpw",
        "password": "InvalidPassword123!",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, admin_token: str):
    """Should return current user info with valid token."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient, db_session):
    """Should reject request without token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403
