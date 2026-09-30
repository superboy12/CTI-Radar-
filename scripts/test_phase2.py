"""Quick integration test for Phase 2 API endpoints (DNS & Infrastructure)."""
import httpx
import time

base = "http://localhost:8000/api/v1"
test_domain_name = "google.com" # Reliable domain for testing DNS

# 1. Login as admin
print("=== 1. LOGIN ===")
r = httpx.post(f"{base}/auth/login", json={"username": "admin", "password": "Admin123!"})
print(f"Status: {r.status_code}")
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Check if domain exists or create it
print(f"\n=== 2. CREATE DOMAIN ({test_domain_name}) ===")
r = httpx.post(f"{base}/domains/analyze", json={"domain": test_domain_name, "source": "test"}, headers=headers)
if r.status_code == 409:
    print("Domain already exists, fetching its ID...")
    # Get domain ID by searching
    r = httpx.get(f"{base}/domains?search={test_domain_name}", headers=headers)
    domain_id = r.json()["items"][0]["id"]
    print(f"Found existing domain ID: {domain_id}")
else:
    print(f"Status: {r.status_code}")
    domain_id = r.json()["id"]
    print(f"Created domain ID: {domain_id}")

# 3. Resolve DNS
print(f"\n=== 3. RESOLVE DNS ===")
start_time = time.time()
r = httpx.post(f"{base}/domains/{domain_id}/dns/resolve", headers=headers)
duration = time.time() - start_time
print(f"Status: {r.status_code} (took {duration:.2f}s)")
if r.status_code == 200:
    data = r.json()
    print(f"Resolved records: {data['summary']['total_records']}")
    print(f"Found IPs: {len(data['summary']['ip_addresses'])} -> {', '.join(data['summary']['ip_addresses'][:3])}...")
    print(f"Found Nameservers: {len(data['summary']['nameservers'])} -> {', '.join(data['summary']['nameservers'][:3])}...")
else:
    print(f"Error: {r.text}")

# 4. Get stored DNS data
print("\n=== 4. GET STORED DNS DATA ===")
r = httpx.get(f"{base}/domains/{domain_id}/dns", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Stored IPs: {len(data['ip_addresses'])}")
    print(f"Stored Nameservers: {len(data['nameservers'])}")
else:
    print(f"Error: {r.text}")

# 5. Get Infrastructure profile
print("\n=== 5. GET INFRASTRUCTURE PROFILE ===")
r = httpx.get(f"{base}/domains/{domain_id}/infrastructure", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print("Infrastructure Summary:")
    print(f"  - Total IPs: {data['infrastructure_summary']['total_ips']}")
    print(f"  - Total NS: {data['infrastructure_summary']['total_nameservers']}")
    
    # Check IP details if available
    if data['ip_addresses']:
        ip = data['ip_addresses'][0]
        print(f"\nExample IP: {ip['address']} (Version: {ip['version']})")
        print(f"Shared with {ip['shared_count']} other domains")
        
        # Test IP Details endpoint
        print(f"\n=== 6. GET IP DETAILS ({ip['address']}) ===")
        r = httpx.get(f"{base}/infrastructure/ips/{ip['id']}", headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            ip_data = r.json()
            print(f"Domains hosted here: {ip_data['domain_count']}")
            for d in ip_data['domains']:
                print(f"  - {d['domain']} (First seen: {d['first_seen']})")
else:
    print(f"Error: {r.text}")

# 7. Get Graph Data
print("\n=== 7. GET GRAPH DATA ===")
r = httpx.get(f"{base}/infrastructure/graph", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print("Graph Summary:")
    print(f"  - Total Nodes: {data['summary']['total_nodes']}")
    print(f"  - Total Edges: {data['summary']['total_edges']}")
else:
    print(f"Error: {r.text}")

print("\n=== ALL PHASE 2 TESTS COMPLETED ===")
