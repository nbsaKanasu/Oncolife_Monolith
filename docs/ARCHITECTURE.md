# OncoLife Architecture Guide

## Overview

OncoLife is a healthcare platform built with a modular monorepo architecture. This document provides a comprehensive overview of the system architecture, design patterns, and code organization.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │     Patient Web (React) │         │     Doctor Web (React)  │           │
│  │     Port: 5173          │         │     Port: 5174          │           │
│  └───────────┬─────────────┘         └───────────┬─────────────┘           │
│              │                                    │                         │
│              │ HTTP/WebSocket                     │ HTTP                    │
│              ▼                                    ▼                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                              API LAYER                                       │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │   Patient API (FastAPI) │         │   Doctor API (FastAPI)  │           │
│  │   Port: 8000            │         │   Port: 8001            │           │
│  │   /api/v1/*             │         │   /api/v1/*             │           │
│  └───────────┬─────────────┘         └───────────┬─────────────┘           │
│              │                                    │                         │
│              ▼                                    ▼                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                           DATABASE LAYER                                     │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │   Patient Database      │◄────────│   Doctor Database       │           │
│  │   (PostgreSQL)          │ read    │   (PostgreSQL)          │           │
│  │   - patient_info        │ only    │   - staff_profiles      │           │
│  │   - conversations       │         │   - all_clinics         │           │
│  │   - diary_entries       │         │   - staff_associations  │           │
│  │   - chemo_dates         │         │                         │           │
│  └─────────────────────────┘         └─────────────────────────┘           │
├─────────────────────────────────────────────────────────────────────────────┤
│                         EXTERNAL SERVICES                                    │
│  ┌─────────────────────────┐                                                │
│  │     AWS Cognito         │  Authentication & User Management              │
│  └─────────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture (Patient API)

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│              API Layer (api/v1/)            │
│  Routes, Request/Response handling          │
│  - auth.py, chat.py, diary.py, etc.        │
├─────────────────────────────────────────────┤
│            Service Layer (services/)         │
│  Business logic, orchestration              │
│  - AuthService, ChatService, etc.           │
├─────────────────────────────────────────────┤
│          Repository Layer (db/repositories/) │
│  Data access, queries                       │
│  - PatientRepository, ConversationRepo      │
├─────────────────────────────────────────────┤
│            Database Layer (db/models/)       │
│  ORM models, schema                         │
│  - PatientInfo, Conversations, Messages     │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
patient-api/src/
├── main.py                      # FastAPI application entry point
│
├── core/                        # Core infrastructure
│   ├── __init__.py
│   ├── config.py               # Pydantic settings (env vars)
│   ├── exceptions.py           # Custom exception classes
│   ├── logging.py              # Structured logging setup
│   └── middleware/             # Request middleware
│       ├── __init__.py
│       ├── correlation_id.py   # Request tracing
│       ├── error_handler.py    # Global exception handling
│       └── request_logging.py  # Request/response logging
│
├── db/                          # Database layer
│   ├── __init__.py
│   ├── base.py                 # SQLAlchemy Base, TimestampMixin
│   ├── session.py              # Database session management
│   ├── patient_models.py       # Legacy models (still used)
│   ├── doctor_models.py        # Doctor DB models (read-only)
│   ├── models/                 # New modular models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── conversation.py
│   │   └── medical.py
│   └── repositories/           # Data access layer
│       ├── __init__.py
│       ├── base.py             # Generic CRUD repository
│       ├── patient_repository.py
│       ├── conversation_repository.py
│       ├── chemo_repository.py
│       ├── diary_repository.py
│       ├── summary_repository.py
│       └── profile_repository.py
│
├── services/                    # Business logic layer
│   ├── __init__.py
│   ├── base.py                 # Base service class
│   ├── auth_service.py         # Cognito authentication
│   ├── chat_service.py         # Symptom checker chat
│   ├── chemo_service.py        # Chemotherapy tracking
│   ├── diary_service.py        # Diary entries
│   ├── summary_service.py      # Conversation summaries
│   ├── profile_service.py      # Patient profiles
│   └── patient_service.py      # Patient operations
│
├── api/                         # API layer (versioned)
│   ├── __init__.py
│   ├── deps.py                 # FastAPI dependencies
│   └── v1/
│       ├── __init__.py
│       ├── router.py           # Main v1 router
│       └── endpoints/
│           ├── __init__.py
│           ├── auth.py         # POST /auth/login, /signup
│           ├── chat.py         # GET/POST /chat/*, WS /chat/ws/*
│           ├── chemo.py        # POST /chemo/log, GET /chemo/history
│           ├── diary.py        # CRUD /diary/*
│           ├── summaries.py    # GET /summaries/*
│           ├── profile.py      # GET/PATCH /profile/*
│           ├── patients.py     # Patient management
│           └── health.py       # Health checks
│
└── routers/                     # Symptom Checker Engine
    └── chat/
        └── symptom_checker/
            ├── __init__.py
            ├── constants.py            # Triage levels, message types
            ├── symptom_definitions.py  # 27 symptom modules
            └── symptom_engine.py       # State machine engine
```

---

## Frontend Architecture (Patient Web)

### Directory Structure

```
patient-web/src/
├── main.tsx                     # React entry point
├── App.tsx                      # Root component with routing
│
├── api/                         # Type-safe API layer
│   ├── index.ts                # Main exports
│   ├── client.ts               # HTTP client with interceptors
│   ├── types.ts                # TypeScript type definitions
│   └── services/               # Domain-specific API calls
│       ├── index.ts
│       ├── auth.ts             # Authentication API
│       ├── chat.ts             # Chat + WebSocket API
│       ├── chemo.ts            # Chemotherapy API
│       ├── diary.ts            # Diary API
│       ├── profile.ts          # Profile API
│       └── summaries.ts        # Summaries API
│
├── config/                      # Configuration
│   └── api.ts                  # API endpoints config
│
├── context/                     # React Context providers
│   ├── index.ts
│   └── AuthContext.tsx         # Authentication state
│
├── hooks/                       # Custom React hooks
│   ├── index.ts
│   ├── useAuth.ts              # Authentication hook
│   ├── useChat.ts              # Chat/WebSocket hook
│   └── useApi.ts               # Generic API hook
│
├── components/                  # React components
│   ├── common/                 # Shared components
│   │   ├── index.ts
│   │   ├── ErrorBoundary.tsx   # Error handling
│   │   └── ErrorBoundary.css
│   └── chat/                   # Chat-specific components
│       ├── SymptomChat.css
│       └── SymptomMessageBubble.tsx
│
├── pages/                       # Page components
│   ├── ChatsPage/
│   ├── DiaryPage/
│   ├── ProfilePage/
│   └── LoginPage/
│
├── services/                    # Legacy services (being migrated)
└── utils/                       # Utility functions
```

### State Management Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                     AuthProvider (Context)                       │
│  - isAuthenticated, user, login(), logout()                     │
├─────────────────────────────────────────────────────────────────┤
│                          App Component                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     ErrorBoundary                           ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │                    Router                             │  ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │  ││
│  │  │  │  LoginPage  │ │  ChatsPage  │ │  Other Pages    │ │  ││
│  │  │  │             │ │  useChat()  │ │  useApi()       │ │  ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────────┘ │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Symptom Checker Architecture

### 27 Symptom Modules

| Category | Modules |
|----------|---------|
| **Emergency (5)** | Trouble Breathing, Chest Pain, Bleeding/Bruising, Fainting, Altered Mental Status |
| **Common Side Effects (5)** | Fever, Dehydration, Nausea, Vomiting, Diarrhea |
| **Pain (7)** | Pain Router, Port/IV Site, Headache, Abdominal, Leg/Calf, Joint/Muscle, Neuropathy |
| **Other (10)** | Constipation, Fatigue, Eye Complaints, Mouth Sores, No Appetite, Urinary Problems, Skin Rash, Swelling, Cough, Falls & Balance |

### State Machine Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GREETING  │────►│  SYMPTOM    │────►│  SCREENING  │────►│  FOLLOW-UP  │
│             │     │  SELECTION  │     │  QUESTIONS  │     │  QUESTIONS  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                    ┌─────────────────────────────────────────────┘
                    ▼
              ┌─────────────┐     ┌─────────────┐
              │   TRIAGE    │────►│  COMPLETE   │
              │  EVALUATION │     │             │
              └─────────────┘     └─────────────┘

Triage Levels:
- call_911: Emergency - immediate action required
- notify_care_team: Alert - care team notification
- none: Monitor - continue observation
```

---

## API Design Patterns

### Endpoint Naming Convention

```
/api/v1/{resource}              # Collection (GET list, POST create)
/api/v1/{resource}/{uuid}       # Instance (GET, PATCH, DELETE)
/api/v1/{resource}/{uuid}/{sub} # Sub-resource
```

### Request/Response Pattern

```python
# Request Models (Pydantic)
class CreateDiaryRequest(BaseModel):
    title: Optional[str]
    diary_entry: str
    marked_for_doctor: bool = False

# Response Models
class DiaryEntryResponse(BaseModel):
    entry_uuid: UUID
    title: Optional[str]
    diary_entry: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Error Handling

```python
# Custom Exceptions (core/exceptions.py)
class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class AuthorizationError(AppError):
    """User not authorized."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)

# Usage in endpoints
@router.get("/{uuid}")
async def get_resource(uuid: UUID):
    resource = service.get_by_uuid(uuid)
    if not resource:
        raise NotFoundError(f"Resource {uuid} not found")
    return resource
```

---

## Database Design

### Patient Database Tables

| Table | Description |
|-------|-------------|
| `patient_info` | Patient profiles (name, email, DOB, etc.) |
| `patient_configurations` | Patient settings (reminders, consent) |
| `patient_physician_associations` | Patient-doctor relationships |
| `patient_diary_entries` | Health journal entries |
| `patient_chemo_dates` | Chemotherapy date tracking |
| `conversations` | Chat sessions |
| `messages` | Chat messages |

### Doctor Database Tables

| Table | Description |
|-------|-------------|
| `staff_profiles` | Doctor/nurse profiles |
| `all_clinics` | Healthcare facilities |
| `staff_associations` | Staff-clinic relationships |

---

## Security

### Authentication Flow

```
1. User enters email/password
2. Frontend calls POST /api/v1/auth/login
3. Backend validates with AWS Cognito
4. Cognito returns JWT tokens
5. Frontend stores access_token in localStorage
6. Frontend includes token in Authorization header
7. Backend validates token on each request
```

### Authorization

```python
# Dependency injection for protected routes
@router.get("/protected")
async def protected_endpoint(
    current_user: TokenData = Depends(get_current_user)
):
    # current_user.sub = user UUID
    return {"user_id": current_user.sub}
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | development/staging/production | development |
| `DEBUG` | Enable debug mode | false |
| `LOG_LEVEL` | Logging level | INFO |
| `POSTGRES_HOST` | Database host | localhost |
| `POSTGRES_PORT` | Database port | 5432 |
| `POSTGRES_USER` | Database user | - |
| `POSTGRES_PASSWORD` | Database password | - |
| `POSTGRES_PATIENT_DB` | Patient database name | - |
| `POSTGRES_DOCTOR_DB` | Doctor database name | - |
| `AWS_REGION` | AWS region | us-west-2 |
| `COGNITO_USER_POOL_ID` | Cognito user pool | - |
| `COGNITO_CLIENT_ID` | Cognito client ID | - |
| `CORS_ORIGINS` | Allowed origins | - |

---

## Related Documentation

- [Features Documentation](apps/patient-platform/patient-api/docs/FEATURES.md)
- [Deployment Guide](apps/patient-platform/patient-api/docs/DEPLOYMENT.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)

---

*Last Updated: January 2026*

