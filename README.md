# Brightloop Nexus — Intelligent Subscription & Revenue Management Platform

## Enterprise Subscription & Revenue Platform
**Repository**: [https://github.com/aswinsparky/subscription-management-system.git](https://github.com/aswinsparky/subscription-management-system.git)  
**Database**: MySQL 8.0+ (InnoDB, UTF-8 `utf8mb4`, `DECIMAL(12,2)` Monetary Precision)  
**Architecture**: FastAPI Microservices + React 18 TypeScript Single-Page Application  

---

## 1. Executive Project Summary

Brightloop Nexus is an enterprise subscription lifecycle, dynamic pricing, automated renewal, and churn intelligence platform. An enterprise subscription lifecycle, dynamic pricing, automated recurring invoicing, and financial revenue intelligence platform unifying subscription operations, automated billing, payment reconciliation, and AI-driven telemetry.

---

## 2. Implemented Modules & Roadmap Status (12 / 12 Phases Complete)

| Phase | Module | Implementation Highlights | Status |
| :---: | :--- | :--- | :---: |
| **01** | **Setup & Database Connectivity** | FastAPI application setup, MySQL 8.0 connection pool with PyMySQL, health diagnostics (`/api/v1/health`), Vite React TS setup with Tailwind CSS. | **COMPLETED** |
| **02** | **Alembic & Authentication & RBAC** | 15+ SQLAlchemy models, Alembic migrations, JWT tokens, bcrypt hashing (>8 chars, upper/lower/special), roles (`ADMIN`, `STAFF`, `CUSTOMER`), single-use password resets. | **COMPLETED** |
| **03** | **Customer Management** | Customer CRUD, unique code generator (`CUST-YYYY-XXXX`), search across fields, status filters (`ACTIVE`, `SUSPENDED`, `ARCHIVED`), tenant isolation. | **COMPLETED** |
| **04** | **Product & Variant Management** | Multi-variant pricing: $\text{Final Price} = \text{Base Price} + \text{Variant Additional Price}$. Safe archive guard (`is_active = False`) if referenced in contracts. | **COMPLETED** |
| **05** | **Subscription Plan Management** | Interval rules (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`), date availability checks, policy rules (`pause_allowed`, `early_cancellation_allowed`, `renewal_allowed`). | **COMPLETED** |
| **06** | **Quotation Management** | Quote templates, line item pricing calculators, expiration date validation, idempotent one-way conversion to subscriptions (`409 Conflict` on replay). | **COMPLETED** |
| **07** | **Subscription Lifecycle Machine** | State machine: `DRAFT` $\rightarrow$ `CONFIRMED` $\rightarrow$ `ACTIVE` $\rightleftharpoons$ `PAUSED` $\rightarrow$ `CLOSED`/`CANCELLED`. Plan policy enforcement & append-only event auditing. | **COMPLETED** |
| **08** | **Renewal Scheduler & Billing Invoicing** | Automated renewal scheduler, horizon-based due detection, deterministic idempotency keys (`REN-SUB{id}-{start}-{end}`), automated recurring invoice generation. | **COMPLETED** |
| **09** | **Churn Radar & Risk Analytics** | Deterministic 0–100 heuristic churn risk scoring, risk classification (`LOW`, `MEDIUM`, `HIGH`), signal breakdown (pauses, auto-renew toggles, overdue bills), retention actions. | **COMPLETED** |
| **10** | **Subscription Time Machine** | Append-only audit store in `subscription_events`. Arbitrary historical state reconstruction as of timestamp $T$. Predictive What-If simulation sandbox without DB mutation. | **COMPLETED** |
| **11** | **Customer Self-Service Portal** | Strict tenant-isolated customer portal (`/api/v1/portal/*`). Customers view profile, manage active subscriptions, request pauses/cancellations, and accept pending quotations. | **COMPLETED** |
| **12** | **Hardening, Optimization & Docs** | Comprehensive Pytest suite (44 passed integration tests), clean Vite TypeScript production bundle, complete financial integration documentation. | **COMPLETED** |

---

## 3. Technology Stack & Design Decisions

### Backend Stack
- **Framework**: Python 3.12, FastAPI (async/await ready, OpenAPI auto-docs).
- **ORM**: SQLAlchemy 2.0 (Strict `Mapped[...]` and `mapped_column[...]` declarative types).
- **Validation**: Pydantic v2 (Strict typing, regex complexity validators).
- **Database Engine**: Local **MySQL Server 8.0.41** on Windows port 3306.
  - Driver: `PyMySQL` (`mysql+pymysql://root:aswinraj@localhost:3306/brightloop_nexus?charset=utf8mb4`).
  - Strict Monetary Precision: All currency columns use `DECIMAL(12, 2)` / `Numeric(12, 2)` to eliminate floating-point rounding errors.
  - Migration Tool: Alembic.

### Frontend Stack
- **Framework**: React 18, TypeScript, Vite.
- **Styling**: Tailwind CSS (Enterprise dark theme: slate-900 / indigo / emerald).
- **Icons**: Lucide React.
- **HTTP Client**: Axios with JWT request/response interceptors & auto-refresh token handling.

---

## 4. API Endpoints Directory

### Core & Diagnostics
- `GET /api/v1/health`: Live health status, MySQL connection check, engine version.

### Module 1: Auth & RBAC
- `POST /api/v1/auth/register`: Customer account self-registration.
- `POST /api/v1/auth/login`: Issue OAuth2 JWT access tokens.
- `GET /api/v1/auth/me`: Authenticated user session.
- `POST /api/v1/auth/staff`: Admin-only staff account creation.
- `POST /api/v1/auth/forgot-password` & `POST /api/v1/auth/reset-password`: Single-use reset tokens.

### Module 2: Customers
- `GET /api/v1/customers`: Searchable customer list with pagination and status filters.
- `POST /api/v1/customers`: Create customer with auto-code `CUST-YYYY-XXXX`.
- `GET /api/v1/customers/{id}` & `PUT /api/v1/customers/{id}`: Customer profile management.

### Module 3: Products & Variants
- `GET /api/v1/products`: Product catalog with nested active variants and computed final prices.
- `POST /api/v1/products`: Create catalog product (`SERVICE`, `SOFTWARE`, `HARDWARE`, `CONSUMABLE`).
- `POST /api/v1/products/{id}/variants`: Dynamic multi-variant builder.
- `DELETE /api/v1/products/{id}`: Referential integrity safe archive guard.

### Module 4: Subscription Plans
- `GET /api/v1/plans`: List active billing plans with intervals and lifecycle rules.
- `POST /api/v1/plans`: Define billing interval (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`) & policies.

### Module 5: Quotations
- `GET /api/v1/quotations`: Quotation listing and customer filtering.
- `POST /api/v1/quotations/`: Create quote from scratch with line pricing calculations.
- `POST /api/v1/quotations/from-template`: Generate quote from template.
- `POST /api/v1/quotations/{id}/convert`: Idempotent conversion to subscription (`409 Conflict` on duplicate).

### Module 6: Subscription Lifecycle & State Machine
- `GET /api/v1/subscriptions`: Subscription directory with status tabs.
- `POST /api/v1/subscriptions`: Create draft subscription directly.
- `POST /api/v1/subscriptions/{id}/confirm`: DRAFT $\rightarrow$ CONFIRMED.
- `POST /api/v1/subscriptions/{id}/activate`: CONFIRMED $\rightarrow$ ACTIVE (advances billing cycle).
- `POST /api/v1/subscriptions/{id}/pause`: ACTIVE $\rightarrow$ PAUSED (enforces plan `pause_allowed`).
- `POST /api/v1/subscriptions/{id}/resume`: PAUSED $\rightarrow$ ACTIVE.
- `POST /api/v1/subscriptions/{id}/cancel`: Terminal CANCELLED state (enforces `early_cancellation_allowed`).
- `POST /api/v1/subscriptions/{id}/close`: Terminal CLOSED state.
- `GET /api/v1/subscriptions/{id}/events`: Append-only audit history.

### Module 7: Automated Renewal Scheduler
- `GET /api/v1/renewals/due`: Subscriptions due within horizon days.
- `GET /api/v1/renewals/requests`: Audit ledger of billing requests.
- `POST /api/v1/renewals/trigger/{id}`: Idempotent renewal with automated invoice generation.
- `POST /api/v1/renewals/batch-run`: Automated batch renewal runner.
- `POST /api/v1/renewals/member2-webhook`: Asynchronous callback contract.

### Module 8: Churn Radar
- `GET /api/v1/churn/dashboard`: Aggregated churn risk metrics and at-risk accounts.
- `GET /api/v1/churn/customer/{id}`: Detailed risk vector breakdown & recommended playbook.
- `POST /api/v1/churn/customer/{id}/retention-action`: Log proactive retention intervention.

### Module 9: Subscription Time Machine
- `GET /api/v1/timemachine/subscriptions/{id}/timeline`: Chronological event audit with field diffs.
- `GET /api/v1/timemachine/subscriptions/{id}/as-of`: Historical state reconstruction as of timestamp $T$.
- `POST /api/v1/timemachine/subscriptions/{id}/simulate`: What-if predictive policy simulation without DB mutation.

### Module 10: Customer Self-Service Portal
- `GET /api/v1/portal/overview`: Customer-scoped dashboard.
- `GET /api/v1/portal/profile` & `PUT /api/v1/portal/profile`: Self-service profile updates.
- `POST /api/v1/portal/subscriptions/{id}/pause`: Customer pause request.
- `POST /api/v1/portal/subscriptions/{id}/resume`: Customer resume request.
- `POST /api/v1/portal/subscriptions/{id}/cancel`: Customer cancellation request.
- `POST /api/v1/portal/quotations/{id}/accept`: Convert customer proposal directly to subscription.

---

## 5. Automated Invoicing & Billing Contract

Full specification documented in [`docs/MEMBER2_INTEGRATION_CONTRACT.md`](docs/MEMBER2_INTEGRATION_CONTRACT.md).
- **Renewal Idempotency**: Guaranteed unique idempotency key: `REN-SUB{sub_id}-{start_date}-{end_date}`.
- **Tax & Discount Hooks**: Subscription engine passes line subtotals; financial engine applies verified tax breakdowns and discount codes.

---

## 6. How to Run & Verify

### Backend Setup & Test Suite
```powershell
# Activate Python 3.12 Virtual Environment
cd c:\odoo\backend
.\.venv\Scripts\activate

# Run database migrations
alembic upgrade head

# Run full integration test suite (44 tests)
pytest backend\tests -v

# Start FastAPI Development Server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup & Build
```powershell
cd c:\odoo\frontend

# Build production bundle
npm run build

# Start Vite Development Server
npm run dev
```
Navigate to `http://localhost:5173` in your browser. Default Admin credentials:
- **Email**: `admin@brightloop.io`
- **Password**: `Admin@123456!`
