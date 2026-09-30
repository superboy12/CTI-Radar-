import httpx
import pandas as pd
import json
import re
from datetime import datetime
import os

OUTPUT_FILE = "d:/SS/ml/datasets/real_dataset.csv"
os.makedirs("d:/SS/ml/datasets", exist_ok=True)

def fetch_stevenblack_gambling():
    print("[1/3] 📥 Mengambil data OSINT dari repositori StevenBlack (Gambling)...")
    url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling/hosts"
    domains = []
    
    try:
        response = httpx.get(url, timeout=30.0)
        lines = response.text.split("\n")
        for line in lines:
            line = line.strip()
            # Ignore comments and localhosts
            if line.startswith("#") or line == "" or "localhost" in line or "broadcasthost" in line:
                continue
            
            parts = line.split()
            if len(parts) >= 2 and parts[0] in ["0.0.0.0", "127.0.0.1"]:
                domain = parts[1]
                # Filter out basic domains, keep only if it looks like standard domain
                if "." in domain:
                    domains.append({"domain": domain, "classification": "GAMBLING_INDICATED", "source": "stevenblack_hosts"})
                    
            if len(domains) >= 1500: # Limit to 1500 for training sample
                break
        print(f"      ✅ Berhasil mendapatkan {len(domains)} domain perjudian dari OSINT.")
        return domains
    except Exception as e:
        print(f"      ❌ Gagal mengambil OSINT: {e}")
        return []

import time

def fetch_crt_sh(keyword: str, limit: int = 100):
    print(f"[2/3] 🕵️ Mengintai log Sertifikat SSL (crt.sh) untuk keyword '{keyword}'...")
    url = f"https://crt.sh/?q=%25{keyword}%25&output=json"
    domains = []
    
    for attempt in range(3):
        try:
            response = httpx.get(url, timeout=45.0)
            
            if response.status_code in [502, 503, 504]:
                print(f"      ⚠️ Server crt.sh sibuk ({response.status_code}), mencoba ulang ({attempt+1}/3)...")
                time.sleep(3)
                continue
                
            data = response.json()
            
            # Deduplicate domains
            seen = set()
            for entry in data:
                domain = entry.get("name_value", "").lower()
                # Sometimes name_value contains multiple domains separated by newline
                for d in domain.split("\n"):
                    d = d.strip().replace("*.", "") # Remove wildcard
                    if d and d not in seen and "." in d:
                        seen.add(d)
                        domains.append({"domain": d, "classification": "GAMBLING_INDICATED", "source": f"crt_sh_{keyword}"})
                
                if len(domains) >= limit:
                    break
                    
            print(f"      ✅ Mendapatkan {len(domains)} domain baru dengan keyword '{keyword}'.")
            return domains
        except Exception as e:
            print(f"      ⚠️ Percobaan {attempt+1} gagal: {str(e)[:50]}...")
            time.sleep(3)
            
    print(f"      ❌ Gagal mengambil dari crt.sh setelah 3 percobaan.")
    return []

def fetch_legitimate_domains():
    print("[3/3] 🌐 Mengambil dataset domain normal (Top 1000 Websites)...")
    url = "https://raw.githubusercontent.com/b-mueller/top-1000-websites/master/top-1000-websites.csv"
    domains = []
    
    try:
        response = httpx.get(url, timeout=30.0)
        lines = response.text.split("\n")[1:] # Skip header
        for line in lines:
            if not line.strip(): continue
            parts = line.split(",")
            if len(parts) >= 2:
                domain = parts[1].strip().replace('"', '')
                domains.append({"domain": domain, "classification": "LEGITIMATE", "source": "top_1000_web"})
                
            if len(domains) >= 1000:
                break
                
        print(f"      ✅ Berhasil mendapatkan {len(domains)} domain normal.")
        return domains
    except Exception as e:
        print(f"      ❌ Gagal mengambil top 1000: {e}")
        return []

def fetch_hagezi_gambling():
    print("[1.5/3] 📥 Mengambil data OSINT tambahan (HaGeZi DNS Blocklist)...")
    url = "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/gambling.txt"
    domains = []
    
    try:
        response = httpx.get(url, timeout=30.0)
        lines = response.text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line or "." not in line:
                continue
            domains.append({"domain": line, "classification": "GAMBLING_INDICATED", "source": "hagezi_gambling"})
            if len(domains) >= 3000: # Ambil 3000 data
                break
        print(f"      ✅ Berhasil mendapatkan {len(domains)} domain dari HaGeZi.")
        return domains
    except Exception as e:
        print(f"      ❌ Gagal mengambil HaGeZi: {e}")
        return []

if __name__ == "__main__":
    print("="*60)
    print("🚀 MEMULAI PENCARIAN DATASET JUDOL KHUSUS INDONESIA")
    print("="*60)
    
    dataset = []
    
    # Baca dataset yang sudah ada
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_csv(OUTPUT_FILE)
            dataset = existing_df.to_dict('records')
            print(f"📦 Memuat {len(dataset)} data lama...")
        except Exception:
            pass

    # 1. OSINT Blocklists
    dataset.extend(fetch_stevenblack_gambling())
    dataset.extend(fetch_hagezi_gambling())
    
    # 2. SSL Logs (Variasi keyword hardcore Judol Indo)
    indo_keywords = [
        "slot", "gacor", "rtp", "zeus", "maxwin", "mahjong", 
        "scatter", "toto", "togel", "pragmatic", "pgsoft", "sbobet"
    ]
    
    for kw in indo_keywords:
        dataset.extend(fetch_crt_sh(kw, limit=300))
    
    # 3. Normal Domains (Kita coba dari Umbrella 1M)
    print("[3/3] 🌐 Mengambil dataset domain normal (Cisco Umbrella)...")
    try:
        # Menggunakan raw github Umbrella top 1m alternative
        url = "https://raw.githubusercontent.com/b-mueller/top-1000-websites/master/top-1000-websites.csv"
        response = httpx.get(url, timeout=30.0)
        lines = response.text.split("\n")[1:]
        added = 0
        for line in lines:
            if not line.strip(): continue
            parts = line.split(",")
            if len(parts) >= 2:
                domain = parts[1].strip().replace('"', '')
                dataset.append({"domain": domain, "classification": "LEGITIMATE", "source": "top_1000_web"})
                added += 1
            if added >= 1000: break
        print(f"      ✅ Berhasil mendapatkan {added} domain normal.")
    except Exception as e:
        print(f"      ❌ Gagal mengambil domain normal: {e}")
    
    # Simpan ke CSV
    if dataset:
        df = pd.DataFrame(dataset)
        # Hapus duplikat
        initial_len = len(df)
        df = df.drop_duplicates(subset=["domain"])
        print("="*60)
        print(f"🎉 SUKSES! Total Domain Unik: {len(df)} (Dihapus {initial_len - len(df)} duplikat)")
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"📁 Dataset disimpan di: {OUTPUT_FILE}")
        print("="*60)
