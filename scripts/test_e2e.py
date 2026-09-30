import httpx
import time
import sys

base_url = "http://localhost:8000/api/v1"

def run_e2e_test(target_domain: str):
    print(f"\n=======================================================")
    print(f"🚀 MEMULAI ANALISIS CYBER THREAT INTELLIGENCE")
    print(f"🎯 Target Domain: {target_domain}")
    print(f"=======================================================\n")
    
    # 1. Login Admin
    print("[1/5] 🔐 Login ke sistem sebagai Admin...")
    r = httpx.post(f"{base_url}/auth/login", json={"username": "admin", "password": "Admin123!"})
    if r.status_code != 200:
        print("❌ Gagal login. Pastikan server backend (FastAPI) sedang menyala.")
        sys.exit(1)
    
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("      ✅ Berhasil login.\n")

    # 2. Analisis Infrastruktur & Konten (Phase 2 & 3)
    print(f"[2/5] 🕵️ Mengumpulkan Intelijen untuk {target_domain} (DNS, IP, dan Scraping)...")
    start = time.time()
    r = httpx.post(f"{base_url}/domains/analyze", json={"domain": target_domain, "source": "manual_test"}, headers=headers)
    if r.status_code not in [201, 200, 409]:
        print(f"❌ Gagal menganalisis: {r.text}")
        sys.exit(1)
        
    domain_data = r.json()
    # Jika 409 (sudah ada), kita fetch manual
    if r.status_code == 409:
        print("      ⚠️ Domain sudah pernah dianalisis. Mengambil data dari database...")
        domain_id = domain_data["detail"].split("id: ")[-1].strip()
    else:
        domain_id = domain_data["id"]
        
    dur = time.time() - start
    print(f"      ✅ Domain didaftarkan dalam {dur:.2f} detik.")
    print(f"      🆔 Domain ID: {domain_id}\n")

    print("[2.5/5] 🤖 Menjalankan Playwright Headless Browser (Scanning)...")
    start = time.time()
    r = httpx.post(f"{base_url}/domains/{domain_id}/infrastructure/analyze", headers=headers, timeout=60.0)
    r2 = httpx.post(f"{base_url}/domains/{domain_id}/features/extract", headers=headers, timeout=60.0)
    if r2.status_code != 200:
        print(f"❌ Gagal ekstraksi fitur: {r2.text}")
    dur = time.time() - start
    print(f"      ✅ Scanning dan Ekstraksi selesai dalam {dur:.2f} detik.\n")

    # 3. Prediksi Machine Learning (Phase 4)
    print("[3/5] 🧠 Memasukkan data ke Machine Learning Pipeline...")
    start = time.time()
    r = httpx.post(f"{base_url}/ml/predict/{domain_id}", headers=headers)
    if r.status_code != 200:
        print(f"❌ Gagal memprediksi: {r.text}")
        sys.exit(1)
        
    prediction = r.json()
    dur = time.time() - start
    
    classification = prediction.get("classification", "UNKNOWN")
    risk_level = prediction.get("risk_level", "UNKNOWN")
    confidence = prediction.get("confidence", 0.0)
    
    print(f"      ✅ Analisis Machine Learning selesai dalam {dur:.2f} detik.")
    print(f"      📊 HASIL KLASIFIKASI: {classification}")
    print(f"      ⚠️ TINGKAT RISIKO: {risk_level}")
    print(f"      🎯 TINGKAT KEYAKINAN (CONFIDENCE): {confidence * 100:.1f}%\n")

    # 4. Cek Statistik Dashboard (Phase 5)
    print("[4/5] 📈 Memperbarui metrik Dashboard...")
    r = httpx.get(f"{base_url}/dashboard/stats", headers=headers)
    stats = r.json()
    print(f"      ✅ Total Domain di Sistem: {stats['total_domains']}")
    print(f"      ✅ Jumlah High Risk: {stats['high_risk_domains']}\n")

    # 5. Cek Mitigasi / Blocklist (Phase 6)
    print("[5/5] 🛡️ Memeriksa konfigurasi Mitigasi (Blocklist)...")
    r = httpx.get(f"{base_url}/mitigation/blocklist/hosts?include_suspicious=true")
    if target_domain in r.text:
        print(f"      🚨 {target_domain} BERHASIL DIEKSPOR KE BLOCKLIST!")
    else:
        print(f"      ✅ {target_domain} aman, tidak masuk ke blocklist.")
        
    print(f"\n=======================================================")
    print(f"✨ PROSES SELESAI ✨")
    print(f"=======================================================\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_e2e_test(sys.argv[1])
    else:
        print("Pilih domain untuk dites:")
        print("1. Domain Normal (google.com)")
        print("2. Uji Coba Domain Anda Sendiri")
        
        pilihan = input("Masukkan pilihan (1/2): ")
        if pilihan == "1":
            run_e2e_test("google.com")
        elif pilihan == "2":
            dom = input("Masukkan domain (tanpa http/https, misal: exampleslot.com): ")
            if dom.strip():
                run_e2e_test(dom.strip())
            else:
                print("Domain tidak valid.")
        else:
            print("Pilihan tidak dikenal.")
