import sys
import os
import asyncio
import uuid
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.session import AsyncSessionLocal
import pandas as pd
import joblib
from sqlalchemy import select
from app.models.ml import MLModel
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def extract_features_sync(url: str):
    print(f"[1/3] 🤖 Membuka {url} dengan Stealth Headless Browser...")
    with sync_playwright() as p:
        # Menyamarkan identitas Chromium agar tidak terdeteksi sebagai robot
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Suntikkan Stealth Script!
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            
            content = page.content()
            text_content = page.evaluate("document.body.innerText")
            
            word_count = len(text_content.split())
            
            # Simple keyword matching
            keywords = ["slot", "gacor", "rtp", "deposit", "withdraw", "togel", "toto", "judi", "casino", "poker", "jackpot", "maxwin", "pragmatic", "zeus"]
            found_keywords = [kw for kw in keywords if kw.lower() in text_content.lower()]
            
            # Count forms
            forms = page.query_selector_all("form")
            has_login = False
            has_register = False
            for f in forms:
                html = f.inner_html().lower()
                if "login" in html or "masuk" in html or "username" in html:
                    has_login = True
                if "register" in html or "daftar" in html:
                    has_register = True
                    
            return {
                "has_features": 1,
                "ip_count": 1,
                "ns_count": 2,
                "word_count": word_count,
                "external_links_count": 5, # Mock
                "internal_links_count": 20, # Mock
                "suspicious_keyword_count": len(found_keywords),
                "has_login_form": 1 if has_login else 0,
                "has_register_form": 1 if has_register else 0,
                "found_keywords": found_keywords
            }
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            browser.close()

async def test_url(url: str):
    print("="*60)
    print(f"🚀 UJI COBA DEEP SCAN URL: {url}")
    print("="*60)
    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        features = await loop.run_in_executor(pool, extract_features_sync, url)
        
    if not features:
        print("❌ Gagal mengekstrak fitur.")
        return
        
    print(f"      ✅ Fitur berhasil diekstrak!")
    print(f"      - Jumlah Kata: {features['word_count']}")
    print(f"      - Form Daftar: {'Ya' if features['has_register_form'] else 'Tidak'}")
    print(f"      - Kata Kunci Judi Ditemukan ({features['suspicious_keyword_count']}): {', '.join(features['found_keywords'])}")
    
    print("\n[2/3] 🧠 Memuat Model AI dari Database...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MLModel).where(MLModel.status == "active").order_by(MLModel.trained_at.desc()).limit(1)
        )
        model_meta = result.scalar_one_or_none()
        
        if not model_meta:
            print("❌ Tidak ada model aktif.")
            return
            
        clf = joblib.load(model_meta.file_path)
        
        print("[3/3] 📊 Melakukan Prediksi...")
        feature_cols = model_meta.feature_columns
        
        # Ensure features match model
        X_input = pd.DataFrame([features])[feature_cols]
        
        prediction = clf.predict(X_input)[0]
        probabilities = clf.predict_proba(X_input)[0]
        confidence = float(max(probabilities))
        classification = "GAMBLING_INDICATED" if prediction == 1 else "LEGITIMATE"
        
        print("\n=======================================================")
        print(f"📊 HASIL KLASIFIKASI: {classification}")
        print(f"🎯 TINGKAT KEYAKINAN (CONFIDENCE): {confidence * 100:.1f}%")
        print("=======================================================")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://premanharum777.com/register/K5J815M8"
    asyncio.run(test_url(url))
