"""Quick integration test for Phase 3 API endpoints (Feature Extraction)."""
import httpx
import time

base = "http://localhost:8000/api/v1"
test_domain_name = "google.com" # Using google.com for a safe scrape test

# 1. Login as admin
print("=== 1. LOGIN ===")
r = httpx.post(f"{base}/auth/login", json={"username": "admin", "password": "Admin123!"})
if r.status_code != 200:
    print(f"Failed to login: {r.text}")
    exit(1)
print(f"Status: {r.status_code}")
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Check if domain exists or create it
print(f"\n=== 2. GET/CREATE DOMAIN ({test_domain_name}) ===")
r = httpx.post(f"{base}/domains/analyze", json={"domain": test_domain_name, "source": "test"}, headers=headers)
if r.status_code == 409:
    print("Domain already exists, fetching its ID...")
    r = httpx.get(f"{base}/domains?search={test_domain_name}", headers=headers)
    domain_id = r.json()["items"][0]["id"]
    print(f"Found existing domain ID: {domain_id}")
else:
    print(f"Status: {r.status_code}")
    domain_id = r.json()["id"]
    print(f"Created domain ID: {domain_id}")

# 3. Extract Features
print(f"\n=== 3. EXTRACT FEATURES ===")
start_time = time.time()
r = httpx.post(f"{base}/domains/{domain_id}/features/extract", headers=headers, timeout=15.0)
duration = time.time() - start_time
print(f"Status: {r.status_code} (took {duration:.2f}s)")
if r.status_code == 200:
    data = r.json()
    features = data["features"]
    print(f"Title: {features['title']}")
    print(f"Word Count: {features['word_count']}")
    print(f"External Links: {len(features['external_links'])}")
    print(f"Internal Links: {len(features['internal_links'])}")
    print(f"Server: {features['server']}")
    print(f"Status Code: {features['status_code']}")
    print(f"Suspicious Keywords Found: {features['suspicious_keywords_found']}")
else:
    print(f"Error: {r.text}")

# 4. Get Stored Features
print("\n=== 4. GET STORED FEATURES ===")
r = httpx.get(f"{base}/domains/{domain_id}/features", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Successfully retrieved stored features for {data['domain']}")
else:
    print(f"Error: {r.text}")

print("\n=== ALL PHASE 3 TESTS COMPLETED ===")
