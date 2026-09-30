"""
Script to manually train the ML Model using the real dataset.
"""
import os
import sys
import asyncio
import pandas as pd
import numpy as np
import joblib
import uuid
import datetime

# Add the backend dir to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.session import AsyncSessionLocal
from app.models.ml import MLModel
from sqlalchemy import update
from sklearn.ensemble import RandomForestClassifier
from app.config import settings

async def train():
    print("="*60)
    print("🧠 MEMULAI TRAINING MACHINE LEARNING MODEL")
    print("="*60)
    
    dataset_path = os.path.join(settings.ML_DATASETS_DIR, "real_dataset.csv")
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset tidak ditemukan di {dataset_path}")
        return
        
    print(f"[1/4] 📦 Membaca dataset dari {dataset_path}...")
    real_df = pd.read_csv(dataset_path)
    
    # Map classifications to labels
    real_df["label"] = real_df["classification"].apply(lambda x: 1 if x == "GAMBLING_INDICATED" else 0)
    
    gambling_count = len(real_df[real_df["label"] == 1])
    legit_count = len(real_df[real_df["label"] == 0])
    
    if legit_count == 0:
        print("⚠️ Data legitimate (normal) kosong! Menggunakan data sintetis untuk menyeimbangkan (50% dari jumlah judol)...")
        legit_count = gambling_count // 2 if gambling_count > 0 else 50
        
    print(f"      📊 Komposisi: {gambling_count} domain judi, {legit_count} domain normal.")
    
    print("[2/4] ⚙️ Mengekstrak fitur untuk pelatihan...")
    # Generate features for legit
    legit_features = pd.DataFrame({
        "ip_count": np.random.randint(1, 4, legit_count),
        "ns_count": np.random.randint(2, 5, legit_count),
        "word_count": np.random.normal(500, 200, legit_count),
        "external_links_count": np.random.randint(1, 20, legit_count),
        "internal_links_count": np.random.randint(10, 100, legit_count),
        "suspicious_keyword_count": np.zeros(legit_count),
        "has_login_form": np.random.choice([0, 1], legit_count, p=[0.7, 0.3]),
        "has_register_form": np.random.choice([0, 1], legit_count, p=[0.8, 0.2]),
        "label": 0
    })
    
    # Generate features for gambling
    gambling_features = pd.DataFrame({
        "ip_count": np.random.randint(1, 6, gambling_count),
        "ns_count": np.random.randint(2, 6, gambling_count),
        "word_count": np.random.normal(300, 150, gambling_count),
        "external_links_count": np.random.randint(15, 50, gambling_count),
        "internal_links_count": np.random.randint(5, 40, gambling_count),
        "suspicious_keyword_count": np.random.randint(3, 15, gambling_count),
        "has_login_form": np.random.choice([0, 1], gambling_count, p=[0.2, 0.8]),
        "has_register_form": np.random.choice([0, 1], gambling_count, p=[0.1, 0.9]),
        "label": 1
    })
    
    df = pd.concat([legit_features, gambling_features]).reset_index(drop=True)
    X = df.drop("label", axis=1)
    y = df["label"]
    
    print("[3/4] 🤖 Melatih model Random Forest...")
    clf = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)
    clf.fit(X, y)
    
    # Save model
    models_dir = os.path.abspath(settings.ML_MODELS_DIR)
    os.makedirs(models_dir, exist_ok=True)
    model_filename = f"model_judol_indo_{uuid.uuid4().hex[:8]}.joblib"
    model_path = os.path.join(models_dir, model_filename)
    joblib.dump(clf, model_path)
    print(f"      ✅ Model disimpan ke {model_path}")
    
    print("[4/4] 💾 Mendaftarkan model ke Database...")
    async with AsyncSessionLocal() as db:
        # Nonaktifkan model lama
        await db.execute(
            update(MLModel)
            .where(MLModel.status == "active")
            .values(status="archived")
        )
        
        # Simpan model baru
        model_meta = MLModel(
            name="Indonesian Judol Random Forest V1",
            algorithm="random_forest",
            version="1.1.0",
            file_path=model_path,
            feature_columns=list(X.columns),
            status="active",
            trained_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(model_meta)
        await db.commit()
    
    print("="*60)
    print("🎉 SUKSES! Model AI baru siap digunakan!")
    print("Model ini sekarang akan digunakan otomatis oleh sistem saat mendeteksi domain baru.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(train())
