import socket
import time
import datetime

# Konfigurasi tujuan Syslog Listener kita
SYSLOG_HOST = "127.0.0.1"
SYSLOG_PORT = 5514 # Port simulasi yang digunakan oleh syslog_listener.py

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Daftar simulasi lalu-lintas jaringan dari HP pengguna
dns_queries = [
    "query from 192.168.1.15: facebook.com. A",
    "query from 192.168.1.15: google.com. A",
    "query from 192.168.1.15: rajaslot99.com. A", # Target judol 1
    "query from 192.168.1.20: instagram.com. A",
    "query from 192.168.1.20: premanharum777.com. A" # Target judol 2
]

print("📡 [SIMULATOR MIKROTIK] Mengirim log aktivitas jaringan...")

for query in dns_queries:
    timestamp = datetime.datetime.now().strftime("%b %d %H:%M:%S")
    # Format standar Syslog MikroTik
    log_message = f"<{13}> {timestamp} MikroTik dns,packet {query}"
    
    sock.sendto(log_message.encode("utf-8"), (SYSLOG_HOST, SYSLOG_PORT))
    print(f"Mengirim: {log_message}")
    
    # Tunggu 3 detik sebelum perangkat membuka web selanjutnya
    time.sleep(3)

print("✅ Selesai mengirim simulasi lalu-lintas jaringan.")
sock.close()
