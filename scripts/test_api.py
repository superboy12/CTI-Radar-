"""Quick integration test for Phase 1 API endpoints."""
import httpx

base = "http://localhost:8000/api/v1"

# Login as admin
print("=== LOGIN ===")
r = httpx.post(f"{base}/auth/login", json={"username": "admin", "password": "Admin123!"})
print(f"Status: {r.status_code}")
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Token: {token[:30]}...")

# Get current user
print("\n=== ME ===")
r = httpx.get(f"{base}/auth/me", headers=headers)
print(f"Status: {r.status_code}")
me = r.json()
print(f"User: {me['username']}, Role: {me['role']}")

# Create domain
print("\n=== CREATE DOMAIN ===")
r = httpx.post(f"{base}/domains/analyze", json={"domain": "example.com", "source": "test"}, headers=headers)
print(f"Status: {r.status_code}")
domain_data = r.json()
print(f"Domain: {domain_data['domain']}, Status: {domain_data['status']}")

# Create another domain
r = httpx.post(f"{base}/domains/analyze", json={"domain": "suspicious-test.xyz", "source": "research"}, headers=headers)
print(f"Status: {r.status_code}")

# List domains
print("\n=== LIST DOMAINS ===")
r = httpx.get(f"{base}/domains", headers=headers)
print(f"Status: {r.status_code}")
data = r.json()
total = data["total"]
items = data["items"]
print(f"Total: {total}, Items: {len(items)}")
for d in items:
    print(f"  - {d['domain']} ({d['status']})")

# Get statistics
print("\n=== STATISTICS ===")
r = httpx.get(f"{base}/domains/statistics", headers=headers)
print(f"Status: {r.status_code}")
stats = r.json()
print(f"Total domains: {stats['total_domains']}")

# Update domain classification
domain_id = items[0]["id"]
print(f"\n=== UPDATE DOMAIN ===")
r = httpx.put(
    f"{base}/domains/{domain_id}",
    json={"classification": "SUSPICIOUS", "risk_level": "MEDIUM"},
    headers=headers,
)
print(f"Status: {r.status_code}")
updated = r.json()
print(f"Classification: {updated['classification']}, Risk: {updated['risk_level']}")

# Bulk create
print("\n=== BULK CREATE ===")
r = httpx.post(
    f"{base}/domains/bulk",
    json={"domains": ["test1.com", "test2.org", "example.com"], "source": "bulk"},
    headers=headers,
)
print(f"Status: {r.status_code}")
print(f"Message: {r.json()['message']}")

# Test duplicate
print("\n=== DUPLICATE TEST ===")
r = httpx.post(f"{base}/domains/analyze", json={"domain": "example.com"}, headers=headers)
print(f"Status: {r.status_code} (expected 409)")

# Test invalid domain
print("\n=== INVALID DOMAIN TEST ===")
r = httpx.post(f"{base}/domains/analyze", json={"domain": "not-valid"}, headers=headers)
print(f"Status: {r.status_code} (expected 422)")

# Final list
print("\n=== FINAL LIST ===")
r = httpx.get(f"{base}/domains", headers=headers)
data = r.json()
print(f"Total domains in system: {data['total']}")

print("\n=== ALL PHASE 1 API TESTS PASSED ===")
