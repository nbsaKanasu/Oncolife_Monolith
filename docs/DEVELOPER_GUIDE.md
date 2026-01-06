# OncoLife Developer Guide

**Version 2.0 | Updated January 2026**

---

## Table of Contents

1. [Quick Start (5 Minutes)](#1-quick-start-5-minutes)
2. [Project Structure](#2-project-structure)
3. [Development Environment](#3-development-environment)
4. [Backend Development](#4-backend-development)
5. [Frontend Development](#5-frontend-development)
6. [Database Operations](#6-database-operations)
7. [Testing](#7-testing)
8. [Code Patterns](#8-code-patterns)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Quick Start (5 Minutes)

### Prerequisites

| Tool | Version | Verify | Install |
|------|---------|--------|---------|
| Docker Desktop | Latest | `docker --version` | [docker.com](https://docker.com) |
| Node.js | 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| Python | 3.11+ | `python --version` | [python.org](https://python.org) |
| Git | Latest | `git --version` | [git-scm.com](https://git-scm.com) |

### Clone and Start

```bash
# 1. Clone repository
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith

# 2. Start all services with Docker
docker-compose up -d

# 3. Wait for services to be ready (30 seconds)
sleep 30

# 4. Verify everything is running
curl http://localhost:8000/health   # Patient API
curl http://localhost:8001/health   # Doctor API
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Patient API | http://localhost:8000 | Backend for patient app |
| Patient API Docs | http://localhost:8000/docs | Swagger UI |
| Doctor API | http://localhost:8001 | Backend for doctor app |
| Doctor API Docs | http://localhost:8001/docs | Swagger UI |
| Patient Web | http://localhost:5173 | React frontend |
| Doctor Web | http://localhost:5174 | React frontend |
| PostgreSQL | localhost:5432 | Database |

---

## 2. Project Structure

```
OncoLife_Monolith/
├── apps/
│   ├── patient-platform/
│   │   ├── patient-api/              # FastAPI Backend
│   │   │   ├── src/
│   │   │   │   ├── api/v1/endpoints/ # REST endpoints
│   │   │   │   ├── services/         # Business logic
│   │   │   │   ├── db/
│   │   │   │   │   ├── models/       # SQLAlchemy models
│   │   │   │   │   └── repositories/ # Data access
│   │   │   │   ├── routers/chat/     # WebSocket + symptom rules
│   │   │   │   └── core/             # Config, logging, exceptions
│   │   │   ├── scripts/              # Seed scripts
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   └── patient-web/              # React Frontend
│   │       ├── src/
│   │       │   ├── components/       # Layout, Chat components
│   │       │   ├── pages/
│   │       │   │   ├── ChatsPage/    # Symptom checker (6-phase flow)
│   │       │   │   ├── SummariesPage/# Past triage summaries
│   │       │   │   ├── NotesPage/    # Patient diary
│   │       │   │   ├── QuestionsPage/# Questions for doctor ← NEW
│   │       │   │   ├── EducationPage/# Learning resources
│   │       │   │   ├── ProfilePage/  # Account settings
│   │       │   │   ├── LoginPage/    # Auth pages
│   │       │   │   └── OnboardingPage/# First-time setup
│   │       │   ├── services/         # API client (questions.ts, notes.ts, etc.)
│   │       │   ├── hooks/            # Custom hooks
│   │       │   └── contexts/         # AuthContext, UserContext
│   │       └── package.json
│   │
│   └── doctor-platform/
│       ├── doctor-api/               # Same structure as patient-api
│       └── doctor-web/               # React Frontend
│           ├── src/
│           │   ├── components/       # Layout
│           │   ├── pages/
│           │   │   ├── Dashboard/    # Severity-ranked patient list
│           │   │   ├── Patients/     # Patient management
│           │   │   ├── PatientDetail/# Patient timeline ← NEW
│           │   │   ├── Reports/      # Weekly reports ← NEW
│           │   │   ├── Staff/        # Staff management
│           │   │   └── LoginPage/    # Auth pages
│           │   ├── services/         # API client (dashboard.ts, patients.ts)
│           │   └── contexts/         # AuthContext, UserContext
│           └── package.json
│
├── packages/
│   └── ui-components/                # Shared React components
│       ├── src/
│       │   ├── components/           # ErrorBoundary, DarkModeToggle, etc.
│       │   ├── contexts/             # ThemeContext
│       │   └── styles/               # Theme definitions
│       └── package.json
│
├── docs/                             # Documentation
├── scripts/
│   ├── aws/                          # Deployment scripts
│   └── db/                           # Database scripts
└── docker-compose.yml                # Local development
```

---

## 3. Development Environment

### Option A: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs for a specific service
docker-compose logs -f patient-api

# Rebuild after code changes
docker-compose up -d --build patient-api

# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v
```

### Option B: Manual Setup

#### Backend (Patient API)

**Windows (PowerShell):**
```powershell
cd apps/patient-platform/patient-api

# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env
# Edit .env with your settings

# Run the API
cd src
uvicorn main:app --reload --port 8000
```

**Mac/Linux:**
```bash
cd apps/patient-platform/patient-api

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your settings

# Run the API
cd src
uvicorn main:app --reload --port 8000
```

#### Frontend (Patient Web)

```bash
cd apps/patient-platform/patient-web

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Environment Variables

Create `.env` file in each API directory:

```env
# =============================================================================
# APPLICATION
# =============================================================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
APP_NAME=OncoLife Patient API
APP_VERSION=1.0.0

# =============================================================================
# DATABASE (for Docker Compose)
# =============================================================================
PATIENT_DB_HOST=localhost
PATIENT_DB_PORT=5432
PATIENT_DB_NAME=oncolife_patient
PATIENT_DB_USER=oncolife_admin
PATIENT_DB_PASSWORD=oncolife_password

# =============================================================================
# AWS (for local development - use fake values or localstack)
# =============================================================================
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# For Cognito - leave empty for local mock auth
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_CLIENT_SECRET=

# =============================================================================
# CORS
# =============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174
```

---

## 4. Backend Development

### Adding a New API Endpoint

**Step 1: Create Pydantic Models**

```python
# api/v1/endpoints/schemas/my_resource.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class MyResourceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MyResourceResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Create Service**

```python
# services/my_resource_service.py
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from db.models.my_resource import MyResource
from core.logging import get_logger

logger = get_logger(__name__)

class MyResourceService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, description: Optional[str] = None) -> MyResource:
        logger.info(f"Creating resource: {name}")
        resource = MyResource(name=name, description=description)
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource

    def get_by_id(self, resource_id: UUID) -> Optional[MyResource]:
        return self.db.query(MyResource).filter(
            MyResource.id == resource_id,
            MyResource.is_deleted == False
        ).first()

    def list_all(self, limit: int = 100) -> List[MyResource]:
        return self.db.query(MyResource).filter(
            MyResource.is_deleted == False
        ).limit(limit).all()
```

**Step 3: Create Endpoint**

```python
# api/v1/endpoints/my_resource.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from api.deps import get_patient_db, get_current_user
from services.my_resource_service import MyResourceService
from .schemas.my_resource import MyResourceCreate, MyResourceResponse
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/", response_model=MyResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: MyResourceCreate,
    db: Session = Depends(get_patient_db),
    current_user = Depends(get_current_user)
):
    """Create a new resource."""
    service = MyResourceService(db)
    resource = service.create(data.name, data.description)
    return resource

@router.get("/", response_model=List[MyResourceResponse])
async def list_resources(
    limit: int = 100,
    db: Session = Depends(get_patient_db),
    current_user = Depends(get_current_user)
):
    """List all resources."""
    service = MyResourceService(db)
    return service.list_all(limit)

@router.get("/{resource_id}", response_model=MyResourceResponse)
async def get_resource(
    resource_id: UUID,
    db: Session = Depends(get_patient_db),
    current_user = Depends(get_current_user)
):
    """Get a specific resource."""
    service = MyResourceService(db)
    resource = service.get_by_id(resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource {resource_id} not found"
        )
    return resource
```

**Step 4: Register Router**

```python
# api/v1/router.py
from .endpoints import my_resource

router.include_router(
    my_resource.router,
    prefix="/my-resources",
    tags=["My Resources"]
)
```

### Adding a Database Model

```python
# db/models/my_resource.py
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from db.base import Base

class MyResource(Base):
    __tablename__ = "my_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MyResource(id={self.id}, name={self.name})>"
```

### Error Handling

Use the built-in exceptions:

```python
from core.exceptions import NotFoundError, ValidationError, AuthorizationError

# These are automatically converted to proper HTTP responses
if not resource:
    raise NotFoundError(f"Resource {uuid} not found")

if not valid_data:
    raise ValidationError("Data validation failed")

if not authorized:
    raise AuthorizationError("Access denied")
```

---

## 5. Frontend Development

### Using the API Client

```typescript
// services/api/myResourceApi.ts
import { apiClient } from './client';

export interface MyResource {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export const myResourceApi = {
  list: () => apiClient.get<MyResource[]>('/my-resources'),
  
  get: (id: string) => apiClient.get<MyResource>(`/my-resources/${id}`),
  
  create: (data: { name: string; description?: string }) => 
    apiClient.post<MyResource>('/my-resources', data),
};
```

### Using React Query

```tsx
// pages/MyResourcePage.tsx
import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { myResourceApi } from '@/services/api/myResourceApi';

const MyResourcePage: React.FC = () => {
  const queryClient = useQueryClient();
  
  // Fetch resources
  const { data: resources, isLoading, error } = useQuery({
    queryKey: ['my-resources'],
    queryFn: myResourceApi.list,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: myResourceApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-resources'] });
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading resources</div>;

  return (
    <div>
      <h1>My Resources</h1>
      <ul>
        {resources?.map((r) => (
          <li key={r.id}>{r.name}</li>
        ))}
      </ul>
      <button onClick={() => createMutation.mutate({ name: 'New Resource' })}>
        Add Resource
      </button>
    </div>
  );
};
```

### Using Custom Hooks

```typescript
// hooks/useAuth.ts
import { useAuthContext } from '@/contexts/AuthContext';

export const useAuth = () => {
  const context = useAuthContext();
  
  return {
    isAuthenticated: context.isAuthenticated,
    user: context.user,
    login: context.login,
    logout: context.logout,
    isLoading: context.isLoading,
  };
};
```

### Using the Theme

```tsx
import { useThemeMode, DarkModeToggle } from '@oncolife/ui-components';

const MyComponent = () => {
  const { isDark, toggleTheme } = useThemeMode();

  return (
    <div style={{ background: isDark ? '#1E293B' : '#F5F7FA' }}>
      <h1>Current mode: {isDark ? 'Dark' : 'Light'}</h1>
      <DarkModeToggle variant="pill" />
    </div>
  );
};
```

---

## 6. Database Operations

### Running Migrations

```bash
cd apps/patient-platform/patient-api/src

# Create a new migration
alembic revision --autogenerate -m "Add my_resources table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Direct Table Creation (Development)

```python
# Quick table creation for development
from db.base import Base
from db.session import engine
from db.models import *  # Import all models

Base.metadata.create_all(bind=engine)
print("Tables created!")
```

### Database Console

```bash
# Connect to local PostgreSQL
docker exec -it oncolife-postgres psql -U oncolife_admin -d oncolife_patient

# Common commands:
\dt                    # List tables
\d table_name          # Describe table
SELECT * FROM users;   # Query
\q                     # Quit
```

---

## 7. Testing

### Backend Tests

```bash
cd apps/patient-platform/patient-api

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run tests matching a pattern
pytest -k "test_login" -v
```

### Frontend Tests

```bash
cd apps/patient-platform/patient-web

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### API Testing with cURL

```bash
# Health check
curl http://localhost:8000/health

# Login (if using mock auth)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Authenticated request
curl http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 8. Code Patterns

### Backend Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Repository | `db/repositories/` | Abstract database queries |
| Service | `services/` | Business logic |
| Dependency Injection | FastAPI `Depends()` | Testable dependencies |
| Pydantic Models | `api/v1/endpoints/schemas/` | Request/response validation |

### Frontend Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Custom Hooks | `hooks/` | Reusable stateful logic |
| Context API | `contexts/` | Global state (auth, theme) |
| Error Boundaries | `@oncolife/ui-components` | Graceful error handling |
| API Client | `services/` | Type-safe API calls |

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python files | snake_case | `auth_service.py` |
| Python classes | PascalCase | `AuthService` |
| Python functions | snake_case | `get_patient()` |
| TypeScript files | camelCase | `authService.ts` |
| React components | PascalCase | `ErrorBoundary.tsx` |
| CSS/styled files | Same as component | `ErrorBoundary.styles.ts` |

---

## 9. Troubleshooting

### Common Issues

#### "Module not found" in Python

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Mac/Linux
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres

# Reset database (loses data!)
docker-compose down -v
docker-compose up -d
```

#### CORS Errors in Browser

Check `.env` includes your frontend URL:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174
```

#### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 PID  # Mac/Linux
taskkill /PID PID /F  # Windows
```

#### Frontend Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### Viewing Logs

```bash
# Docker logs
docker-compose logs -f patient-api
docker-compose logs -f patient-web

# API logs (manual run)
tail -f logs/app.log
```

### Getting Help

1. Check [Architecture Guide](ARCHITECTURE.md) for system overview
2. Check [Deployment Guide](STEP_BY_STEP_DEPLOYMENT.md) for AWS setup
3. Review existing code for patterns
4. Check CloudWatch Logs (production)

---

*Document Version: 2.0*
*Last Updated: January 2026*
