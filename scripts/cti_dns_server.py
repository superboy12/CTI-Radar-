import socket
import threading
import httpx
import time
import datetime
from dnslib import DNSRecord, QTYPE, RR, A

# Konfigurasi
DNS_PORT = 53
DNS_HOST = "0.0.0.0" # Mendengarkan semua koneksi masuk (Hotspot WiFi)
UPSTREAM_DNS = "8.8.8.8"

API_BLOCKLIST_URL = "http://localhost:8000/api/v1/mitigation/blocklist/pihole"
SYSLOG_HOST = "127.0.0.1"
SYSLOG_PORT = 5514

# Cache Daftar Blokir
blocked_domains = set()

def update_blocklist():
    """Mengambil daftar blokir terbaru dari server AI setiap 5 detik"""
    global blocked_domains
    while True:
        try:
            response = httpx.get(API_BLOCKLIST_URL, timeout=3.0)
            if response.status_code == 200:
                lines = response.text.split("\n")
                new_blocklist = set()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        new_blocklist.add(line)
                blocked_domains = new_blocklist
        except Exception as e:
            pass # Abaikan jika server belum hidup
        time.sleep(5)

def send_to_radar(domain: str, client_ip: str):
    """Mengirim laporan ke Radar (syslog_listener.py) untuk di-scan AI"""
    # Abaikan domain wajar
    if domain.endswith(".arpa") or domain in ["google.com", "apple.com", "windows.com", "localhost"]:
        return
        
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        timestamp = datetime.datetime.now().strftime("%b %d %H:%M:%S")
        log_msg = f"<{13}> {timestamp} MikroTik dns,packet query from {client_ip}: {domain}. A"
        sock.sendto(log_msg.encode('utf-8'), (SYSLOG_HOST, SYSLOG_PORT))
        sock.close()
    except Exception:
        pass

def handle_dns_request(data, addr, sock):
    try:
        request = DNSRecord.parse(data)
        qname = str(request.q.qname).strip(".")
        client_ip = addr[0]
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔎 {client_ip} mencari: {qname}")
        
        # 1. Cek apakah domain ada di Blocklist AI?
        if qname in blocked_domains:
            print(f"🛡️ [BLOKIR AKTIF] {client_ip} dicegah mengakses {qname}!")
            # Jawab dengan IP kosong (Sinkhole)
            reply = request.reply()
            reply.add_answer(RR(qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
            sock.sendto(reply.pack(), addr)
            return

        # 2. Jika tidak diblokir, teruskan ke Google DNS (Beri akses)
        proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        proxy_sock.settimeout(3.0)
        proxy_sock.sendto(data, (UPSTREAM_DNS, 53))
        try:
            response_data, _ = proxy_sock.recvfrom(4096)
            
            # --- TRIK RAHASIA (MENCEGAH CACHE HP PENJUDI) ---
            # Kita modifikasi jawaban dari Google DNS, kita paksa TTL-nya menjadi 1 detik!
            # Sehingga HP penjudi TIDAK AKAN BISA menyimpan alamat ini di memori mereka.
            # Saat AI selesai memblokir dalam 30 detik, klik selanjutnya pasti akan gagal!
            try:
                parsed_resp = DNSRecord.parse(response_data)
                for rr in parsed_resp.rr:
                    rr.ttl = 1 # Paksa lupa dalam 1 detik!
                response_data = parsed_resp.pack()
            except:
                pass
                
            sock.sendto(response_data, addr)
        except socket.timeout:
            pass
        finally:
            proxy_sock.close()
            
        # 3. Diam-diam kirim domain ke Radar (AI akan nge-scan di belakang layar)
        # Jadi jika ternyata ini web judi, 10 detik lagi web ini akan masuk Blocklist!
        send_to_radar(qname, client_ip)
        
    except Exception as e:
        print(f"Error handling DNS: {e}")

def run_dns_server():
    print("=======================================================")
    print("🌐 CTI DNS SERVER (HOTSPOT DEMO MODE) AKTIF")
    print(f"Mendengarkan permintaan DNS HP di Port {DNS_PORT}...")
    print("=======================================================")
    
    # Jalankan thread pembaruan blocklist
    threading.Thread(target=update_blocklist, daemon=True).start()
    
    # Buka UDP Server Port 53
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((DNS_HOST, DNS_PORT))
    except PermissionError:
        print("❌ GAGAL: Tidak bisa mengikat Port 53. Port ini mungkin sedang dipakai oleh internet sharing Windows.")
        return
        
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            threading.Thread(target=handle_dns_request, args=(data, addr, sock), daemon=True).start()
        except ConnectionResetError:
            # Mengabaikan Windows socket bug (WinError 10054)
            pass
        except Exception as e:
            print(f"Error menerima paket: {e}")

if __name__ == "__main__":
    run_dns_server()
