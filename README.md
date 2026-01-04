# OncoLife Monolith

A comprehensive healthcare platform for cancer patient symptom tracking and care team management.

**Production Ready** ✅ | **HIPAA Compliant** 🔒 | **Rule-Based (No AI)** 🎯

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [**Step-by-Step Deployment**](docs/STEP_BY_STEP_DEPLOYMENT.md) | 🚀 **Complete AWS deployment walkthrough** |
| [Architecture Guide](docs/ARCHITECTURE.md) | System architecture, design patterns, code organization |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Getting started, development environment, code patterns |
| [Patient Onboarding](apps/patient-platform/patient-api/docs/ONBOARDING.md) | Fax/OCR → Cognito → Welcome flow |
| [Patient Education](apps/patient-platform/patient-api/docs/EDUCATION.md) | Post-session education delivery |
| [Patient API Features](apps/patient-platform/patient-api/docs/FEATURES.md) | Complete feature documentation (27 symptom modules) |
| [Patient API Deployment](apps/patient-platform/patient-api/docs/DEPLOYMENT.md) | AWS deployment details |
| [Doctor API Docs](apps/doctor-platform/doctor-api/docs/README.md) | Doctor API endpoints and usage |

---

## 🏗️ Architecture

```
OncoLife_Monolith/
├── apps/
│   ├── patient-platform/
│   │   ├── patient-api/     # FastAPI - Patient backend (Python)
│   │   ├── patient-server/  # Express - BFF layer (Node.js)
│   │   └── patient-web/     # React - Patient frontend
│   └── doctor-platform/
│       ├── doctor-api/      # FastAPI - Doctor backend (Python)
│       └── doctor-web/      # React - Doctor frontend
├── docs/                     # Architecture & developer guides
├── packages/                 # Shared packages (future)
├── scripts/                  # Deployment & utility scripts
│   ├── aws/                 # AWS deployment scripts
│   └── db/                  # Database scripts
└── docker-compose.yml       # Local development orchestration
```

### Backend Layered Architecture

```
┌─────────────────────────────────────────────┐
│              API Layer (api/v1/)            │
│  Routes, Request/Response handling          │
├─────────────────────────────────────────────┤
│            Service Layer (services/)         │
│  Business logic, orchestration              │
├─────────────────────────────────────────────┤
│          Repository Layer (db/repositories/) │
│  Data access, queries                       │
├─────────────────────────────────────────────┤
│            Database Layer (db/models/)       │
│  ORM models, schema                         │
└─────────────────────────────────────────────┘
```

### Frontend Architecture

```
┌─────────────────────────────────────────────┐
│        Components (pages/, components/)      │
├─────────────────────────────────────────────┤
│        Hooks (hooks/) & Context (context/)   │
├─────────────────────────────────────────────┤
│        API Layer (api/services/)             │
├─────────────────────────────────────────────┤
│        HTTP Client (api/client.ts)           │
└─────────────────────────────────────────────┘
```

---

## ✨ Key Features

### Patient Onboarding (Zero-Friction)
- **Fax → OCR**: Clinic sends referral fax → AWS Textract extracts patient data
- **Pre-Registration**: System creates Cognito account automatically
- **Welcome Email/SMS**: Patient receives credentials via AWS SES/SNS
- **Guided Setup**: Password reset → Acknowledgement → Terms → Reminders

### Patient Education (Rule-Based, Non-AI) 🆕
- **Post-Session Delivery**: Education delivered automatically after every symptom session
- **Clinician-Approved Content**: All education copied verbatim from approved sources
- **Care Team Handout**: Always included with every education response
- **Mandatory Disclaimer**: Cannot be removed, shown every time
- **Patient Summaries**: Deterministic template-based generation (no AI)
- **Education Tab**: Read-only library with search
- **Full Audit Trail**: Every delivery logged for HIPAA compliance

### Patient Platform
- **27 Symptom Modules**: Rule-based symptom checker with clinical triage logic
- **Real-time Chat**: WebSocket-based symptom assessment conversations
- **Chemotherapy Tracking**: Log and view treatment dates
- **Patient Diary**: Daily health journal entries
- **Conversation Summaries**: Review past symptom checker sessions

### Doctor Platform
- **Patient Management**: View and manage assigned patients
- **Alert Dashboard**: Monitor patient symptom alerts by triage level
- **Conversation Review**: Review patient symptom checker transcripts
- **Staff Management**: Manage clinic staff and permissions
- **Patient Summaries**: View immutable patient-generated summaries

### Triage Levels
| Level | Description | Action |
|-------|-------------|--------|
| 🔴 `call_911` | Emergency | Immediate medical attention required |
| 🟡 `notify_care_team` | Alert | Care team notification needed |
| 🟢 `none` | Monitor | Continue observation |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith

# Start all services
docker-compose up -d

# Verify services
curl http://localhost:8000/health  # Patient API
curl http://localhost:8001/health  # Doctor API
```

### Option 2: Manual Setup

See the [Developer Guide](docs/DEVELOPER_GUIDE.md) for detailed instructions.

```bash
# Patient API
cd apps/patient-platform/patient-api
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd src && uvicorn main:app --reload --port 8000

# Doctor API (in another terminal)
cd apps/doctor-platform/doctor-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd src && uvicorn main:app --reload --port 8001
```

---

## 🔗 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Patient API | http://localhost:8000 | REST + WebSocket API |
| Patient API Docs | http://localhost:8000/docs | Swagger UI |
| Doctor API | http://localhost:8001 | REST API |
| Doctor API Docs | http://localhost:8001/docs | Swagger UI |
| Patient Web | http://localhost:5173 | React frontend |
| Doctor Web | http://localhost:5174 | React frontend |

---

## 📡 API Endpoints

### Patient API (`/api/v1/`)

| Category | Endpoints |
|----------|-----------|
| **Onboarding** | `POST /onboarding/webhook/fax`, `GET /onboarding/status`, `POST /onboarding/complete/*` |
| **Education** 🆕 | `POST /education/deliver`, `GET /education/tab`, `POST /education/summary`, `GET /education/search` |
| **Auth** | `POST /auth/login`, `/signup`, `/logout` |
| **Chat** | `GET /chat/session/today`, `POST /chat/session/new`, `WS /chat/ws/{uuid}` |
| **Chemo** | `POST /chemo/log`, `GET /chemo/history` |
| **Diary** | `GET /diary/`, `POST /diary/`, `PATCH /diary/{uuid}` |
| **Summaries** | `GET /summaries/{year}/{month}` |
| **Profile** | `GET /profile/`, `PATCH /profile/config` |

### Doctor API (`/api/v1/`)

| Category | Endpoints |
|----------|-----------|
| **Auth** | `POST /auth/login`, `/signup`, `/logout` |
| **Patients** | `GET /patients`, `/patients/{uuid}`, `/patients/{uuid}/alerts` |
| **Staff** | `GET /staff`, `/staff/profile`, `/staff/{uuid}` |
| **Clinics** | `GET /clinics`, `POST /clinics` |

---

## 🔧 Configuration

Create `.env` files in each API directory:

```env
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=oncolife_admin
POSTGRES_PASSWORD=your_password
POSTGRES_PATIENT_DB=oncolife_patient
POSTGRES_DOCTOR_DB=oncolife_doctor

# AWS Core
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# AWS Cognito (Authentication)
COGNITO_USER_POOL_ID=us-west-2_xxx
COGNITO_CLIENT_ID=xxx
COGNITO_CLIENT_SECRET=xxx

# AWS S3 (Document Storage)
S3_REFERRAL_BUCKET=oncolife-referrals

# AWS SES (Email)
SES_SENDER_EMAIL=noreply@oncolife.com
SES_SENDER_NAME=OncoLife Care

# AWS SNS (SMS)
SNS_ENABLED=true

# Fax Webhook (Sinch/Twilio)
FAX_WEBHOOK_SECRET=your_webhook_secret

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 🚢 Deployment

### AWS Deployment

```bash
# Setup infrastructure
./scripts/aws/setup-infrastructure.sh

# Deploy all services
./scripts/aws/deploy.sh all

# Or deploy individually
./scripts/aws/deploy.sh patient-api
./scripts/aws/deploy.sh doctor-api
```

See [Deployment Guide](apps/patient-platform/patient-api/docs/DEPLOYMENT.md) for detailed AWS instructions.

### Education Module Setup (Required)

```bash
# 1. Create S3 bucket for education content
./scripts/create-education-bucket.sh

# 2. Upload clinician-approved PDFs
./scripts/upload-education-pdfs.sh

# 3. Seed database with education metadata
cd apps/patient-platform/patient-api
python scripts/seed_education.py
```

---

## ✅ Production Readiness

### Features Complete
| Feature | Status | Description |
|---------|--------|-------------|
| Patient Onboarding | ✅ | Fax → OCR → Cognito → Welcome |
| Symptom Checker | ✅ | 27 modules, rule-based triage |
| Patient Education | ✅ | Post-session delivery, no AI |
| Patient Summaries | ✅ | Template-based, immutable |
| Education Tab | ✅ | Read-only library with search |
| Doctor Portal | ✅ | Alerts, conversations, stats |

### Security & Compliance
| Requirement | Status | Implementation |
|-------------|--------|----------------|
| HIPAA Compliance | ✅ | KMS encryption, audit logs, access controls |
| Data Encryption | ✅ | At rest (RDS, S3) + in transit (TLS) |
| Authentication | ✅ | AWS Cognito with MFA support |
| Audit Trail | ✅ | CloudTrail, education delivery logs |
| Pre-signed URLs | ✅ | 30 min expiry, HTTPS only |

### No AI/LLM Dependencies
| Component | Approach |
|-----------|----------|
| Symptom Checker | Rule-based decision trees |
| Education Content | Clinician-approved, copied verbatim |
| Patient Summaries | Deterministic templates |
| Triage Logic | Clinician-defined rules |

### AWS Services Used
| Service | Purpose |
|---------|---------|
| ECS/Fargate | Container orchestration |
| RDS PostgreSQL | Database (encrypted) |
| Cognito | Authentication |
| S3 | Document storage (KMS) |
| Textract | Fax OCR |
| SES | Welcome emails |
| SNS | SMS notifications |
| Secrets Manager | Credentials |
| CloudWatch | Logging & monitoring |
| ALB | Load balancing (WAF) |

---

## 📁 Key Files

### Backend (Python/FastAPI)

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `core/config.py` | Environment configuration |
| `core/exceptions.py` | Custom exceptions |
| `services/*.py` | Business logic |
| `api/v1/endpoints/*.py` | API routes |
| `db/repositories/*.py` | Data access |

### Frontend (React/TypeScript)

| File | Purpose |
|------|---------|
| `api/client.ts` | Type-safe HTTP client |
| `api/services/*.ts` | API service modules |
| `hooks/*.ts` | Custom React hooks |
| `context/*.tsx` | State providers |
| `components/common/*.tsx` | Shared components |

---

## 🛠️ Development

### Code Patterns

- **Backend**: Repository Pattern, Service Layer, Dependency Injection
- **Frontend**: Custom Hooks, Context API, Error Boundaries

### Testing

```bash
# Backend
cd apps/patient-platform/patient-api
pytest

# Frontend
cd apps/patient-platform/patient-web
npm test
```

### Git Workflow

```bash
# Feature branch
git checkout -b feature/my-feature

# Commit with conventional commits
git commit -m "feat: add new symptom module"

# Push and create PR
git push origin feature/my-feature
```

---

## 📄 License

Proprietary - OncoLife Inc.

---

*Last Updated: January 2026*
