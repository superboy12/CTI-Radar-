"""Quick integration test for Phase 5 API endpoints (Dashboard & Reporting)."""
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

# 2. Get Dashboard Stats
print(f"\n=== 2. GET DASHBOARD STATS ===")
start_time = time.time()
r = httpx.get(f"{base}/dashboard/stats", headers=headers)
duration = time.time() - start_time
print(f"Status: {r.status_code} (took {duration:.2f}s)")

if r.status_code == 200:
    data = r.json()
    print(f"Total Domains: {data['total_domains']}")
    print(f"Analyzed Domains: {data['analyzed_domains']}")
    print(f"High Risk Domains: {data['high_risk_domains']}")
    
    print("\nRisk Distribution:")
    print(f"  - High: {data['risk_distribution']['high']}")
    print(f"  - Medium: {data['risk_distribution']['medium']}")
    print(f"  - Low: {data['risk_distribution']['low']}")
    
    print("\nClassification Distribution:")
    print(f"  - Gambling: {data['classification_distribution']['gambling_indicated']}")
    print(f"  - Legitimate: {data['classification_distribution']['legitimate']}")
    print(f"  - Suspicious: {data['classification_distribution']['suspicious']}")
    print(f"  - Pending: {data['classification_distribution']['pending']}")
else:
    print(f"Error: {r.text}")

# 3. Get Recent Activity
print(f"\n=== 3. GET RECENT ACTIVITY ===")
r = httpx.get(f"{base}/dashboard/recent?limit=5", headers=headers)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"Found {len(data)} recent items:")
    for item in data:
        class_str = item.get("classification") or "None"
        risk_str = item.get("risk_level") or "None"
        print(f"  - {item['domain']} [Status: {item['status']}, Class: {class_str}, Risk: {risk_str}]")
else:
    print(f"Error: {r.text}")

print("\n=== ALL PHASE 5 TESTS COMPLETED ===")
