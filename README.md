# Brightloop Nexus — Intelligent Subscription & Revenue Management Platform

## Member 1: Subscription & Intelligence Engine

Brightloop Nexus is an enterprise-grade subscription lifecycle, pricing, and revenue retention platform built for modern SaaS and recurring billing models.

---

### Tech Stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, PyMySQL, Alembic
- **Database**: MySQL 8.0+ (InnoDB Engine, `DECIMAL(12,2)` monetary precision, UTF-8 `utf8mb4`)
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Axios, React Hook Form, Zod
- **Testing**: Pytest, FastAPI TestClient, Vitest

---

### Repository Structure
```
c:\odoo\
├── backend/
│   ├── alembic/              # Database migration scripts & environment
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/ # Route controllers
│   │   │       │   └── health.py
│   │   │       └── router.py  # Consolidated v1 router
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic BaseSettings & connection URI
│   │   │   ├── database.py    # SQLAlchemy 2.0 Engine & Session Local
│   │   │   └── security.py    # JWT, Argon2/Bcrypt password hashing
│   │   ├── models/            # Declarative SQLAlchemy models
│   │   ├── schemas/           # Pydantic v2 validation schemas
│   │   ├── services/          # Pure business logic and domain services
│   │   └── main.py            # FastAPI ASGI application entrypoint
│   ├── tests/                 # Pytest test suite
│   ├── alembic.ini            # Alembic configuration
│   ├── requirements.txt       # Python dependencies
│   ├── pytest.ini             # Pytest configuration
│   └── .env                   # Environment variables (DB credentials, secrets)
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios client with JWT interceptors
│   │   ├── components/        # Reusable enterprise UI components
│   │   ├── App.tsx            # Main App component & Phase 1 dashboard
│   │   ├── main.tsx           # React DOM root entrypoint
│   │   └── index.css          # Tailwind CSS styles
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.ts         # Vite bundler config with API proxy
│   ├── tailwind.config.js     # Enterprise Tailwind theme tokens
│   └── tsconfig.json          # TypeScript configuration
├── docs/
│   └── architecture/
│       └── DATABASE_DESIGN.md # Complete ER diagram & database explanations
└── README.md
```

---

### Phase 1 Quickstart (PowerShell)

#### 1. Backend Server
```powershell
cd c:\odoo\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```
- API Documentation: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

#### 2. Run Backend Tests
```powershell
cd c:\odoo\backend
.\.venv\Scripts\pytest -v
```

#### 3. Frontend Development Server
```powershell
cd c:\odoo\frontend
npm run dev
```
- Frontend UI: [http://localhost:5173](http://localhost:5173)

