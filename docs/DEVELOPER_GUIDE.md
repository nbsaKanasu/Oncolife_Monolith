# OncoLife Developer Guide

## Welcome! 👋

This guide will help you get started as a developer on the OncoLife platform. Whether you're working on the backend APIs or the frontend applications, this document covers everything you need to know.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [Patient Onboarding](#patient-onboarding) 🆕
6. [Code Patterns](#code-patterns)
7. [Testing](#testing)
8. [Git Workflow](#git-workflow)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend APIs |
| Node.js | 18+ | Frontend apps |
| PostgreSQL | 15+ | Database |
| Docker | Latest | Local services |
| Git | Latest | Version control |

### Quick Setup (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith

# 2. Start all services with Docker
docker-compose up -d

# 3. Verify services are running
curl http://localhost:8000/health  # Patient API
curl http://localhost:8001/health  # Doctor API
```

---

## Development Environment

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f patient-api

# Stop all services
docker-compose down
```

### Option 2: Manual Setup

#### Patient API

```bash
cd apps/patient-platform/patient-api

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
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

#### Doctor API

```bash
cd apps/doctor-platform/doctor-api

# Same steps as Patient API...
uvicorn main:app --reload --port 8001
```

#### Patient Web

```bash
cd apps/patient-platform/patient-web

# Install dependencies
npm install

# Run development server
npm run dev
```

#### Doctor Web

```bash
cd apps/doctor-platform/doctor-web
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in each API directory:

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
# DATABASE
# =============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=oncolife_admin
POSTGRES_PASSWORD=your_password
POSTGRES_PATIENT_DB=oncolife_patient
POSTGRES_DOCTOR_DB=oncolife_doctor

# =============================================================================
# AWS CORE
# =============================================================================
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# =============================================================================
# AWS COGNITO (Authentication)
# =============================================================================
COGNITO_USER_POOL_ID=us-west-2_xxxxx
COGNITO_CLIENT_ID=xxxxx
COGNITO_CLIENT_SECRET=xxxxx

# =============================================================================
# AWS S3 (Document Storage for Onboarding)
# =============================================================================
S3_REFERRAL_BUCKET=oncolife-referrals

# =============================================================================
# AWS SES (Email Notifications)
# =============================================================================
SES_SENDER_EMAIL=noreply@oncolife.com
SES_SENDER_NAME=OncoLife Care

# =============================================================================
# AWS SNS (SMS Notifications)
# =============================================================================
SNS_ENABLED=true

# =============================================================================
# FAX WEBHOOK (Sinch/Twilio)
# =============================================================================
FAX_WEBHOOK_SECRET=your_webhook_secret
FAX_INBOUND_NUMBER=+18001234567

# =============================================================================
# ONBOARDING SETTINGS
# =============================================================================
TERMS_VERSION=1.0
PRIVACY_VERSION=1.0
HIPAA_VERSION=1.0
ONBOARDING_TEMP_PASSWORD_LENGTH=12

# =============================================================================
# CORS
# =============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Backend Development

### Adding a New Endpoint

1. **Create the service** (if needed):

```python
# services/my_service.py
from .base import BaseService
from core.logging import get_logger

logger = get_logger(__name__)

class MyService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
    
    def my_operation(self, data: dict) -> dict:
        logger.info("Performing operation...")
        # Business logic here
        return result
```

2. **Create the endpoint**:

```python
# api/v1/endpoints/my_endpoint.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_patient_db, get_current_user
from services import MyService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    result: str

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(
    request: MyRequest,
    db: Session = Depends(get_patient_db),
    current_user = Depends(get_current_user)
):
    """
    My endpoint description.
    """
    service = MyService(db)
    result = service.my_operation(request.dict())
    return MyResponse(result=result)
```

3. **Register the router**:

```python
# api/v1/router.py
from .endpoints import my_endpoint

router.include_router(
    my_endpoint.router,
    prefix="/my-resource",
    tags=["My Resource"]
)
```

### Adding a Repository

```python
# db/repositories/my_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from .base import BaseRepository
from db.models.my_model import MyModel
from core.exceptions import NotFoundError

class MyRepository(BaseRepository[MyModel]):
    def __init__(self, db: Session):
        super().__init__(db, MyModel)
    
    def find_by_status(self, status: str) -> List[MyModel]:
        return self.db.query(MyModel).filter(
            MyModel.status == status
        ).all()
```

### Error Handling

```python
from core.exceptions import NotFoundError, ValidationError, AuthorizationError

# Raise exceptions - middleware handles the response
if not resource:
    raise NotFoundError(f"Resource {uuid} not found")

if not valid:
    raise ValidationError("Invalid data provided")

if not authorized:
    raise AuthorizationError("Not authorized to access this resource")
```

---

## Frontend Development

### Making API Calls

Use the type-safe API client:

```typescript
// Import the service
import { diaryApi } from '@/api/services';

// In a component
const MyComponent = () => {
  const [entries, setEntries] = useState<DiaryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await diaryApi.getAll();
        setEntries(data);
      } catch (error) {
        console.error('Failed to load entries:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // ...
};
```

### Using Custom Hooks

```typescript
// useApi hook for simple cases
import { useApi } from '@/hooks';
import { diaryApi } from '@/api/services';

const MyComponent = () => {
  const { data, isLoading, error, execute } = useApi(
    () => diaryApi.getAll(),
    { immediate: true }
  );

  if (isLoading) return <Loading />;
  if (error) return <Error message={error.message} />;
  
  return <DiaryList entries={data} />;
};
```

```typescript
// useChat hook for symptom checker
import { useChat } from '@/hooks';

const ChatComponent = () => {
  const { 
    messages, 
    isConnected, 
    sendMessage,
    isSending 
  } = useChat({
    patientUuid: 'xxx-xxx-xxx',
    autoConnect: true
  });

  const handleSend = (content: string) => {
    sendMessage(content, 'text');
  };

  // ...
};
```

### Authentication

```typescript
// Use the auth context
import { useAuthContext } from '@/context';

const MyComponent = () => {
  const { 
    isAuthenticated, 
    user, 
    login, 
    logout,
    isLoading 
  } = useAuthContext();

  const handleLogin = async (email: string, password: string) => {
    const success = await login({ email, password });
    if (success) {
      navigate('/dashboard');
    }
  };

  // ...
};
```

### Error Boundaries

Wrap components with error boundaries:

```tsx
import { ErrorBoundary } from '@/components/common';

const App = () => (
  <ErrorBoundary
    onError={(error, info) => console.error(error, info)}
    showDetails={process.env.NODE_ENV === 'development'}
  >
    <Router>
      {/* Your app */}
    </Router>
  </ErrorBoundary>
);
```

---

## Patient Onboarding

### Overview

The Patient Onboarding system is a zero-friction registration flow where:
1. **Clinic sends fax** → Patient doesn't do anything
2. **System creates account** → Automatic via Cognito
3. **Patient receives email** → Login credentials sent
4. **First login wizard** → Password, acknowledgement, terms, reminders

### Architecture

```
Clinic Fax → Sinch → Webhook → S3 → Textract → DB → Cognito → SES/SNS
```

### Key Services

| Service | File | Purpose |
|---------|------|---------|
| `FaxService` | `services/fax_service.py` | Receive webhook, upload to S3 |
| `OCRService` | `services/ocr_service.py` | AWS Textract processing |
| `NotificationService` | `services/notification_service.py` | Email/SMS via SES/SNS |
| `OnboardingService` | `services/onboarding_service.py` | Main orchestration |

### Testing Onboarding Locally

#### 1. Create a Manual Referral (No Fax Needed)

```bash
# First, get an auth token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@oncolife.com", "password": "password"}' \
  | jq -r '.tokens.access_token')

# Create a manual referral
curl -X POST http://localhost:8000/api/v1/onboarding/referral/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+15031234567",
    "dob": "1960-05-15",
    "cancer_type": "Breast Cancer",
    "physician_name": "Dr. Smith",
    "send_welcome": false
  }'
```

#### 2. Simulate a Fax Webhook (Sinch Format)

```bash
curl -X POST http://localhost:8000/api/v1/onboarding/webhook/fax/sinch \
  -H "Content-Type: application/json" \
  -d '{
    "faxId": "test-123",
    "fromNumber": "+15551234567",
    "toNumber": "+18001234567",
    "documentUrl": "https://example.com/test.pdf",
    "pages": 3
  }'
```

#### 3. Check Onboarding Status

```bash
curl http://localhost:8000/api/v1/onboarding/status \
  -H "Authorization: Bearer $TOKEN"
```

### Configuring Fax Provider (Sinch)

1. Log into Sinch Dashboard
2. Create a new fax number
3. Configure webhook URL:
   ```
   https://api.oncolife.com/api/v1/onboarding/webhook/fax/sinch
   ```
4. Set webhook secret (same as `FAX_WEBHOOK_SECRET` in `.env`)
5. Enable "fax.received" event

### Required AWS Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::oncolife-referrals/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:AnalyzeDocument",
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminDeleteUser"
      ],
      "Resource": "arn:aws:cognito-idp:*:*:userpool/*"
    }
  ]
}
```

### Frontend Onboarding Wizard

The frontend has a multi-step wizard at `/onboarding`:

```typescript
// pages/OnboardingPage/OnboardingWizard.tsx

// Step 1: Password Reset (handled by Cognito challenge)
// Step 2: Acknowledgement - Medical disclaimer
// Step 3: Terms & Privacy - Legal acceptance  
// Step 4: Reminder Setup - Email/SMS preferences
```

To use the onboarding API:

```typescript
import { onboardingApi } from '@/api/services';

// Check status
const status = await onboardingApi.getOnboardingStatus();

// Complete acknowledgement
await onboardingApi.completeAcknowledgementStep({
  acknowledged: true,
  acknowledgement_text: "I understand..."
});

// Complete terms
await onboardingApi.completeTermsStep({
  terms_accepted: true,
  privacy_accepted: true,
  hipaa_acknowledged: true
});

// Complete reminders
await onboardingApi.completeReminderStep({
  channel: 'email',
  reminder_time: '09:00'
});
```

### Database Migrations

Run the onboarding tables migration:

```sql
-- See apps/patient-platform/patient-api/docs/ONBOARDING.md for full SQL
CREATE TABLE patient_referrals (...);
CREATE TABLE patient_onboarding_status (...);
CREATE TABLE referral_documents (...);
CREATE TABLE onboarding_notification_log (...);
```

---

## Code Patterns

### Backend Patterns

| Pattern | Usage |
|---------|-------|
| **Repository** | Abstract database operations |
| **Service** | Business logic and orchestration |
| **Dependency Injection** | FastAPI Depends() for DB, auth |
| **Pydantic Models** | Request/response validation |

### Frontend Patterns

| Pattern | Usage |
|---------|-------|
| **Custom Hooks** | Encapsulate stateful logic |
| **Context API** | Global state (auth, theme) |
| **Error Boundaries** | Graceful error handling |
| **Type-safe API** | Typed API calls and responses |

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python files | snake_case | `auth_service.py` |
| Python classes | PascalCase | `AuthService` |
| Python functions | snake_case | `get_patient()` |
| TypeScript files | camelCase | `authService.ts` |
| React components | PascalCase | `ErrorBoundary.tsx` |
| CSS files | Same as component | `ErrorBoundary.css` |

---

## Testing

### Backend Tests

```bash
cd apps/patient-platform/patient-api
pytest

# With coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/test_auth.py -v
```

### Frontend Tests

```bash
cd apps/patient-platform/patient-web
npm test

# With coverage
npm run test:coverage
```

---

## Git Workflow

### Branch Naming

```
feature/add-symptom-module
bugfix/fix-login-error
hotfix/security-patch
refactor/modernize-api-client
```

### Commit Messages

```
feat: Add mouth sores symptom module
fix: Resolve authentication timeout issue
refactor: Migrate to type-safe API client
docs: Update developer guide
test: Add unit tests for ChatService
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes and commit
3. Push branch and create PR
4. Request code review
5. Address feedback
6. Merge after approval

---

## Troubleshooting

### Common Issues

#### "Module not found" in Python

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database connection errors

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check connection
psql -h localhost -U oncolife_admin -d oncolife_patient
```

#### CORS errors in browser

Check that `CORS_ORIGINS` in `.env` includes your frontend URL:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### Cognito authentication errors

1. Verify AWS credentials in `.env`
2. Check Cognito User Pool settings in AWS Console
3. Ensure client secret is correct

### Logs

```bash
# API logs
docker-compose logs -f patient-api

# Or if running locally
tail -f logs/app.log
```

---

## Need Help?

- Check the [Architecture Guide](ARCHITECTURE.md)
- Review the [Features Documentation](../apps/patient-platform/patient-api/docs/FEATURES.md)
- Look at existing code for examples
- Ask in the team Slack channel

---

*Last Updated: January 2026*

