"""
Tests for domain management endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_domain(client: AsyncClient, admin_token: str):
    """Should create a new domain entry."""
    response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "example.com", "source": "test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["domain"] == "example.com"
    assert data["status"] == "pending"
    assert data["source"] == "test"


@pytest.mark.asyncio
async def test_create_domain_with_protocol(client: AsyncClient, admin_token: str):
    """Should strip protocol from domain input."""
    response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "https://example.org/path/page"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["domain"] == "example.org"


@pytest.mark.asyncio
async def test_create_duplicate_domain(client: AsyncClient, admin_token: str):
    """Should reject duplicate domain."""
    await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "duplicate.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "duplicate.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_invalid_domain(client: AsyncClient, admin_token: str):
    """Should reject invalid domain format."""
    response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "not-a-valid-domain"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_domains(client: AsyncClient, admin_token: str):
    """Should list domains with pagination."""
    # Create test domains
    for i in range(5):
        await client.post(
            "/api/v1/domains/analyze",
            json={"domain": f"domain{i}.com"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    response = await client.get(
        "/api/v1/domains?page=1&page_size=3",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_get_domain_by_id(client: AsyncClient, admin_token: str):
    """Should return domain details by ID."""
    create_response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "detail-test.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    domain_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/domains/{domain_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["domain"] == "detail-test.com"


@pytest.mark.asyncio
async def test_update_domain_classification(client: AsyncClient, admin_token: str):
    """Should update domain classification."""
    create_response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "update-test.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    domain_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/domains/{domain_id}",
        json={"classification": "SUSPICIOUS", "risk_level": "MEDIUM"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "SUSPICIOUS"
    assert data["risk_level"] == "MEDIUM"


@pytest.mark.asyncio
async def test_delete_domain(client: AsyncClient, admin_token: str):
    """Should delete domain (admin only)."""
    create_response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "delete-test.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    domain_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/domains/{domain_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # Verify deleted
    response = await client.get(
        f"/api/v1/domains/{domain_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_create_domains(client: AsyncClient, admin_token: str):
    """Should create multiple domains, skipping duplicates."""
    # Create one domain first
    await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "existing.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.post(
        "/api/v1/domains/bulk",
        json={
            "domains": ["existing.com", "new1.com", "new2.com"],
            "source": "bulk-test",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "Created 2 domains" in data["message"]
    assert "skipped 1" in data["message"]


@pytest.mark.asyncio
async def test_get_statistics(client: AsyncClient, admin_token: str):
    """Should return domain statistics."""
    response = await client.get(
        "/api/v1/domains/statistics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_domains" in data
    assert "unique_ips" in data


@pytest.mark.asyncio
async def test_viewer_cannot_create_domain(client: AsyncClient, db_session):
    """Viewer should not be able to create domains."""
    # Register (first user = admin)
    await client.post("/api/v1/auth/register", json={
        "username": "adminuser",
        "email": "admin@test.com",
        "password": "AdminUser123!",
    })
    # Register viewer
    await client.post("/api/v1/auth/register", json={
        "username": "vieweruser",
        "email": "viewer@test.com",
        "password": "ViewerUser123!",
    })
    # Login as viewer
    login_response = await client.post("/api/v1/auth/login", json={
        "username": "vieweruser",
        "password": "ViewerUser123!",
    })
    viewer_token = login_response.json()["access_token"]

    # Try to create domain
    response = await client.post(
        "/api/v1/domains/analyze",
        json={"domain": "viewer-test.com"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403
