import httpx
import os

os.makedirs(r"d:\SS\output\mitigation", exist_ok=True)
base = "http://localhost:8000/api/v1/mitigation/blocklist"

b_m = httpx.get(f"{base}/mikrotik").text
open(r"d:\SS\output\mitigation\mikrotik.rsc", "w", encoding="utf-8").write(b_m)

b_h = httpx.get(f"{base}/hosts").text
open(r"d:\SS\output\mitigation\hosts.txt", "w", encoding="utf-8").write(b_h)

b_p = httpx.get(f"{base}/pihole").text
open(r"d:\SS\output\mitigation\pihole.txt", "w", encoding="utf-8").write(b_p)

print("Export completed!")
