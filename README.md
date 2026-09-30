# 🛡️ Cyber Threat Intelligence Platform

> **Deteksi, Analisis, dan Mitigasi Domain Perjudian Daring**  
> Research & Prototype — Kelompok 4 Mahasiswa

⚠️ **DISCLAIMER**: Platform ini adalah **sistem riset keamanan siber**. Bukan website perjudian dan bukan sistem untuk memfasilitasi perjudian. Machine learning classification represents an automated risk indication and does not constitute legal determination.

---

## 🎯 Tujuan

Platform Cyber Threat Intelligence untuk:
- **Mengidentifikasi** domain yang terindikasi berkaitan dengan perjudian daring
- **Menganalisis** infrastruktur domain (DNS, IP, Certificate)
- **Mengklasifikasi** domain menggunakan Machine Learning
- **Menampilkan** threat intelligence pada dashboard interaktif
- **Menyediakan** mekanisme mitigasi berupa DNS filtering

## 🏗️ Arsitektur

```
Data Collection → Domain Intelligence → DNS/IP/Cert Analysis
    → Website Feature Extraction → ML Classification
    → Threat Intelligence Database → Dashboard → DNS Filtering
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python FastAPI |
| Frontend | React + Vite |
| Database | PostgreSQL |
| ML | scikit-learn, pandas, numpy |
| Graph Viz | Cytoscape.js |
| Container | Docker Compose |

## 📁 Struktur Project

```
├── backend/          # FastAPI backend
│   └── app/
│       ├── api/      # REST endpoints
│       ├── core/     # Security, logging
│       ├── models/   # SQLAlchemy models
│       ├── schemas/  # Pydantic schemas
│       ├── services/ # Business logic
│       └── database/ # DB session, init
├── frontend/         # React frontend (Phase 6)
├── ml/               # ML pipeline
│   ├── datasets/     # Training data
│   ├── models/       # Saved models
│   └── pipeline/     # ML code
├── docker/           # Docker configs
├── scripts/          # Utility scripts
├── tests/            # Test suite
└── docs/             # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Node.js 18+ (for frontend, Phase 6)
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
cd docker
docker-compose up -d

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Option 2: Manual Setup

```bash
# 1. Create PostgreSQL database
createdb cti_db

# 2. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Configure environment
copy ..\.env.example .env
# Edit .env with your database credentials

# 4. Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. (Optional) Seed sample data
cd ..
python -m scripts.seed_data
```

### Environment Variables

Copy `.env.example` to `backend/.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://cti_user:cti_password@localhost:5432/cti_db` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Change in production! |
| `FIRST_ADMIN_USERNAME` | Initial admin username | `admin` |
| `FIRST_ADMIN_PASSWORD` | Initial admin password | Change in production! |

## 📡 API Endpoints (Phase 1)

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/login` | Login, get JWT |
| `POST` | `/api/v1/auth/refresh` | Refresh token |
| `GET` | `/api/v1/auth/me` | Current user |

### Domain Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/domains/analyze` | Submit domain |
| `POST` | `/api/v1/domains/bulk` | Bulk submit |
| `GET` | `/api/v1/domains` | List domains |
| `GET` | `/api/v1/domains/statistics` | Statistics |
| `GET` | `/api/v1/domains/{id}` | Domain detail |
| `PUT` | `/api/v1/domains/{id}` | Update domain |
| `DELETE` | `/api/v1/domains/{id}` | Delete (admin) |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

## 🔐 Role-Based Access

| Role | Permissions |
|------|------------|
| **ADMIN** | Full access, delete domains, manage blocklist |
| **RESEARCHER** | Create/update domains, run ML, experiments |
| **VIEWER** | Read-only access to all data |

First registered user is automatically assigned ADMIN role.

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx aiosqlite

# Run tests
cd tests
pytest -v
```

## 📋 Development Phases

- [x] **Phase 1**: Database + Backend + Domain Management + Auth
- [ ] **Phase 2**: DNS Intelligence
- [ ] **Phase 3**: Infrastructure Relationships
- [ ] **Phase 4**: Feature Extraction
- [ ] **Phase 5**: ML Pipeline
- [ ] **Phase 6**: Dashboard Frontend
- [ ] **Phase 7**: Threat Graph
- [ ] **Phase 8**: DNS Filtering
- [ ] **Phase 9**: Research Experiment Module
- [ ] **Phase 10**: Security Hardening + Testing

## 👥 Team Distribution

| Member | Responsibility |
|--------|---------------|
| **Anggota 1** | Network & DNS Intelligence |
| **Anggota 2** | Machine Learning Pipeline |
| **Anggota 3** | Backend & Database |
| **Anggota 4** | Frontend & Visualization |

## ⚖️ Ethics & Privacy

- ✅ Passive/public information only
- ✅ No aggressive scanning or exploitation
- ✅ No collection of personal data
- ✅ Research purposes only
- ✅ ML results are indications, not legal proof

## 📄 License

This project is for academic research purposes.
