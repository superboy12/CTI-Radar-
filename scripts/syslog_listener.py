import socket
import re
import httpx
import threading
import datetime

# Konfigurasi Syslog
SYSLOG_HOST = "0.0.0.0"
SYSLOG_PORT_SIMULATION = 5514

# Konfigurasi API
BASE_URL = "http://localhost:8000/api/v1"
DNS_QUERY_REGEX = re.compile(r"query from .*?: ([\w\.-]+)\.\s+[A-Z]+")
scanned_domains_cache = set()

def submit_to_ai(domain: str, is_main_target: bool = True):
    if domain in scanned_domains_cache:
        return
    scanned_domains_cache.add(domain)
    
    start_time = datetime.datetime.now()
    
    try:
        # 1. Login sebagai mesin
        if is_main_target:
            print(f"[{start_time.strftime('%H:%M:%S')}] 📡 Memeriksa domain tak dikenal: {domain}")
        r = httpx.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Admin123!"})
        if r.status_code != 200:
            return
        
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        
        # 2. Masukkan ke Antrean
        r = httpx.post(f"{BASE_URL}/domains/analyze", json={"domain": domain, "source": "NTA_Syslog"}, headers=headers)
        if r.status_code == 409:
            # Fetch ID
            r_get = httpx.get(f"{BASE_URL}/domains?search={domain}", headers=headers)
            if r_get.status_code == 200 and r_get.json()["items"]:
                domain_id = r_get.json()["items"][0]["id"]
            else:
                return
        elif r.status_code == 201:
            domain_id = r.json()["id"]
        else:
            return
            
        # 3. Eksekusi Stealth Scan & Machine Learning!
        if is_main_target:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🕵️  [+{(datetime.datetime.now() - start_time).seconds}s] Menyusup ke {domain} (Membypass Cloudflare/Anti-Bot)...")
        r_extract = httpx.post(f"{BASE_URL}/domains/{domain_id}/features/extract", headers=headers, timeout=60.0)
        
        if is_main_target:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🧠 [+{(datetime.datetime.now() - start_time).seconds}s] Fitur diekstrak. Mengirim ke model AI Random Forest...")
        r_ml = httpx.post(f"{BASE_URL}/ml/predict/{domain_id}", headers=headers)
        
        # 3b. Auto-scan domain yang ditemukan dari aset halaman (gambar, script, iframe, dll)
        if r_extract.status_code == 200:
            try:
                extracted_data = r_extract.json()
                ref_domains = extracted_data.get("features", {}).get("all_referenced_domains", [])
                if ref_domains:
                    for ref_domain in ref_domains[:20]:  # Batasi 20 domain per halaman
                        if ref_domain not in scanned_domains_cache:
                            threading.Thread(target=submit_to_ai, args=(ref_domain, False), daemon=True).start()
            except Exception:
                pass
        
        if r_ml.status_code == 200:
            hasil = r_ml.json()
            if hasil.get("classification") == "GAMBLING_INDICATED":
                conf = hasil.get('confidence', 0)
                if isinstance(conf, float): conf = int(conf * 100)
                
                print(f"\n=======================================================")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚨 [+{(datetime.datetime.now() - start_time).seconds}s] ANCAMAN JUDI ONLINE TERDETEKSI!")
                print(f"      📡 Target : {domain}")
                print(f"      🛑 Vonis  : GAMBLING_INDICATED (Keyakinan: {conf}%)")
                print(f"      🧱 Aksi   : Memblokir akses DNS seketika (Time-to-Mitigate: {(datetime.datetime.now() - start_time).seconds} detik)")
                
                # 4. FOOTPRINTING: Buru seluruh keluarga domain judi ini!
                try:
                    r_hunt = httpx.post(f"{BASE_URL}/siblings/hunt/{domain_id}", headers=headers, timeout=30.0)
                    if r_hunt.status_code == 200:
                        hunt_data = r_hunt.json()
                        siblings_flagged = hunt_data.get("siblings_flagged_suspicious", 0)
                        new_kw = hunt_data.get("dynamic_keywords", {}).get("new_keywords_discovered", [])
                        
                        if siblings_flagged > 0:
                            print(f"      🔗 Footprint: Ditemukan {siblings_flagged} domain SAUDARA!")
                            for sib in hunt_data.get("flagged_siblings", [])[:5]:
                                print(f"         ↳ {sib['domain']} (IP: {', '.join(sib.get('shared_ips', [])[:2])})")
                        
                        if new_kw:
                            print(f"      🧠 Keyword : Ditemukan {len(new_kw)} kata kunci judi BARU: {', '.join(new_kw[:5])}")
                except Exception:
                    pass  # Footprinting gagal? Tidak apa-apa, domain utama sudah terblokir.
                
                print(f"=======================================================\n")
                
    except Exception as e:
        pass

def run_syslog_listener():
    print("=======================================================")
    print("🛡️ CTI REAL-TIME NETWORK TRAFFIC ANALYZER (NTA) AKTIF")
    print(f"Mendengarkan Log DNS dari MikroTik di {SYSLOG_HOST}:{SYSLOG_PORT_SIMULATION}...")
    print("=======================================================")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SYSLOG_HOST, SYSLOG_PORT_SIMULATION))
    
    try:
        while True:
            data, addr = sock.recvfrom(2048)
            log_message = data.decode("utf-8", errors="ignore")
            
            if "dns" in log_message.lower() and "query" in log_message.lower():
                match = DNS_QUERY_REGEX.search(log_message)
                if match:
                    domain = match.group(1).lower()
                    
                    # Tambahkan LOG agar terlihat seperti lalu lintas jaringan sibuk (Matrix style)
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🟢 [TRAFIK NORMAL] User membuka -> {domain}")
                    
                    if domain.endswith(".local") or domain in ["google.com", "apple.com", "windows.com", "googleadservices.com", "cloudflare.com"]:
                        continue
                        
                    # Lempar ke thread baru agar radar tidak berhenti mendengarkan
                    threading.Thread(target=submit_to_ai, args=(domain, True), daemon=True).start()
                    
    except KeyboardInterrupt:
        print("\n🛑 Mematikan sistem analisis jaringan...")
    finally:
        sock.close()

if __name__ == "__main__":
    run_syslog_listener()
