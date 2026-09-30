"""Quick integration test for Phase 4 API endpoints (Machine Learning Pipeline)."""
import httpx
import time

base = "http://localhost:8000/api/v1"

# 1. Login as admin
print("=== 1. LOGIN ===")
r = httpx.post(f"{base}/auth/login", json={"username": "admin", "password": "Admin123!"})
if r.status_code != 200:
    print(f"Failed to login: {r.text}")
    exit(1)
print(f"Status: {r.status_code}")
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Get the test domain
print(f"\n=== 2. GET DOMAIN ===")
r = httpx.get(f"{base}/domains?search=google.com", headers=headers)
if r.status_code == 200 and r.json()["items"]:
    domain_id = r.json()["items"][0]["id"]
    print(f"Found domain ID: {domain_id}")
else:
    print("Could not find domain google.com. Creating it...")
    r = httpx.post(f"{base}/domains/analyze", json={"domain": "google.com", "source": "test"}, headers=headers)
    domain_id = r.json().get("id")
    print(f"Created domain ID: {domain_id}")

# 3. List ML Models
print(f"\n=== 3. LIST MODELS ===")
r = httpx.get(f"{base}/ml/models", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    models = r.json()
    print(f"Total models found: {len(models)}")
    if models:
        for m in models:
            print(f"  - {m['name']} (v{m['version']}) [Status: {m['status']}]")
else:
    print(f"Error: {r.text}")

# 4. Run ML Prediction
print(f"\n=== 4. RUN PREDICTION ===")
start_time = time.time()
r = httpx.post(f"{base}/ml/predict/{domain_id}", headers=headers)
duration = time.time() - start_time
print(f"Status: {r.status_code} (took {duration:.2f}s)")

if r.status_code == 200:
    data = r.json()
    print(f"Domain: {data['domain']}")
    print(f"Classification: {data['classification']}")
    print(f"Confidence: {data['confidence']:.2f}")
    print(f"Risk Level: {data['risk_level']}")
    
    print("\nFeatures Used:")
    for key, value in data['features_used'].items():
        print(f"  - {key}: {value}")
else:
    print(f"Error: {r.text}")

print("\n=== ALL PHASE 4 TESTS COMPLETED ===")
