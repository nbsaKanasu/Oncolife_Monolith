# OncoLife Monolith

A comprehensive healthcare platform for cancer patient symptom tracking and care team management.

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
├── packages/                 # Shared packages (future)
├── scripts/                  # Deployment & utility scripts
│   ├── aws/                 # AWS deployment scripts
│   └── db/                  # Database scripts
└── docker-compose.yml       # Local development orchestration
```

## ✨ Key Features

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

### Triage Levels
| Level | Description | Action |
|-------|-------------|--------|
| 🔴 `call_911` | Emergency | Immediate medical attention required |
| 🟡 `notify_care_team` | Alert | Care team notification needed |
| 🟢 `none` | Monitor | Continue observation |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith
```

2. **Start all services with Docker Compose**
```bash
docker-compose up -d
```

3. **Or run services individually**

**Patient API:**
```bash
cd apps/patient-platform/patient-api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8000
```

**Doctor API:**
```bash
cd apps/doctor-platform/doctor-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8001
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Patient API | http://localhost:8000 | REST + WebSocket API |
| Patient API Docs | http://localhost:8000/docs | Swagger UI |
| Doctor API | http://localhost:8001 | REST API |
| Doctor API Docs | http://localhost:8001/docs | Swagger UI |
| Patient Web | http://localhost:5173 | React frontend |
| Doctor Web | http://localhost:5174 | React frontend |

## 📚 API Documentation

### Patient API Endpoints (`/api/v1/`)

#### Authentication
```
POST /auth/signup                - Register new patient
POST /auth/login                 - Patient login
POST /auth/complete-new-password - Complete password setup
DELETE /auth/delete-patient      - Delete account
```

#### Symptom Checker
```
GET  /chat/session/today         - Get/create today's session
POST /chat/session/new           - Force new session
WS   /chat/ws/{chat_uuid}        - Real-time chat
POST /chat/{uuid}/feeling        - Update overall feeling
```

#### Chemotherapy
```
POST /chemo/log                  - Log chemo date
GET  /chemo/history              - Get all dates
```

#### Diary
```
GET  /diary/                     - Get all entries
GET  /diary/{year}/{month}       - Get by month
POST /diary/                     - Create entry
PATCH /diary/{uuid}              - Update entry
```

#### Summaries
```
GET /summaries/{year}/{month}    - Get by month
GET /summaries/{uuid}            - Get details
```

#### Profile
```
GET   /profile/                  - Get profile
PATCH /profile/config            - Update settings
```

### Doctor API Endpoints (`/api/v1/`)

```
POST /auth/login                 - Staff login
GET  /patients                   - List patients
GET  /patients/{uuid}            - Patient details
GET  /patients/{uuid}/alerts     - Patient alerts
GET  /staff/profile              - Staff profile
```

## 🔧 Configuration

### Environment Variables

Create `.env` files in each API directory:

**Patient API (.env):**
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=oncolife_admin
POSTGRES_PASSWORD=password
POSTGRES_PATIENT_DB=oncolife_patient
POSTGRES_DOCTOR_DB=oncolife_doctor

# AWS Cognito
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
COGNITO_USER_POOL_ID=us-west-2_xxx
COGNITO_CLIENT_ID=xxx
COGNITO_CLIENT_SECRET=xxx

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🚢 Deployment

### AWS Deployment

1. **Setup Infrastructure**
```bash
./scripts/aws/setup-infrastructure.sh
```

2. **Deploy Services**
```bash
# Deploy all services
./scripts/aws/deploy.sh all

# Or deploy individually
./scripts/aws/deploy.sh patient-api
./scripts/aws/deploy.sh doctor-api
```

See [Deployment Guide](apps/patient-platform/patient-api/docs/DEPLOYMENT.md) for detailed instructions.

## 🧪 Testing

```bash
# Run Patient API tests
cd apps/patient-platform/patient-api
pytest

# Run Doctor API tests
cd apps/doctor-platform/doctor-api
pytest
```

## 📁 Project Structure (Patient API)

```
patient-api/src/
├── main.py                      # Application entry point
├── core/                        # Infrastructure
│   ├── config.py               # Settings
│   ├── logging.py              # Logging setup
│   ├── exceptions.py           # Custom exceptions
│   └── middleware/             # Request handling
├── db/                          # Database layer
│   ├── base.py                 # SQLAlchemy base
│   ├── session.py              # Session management
│   ├── models/                 # SQLAlchemy models
│   └── repositories/           # Data access
├── services/                    # Business logic
│   ├── auth_service.py
│   ├── chat_service.py
│   ├── chemo_service.py
│   └── ...
├── api/                         # API layer
│   └── v1/
│       ├── router.py           # Main router
│       └── endpoints/          # Route handlers
└── routers/                     # Legacy + Symptom Engine
    └── chat/
        └── symptom_checker/
            ├── symptom_definitions.py  # 27 modules
            └── symptom_engine.py       # State machine
```

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Run tests
4. Submit pull request

## 📄 License

Proprietary - OncoLife Inc.

---

*Last Updated: January 2026*
