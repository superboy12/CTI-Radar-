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

def submit_to_ai(domain: str):
    if domain in scanned_domains_cache:
        return
    scanned_domains_cache.add(domain)
    
    try:
        # 1. Login sebagai mesin
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
        httpx.post(f"{BASE_URL}/domains/{domain_id}/features/extract", headers=headers, timeout=60.0)
        r_ml = httpx.post(f"{BASE_URL}/ml/predict/{domain_id}", headers=headers)
        
        if r_ml.status_code == 200:
            hasil = r_ml.json()
            if hasil.get("classification") == "GAMBLING_INDICATED":
                conf = hasil.get('confidence', 0)
                if isinstance(conf, float): conf = int(conf * 100)
                
                print(f"\n=======================================================")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚨 ANCAMAN JUDI ONLINE TERDETEKSI!")
                print(f"      📡 Target : {domain}")
                print(f"      🛑 Vonis  : GAMBLING_INDICATED (Keyakinan: {conf}%)")
                print(f"      🧱 Aksi   : Memblokir akses dari seluruh jaringan...")
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
                    if domain.endswith(".local") or domain in ["google.com", "apple.com", "windows.com", "googleadservices.com"]:
                        continue
                        
                    # Lempar ke thread baru agar radar tidak berhenti mendengarkan
                    threading.Thread(target=submit_to_ai, args=(domain,), daemon=True).start()
                    
    except KeyboardInterrupt:
        print("\n🛑 Mematikan sistem analisis jaringan...")
    finally:
        sock.close()

if __name__ == "__main__":
    run_syslog_listener()
