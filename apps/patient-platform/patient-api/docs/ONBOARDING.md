# Patient Onboarding System - Complete Documentation

## Overview

The Patient Onboarding System handles the complete patient registration flow from clinic referral to active user. This is a **zero-friction** system where patients do not need to sign up - they are pre-registered based on clinic referrals.

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PATIENT ONBOARDING FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │   CLINIC     │     │   ONCOLIFE   │     │   ONCOLIFE   │     │   PATIENT    │
  │   (EHR)      │────▶│   FAX/OCR    │────▶│   COGNITO    │────▶│   WELCOME    │
  │              │     │   SYSTEM     │     │   + DB       │     │   EMAIL/SMS  │
  └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                        │
                                                                        ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │   ACTIVE     │     │   REMINDER   │     │   TERMS &    │     │   PASSWORD   │
  │   USER       │◀────│   SETUP      │◀────│   PRIVACY    │◀────│   RESET      │
  │   (CHAT)     │     │              │     │   ACCEPT     │     │   (First     │
  └──────────────┘     └──────────────┘     └──────────────┘     │   Login)     │
                                                                 └──────────────┘
```

## Components

### 1. Backend Services

#### Fax Service (`services/fax_service.py`) ⭐ NEW
- **Webhook receiver** for fax providers (Sinch, Twilio, Phaxio, RingCentral)
- **Signature validation** for webhook security
- **Document download** from provider URLs
- **Base64 decoding** for inline document payloads
- **S3 upload** with KMS encryption (HIPAA compliant)
- **Provider-specific payload parsing**

#### OCR Service (`services/ocr_service.py`)
- **AWS Textract** integration for document processing
- Extracts patient demographics, treatment info, medical history
- Supports async processing for multi-page faxes
- Confidence scoring and field validation

#### Notification Service (`services/notification_service.py`)
- **AWS SES** for email notifications
- **AWS SNS** for SMS notifications
- Welcome email with credentials
- Onboarding reminders
- Audit logging

#### Onboarding Service (`services/onboarding_service.py`)
- Main orchestration service
- Manages referral processing pipeline
- Creates Cognito users with temp passwords
- Tracks onboarding progress
- Manual referral entry support

### 2. Database Models (`db/models/referral.py`)

| Table | Description |
|-------|-------------|
| `patient_referrals` | Stores all referral data from clinic faxes |
| `patient_onboarding_status` | Tracks progress through onboarding steps |
| `referral_documents` | S3 references to original fax documents |
| `onboarding_notification_log` | Audit log of all notifications sent |

### 3. API Endpoints (`api/v1/endpoints/onboarding.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/onboarding/webhook/fax` | POST | Receive fax webhook from provider |
| `/onboarding/status` | GET | Get current onboarding status |
| `/onboarding/complete/password` | POST | Mark password step complete |
| `/onboarding/complete/acknowledgement` | POST | Complete medical disclaimer |
| `/onboarding/complete/terms` | POST | Accept terms/privacy |
| `/onboarding/complete/reminders` | POST | Set reminder preferences |
| `/onboarding/referral/manual` | POST | Create manual referral (admin) |
| `/onboarding/referral/{uuid}` | GET | Get referral details (admin) |

### 4. Frontend Components (`patient-web`)

#### OnboardingWizard (`pages/OnboardingPage/OnboardingWizard.tsx`)
- Multi-step wizard with progress indicator
- Step 1: Medical Acknowledgement
- Step 2: Terms & Privacy
- Step 3: Reminder Setup
- Automatic redirect on completion

#### API Services (`api/services/onboarding.ts`)
- Type-safe API client for onboarding endpoints
- Status fetching and step completion

---

## Detailed Flow

### Phase 1: Fax Reception (Complete Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Clinic (EHR) → Dedicated Fax Number                                │
│  - Epic/Cerner sends referral to Oncolife's fax number                      │
│  - AWS is NOT involved yet                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: Fax Provider (Sinch) → Digital Conversion                          │
│  - Receives analog fax                                                       │
│  - Converts to PDF/TIFF                                                      │
│  - Triggers webhook when complete                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: Webhook → Oncolife API (FastAPI or AWS Lambda)                     │
│  - POST /api/v1/onboarding/webhook/fax                                       │
│  - Validates signature (HMAC-SHA256)                                         │
│  - Downloads document from provider URL                                      │
│  - Or decodes base64 payload                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: Upload to S3 (Encrypted)                                           │
│  - Stored in: s3://oncolife-referrals/referrals/YYYY/MM/DD/fax_id.pdf       │
│  - Encrypted with AWS KMS (HIPAA compliant)                                  │
│  - Metadata stored in RDS                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: OCR Processing (AWS Textract)                                      │
│  - Extracts text, forms, tables                                              │
│  - Parses patient demographics, treatment info                               │
│  - Confidence scoring per field                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 6: Data Normalization → Patient Record                                │
│  - Structured fields stored in RDS                                           │
│  - Linked to original fax for auditability                                   │
│  - Validation for required fields                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 7: Patient Account Creation (Cognito + DB)                            │
│  - Pre-register in AWS Cognito                                               │
│  - Generate temporary password                                               │
│  - Create local DB records                                                   │
│  - Send welcome email/SMS                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fax Provider Integration Details

#### Supported Providers

| Provider | Webhook URL | Signature Method |
|----------|-------------|------------------|
| **Sinch** (recommended) | `/api/v1/onboarding/webhook/fax/sinch` | HMAC-SHA256 |
| **Twilio** | `/api/v1/onboarding/webhook/fax/twilio` | HMAC-SHA1 |
| **Phaxio** | `/api/v1/onboarding/webhook/fax/phaxio` | HMAC-SHA256 |
| **RingCentral** | `/api/v1/onboarding/webhook/fax/ringcentral` | HMAC-SHA256 |
| **Generic** | `/api/v1/onboarding/webhook/fax` | HMAC-SHA256 |

#### Sinch Webhook Configuration

```
Webhook URL: https://api.oncolife.com/api/v1/onboarding/webhook/fax/sinch
Method: POST
Content-Type: application/json
Headers:
  X-Webhook-Signature: <HMAC-SHA256 of body>
```

#### Twilio Webhook Configuration

```
Webhook URL: https://api.oncolife.com/api/v1/onboarding/webhook/fax/twilio
Method: POST
Content-Type: application/x-www-form-urlencoded
Headers:
  X-Twilio-Signature: <HMAC-SHA1 signature>
```

### Phase 2: Referral Reception (Legacy - Direct S3)

### Phase 2: OCR Processing

1. **AWS Textract** processes the document
2. **Form fields** are extracted:
   - Patient: Name, DOB, Email, Phone, MRN
   - Physician: Name, Clinic, NPI
   - Diagnosis: Cancer type, Staging
   - Treatment: Chemo regimen, Dates, Cycles
   - History: Medical, Surgical, Medications
   - Vitals: Height, Weight, BMI, BP
3. **Validation** checks for required fields
4. **Low confidence fields** flagged for review

### Phase 3: Patient Account Creation

1. **Cognito user** created with:
   - Email as username
   - Auto-generated temporary password
   - Email verified flag set
2. **Local DB records** created:
   - `patient_info` - Demographics
   - `patient_configurations` - Settings
   - `patient_physician_associations` - Care team link
   - `patient_onboarding_status` - Progress tracking
3. **Referral** linked to patient account

### Phase 4: Welcome Notification

1. **Email sent** via AWS SES containing:
   - Login URL
   - Username (email)
   - Temporary password
   - Brief explanation
2. **SMS sent** (optional) via AWS SNS:
   - Short welcome message
   - Link to app

### Phase 5: First Login (Mandatory Steps)

#### Step 1: Password Reset
- Cognito forces `NEW_PASSWORD_REQUIRED` challenge
- Patient creates new secure password
- Frontend calls `/onboarding/complete/password`

#### Step 2: Acknowledgement
- Patient reads medical disclaimer
- Must check acknowledgement box
- IP address logged for audit
- Frontend calls `/onboarding/complete/acknowledgement`

#### Step 3: Terms & Privacy
- Must accept Terms & Conditions
- Must accept Privacy Policy
- HIPAA notice acknowledged
- Version numbers stored for compliance
- Frontend calls `/onboarding/complete/terms`

#### Step 4: Reminder Setup
- Choose notification channel (email/SMS/both)
- Set daily reminder time
- Timezone automatically detected
- Frontend calls `/onboarding/complete/reminders`

### Phase 6: Onboarding Complete

1. **Patient is fully activated**
2. **Redirected to Chat screen**
3. **Referral status** updated to `COMPLETED`
4. **Daily reminders** will start based on preference

---

## AWS Services Required

### Cognito
- User Pool for patient authentication
- App client with ADMIN_USER_PASSWORD_AUTH flow
- Temporary password support

### S3
- Bucket for referral document storage
- Lifecycle policies for retention

### Textract
- Document analysis for OCR
- Form and table extraction

### SES
- Verified sender email
- Email templates (optional)

### SNS
- SMS messaging enabled
- Transactional message type

---

## Environment Variables

```env
# AWS Core
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Cognito
COGNITO_USER_POOL_ID=us-west-2_xxxxx
COGNITO_CLIENT_ID=xxxxx
COGNITO_CLIENT_SECRET=xxxxx

# S3
S3_REFERRAL_BUCKET=oncolife-referrals

# SES
SES_SENDER_EMAIL=noreply@oncolife.com
SES_SENDER_NAME=OncoLife Care

# SNS
SNS_ENABLED=true

# Fax Webhook
FAX_WEBHOOK_SECRET=your-webhook-secret

# Onboarding
ONBOARDING_TEMP_PASSWORD_LENGTH=12
TERMS_VERSION=1.0
PRIVACY_VERSION=1.0
```

---

## Database Migration

```sql
-- Create referral tables
CREATE TABLE patient_referrals (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'received',
    status_message TEXT,
    
    -- Source
    fax_number VARCHAR(20),
    fax_received_at TIMESTAMP WITH TIME ZONE,
    
    -- Patient Demographics
    patient_first_name VARCHAR(100),
    patient_last_name VARCHAR(100),
    patient_email VARCHAR(255),
    patient_phone VARCHAR(20),
    patient_dob DATE,
    patient_sex VARCHAR(20),
    patient_mrn VARCHAR(50),
    
    -- Physician
    attending_physician_name VARCHAR(255),
    clinic_name VARCHAR(255),
    
    -- Cancer/Treatment
    cancer_type VARCHAR(255),
    cancer_staging VARCHAR(100),
    chemo_plan_name VARCHAR(500),
    chemo_start_date DATE,
    chemo_end_date DATE,
    chemo_current_cycle INTEGER,
    chemo_total_cycles INTEGER,
    
    -- Vitals
    bmi FLOAT,
    height_cm FLOAT,
    weight_kg FLOAT,
    blood_pressure VARCHAR(20),
    
    -- History
    past_medical_history TEXT,
    past_surgical_history TEXT,
    current_medications JSONB,
    
    -- Raw Data
    raw_extracted_data JSONB,
    extraction_confidence FLOAT,
    fields_needing_review JSONB,
    
    -- Patient Link
    patient_uuid UUID,
    cognito_user_id VARCHAR(100)
);

CREATE TABLE patient_onboarding_status (
    id SERIAL PRIMARY KEY,
    referral_uuid UUID UNIQUE REFERENCES patient_referrals(uuid),
    patient_uuid UUID,
    
    -- Current Step
    current_step VARCHAR(50) NOT NULL DEFAULT 'not_started',
    
    -- Password Reset
    password_reset_completed BOOLEAN DEFAULT FALSE,
    password_reset_at TIMESTAMP WITH TIME ZONE,
    
    -- Acknowledgement
    acknowledgement_completed BOOLEAN DEFAULT FALSE,
    acknowledgement_text TEXT,
    acknowledgement_at TIMESTAMP WITH TIME ZONE,
    acknowledgement_ip VARCHAR(50),
    
    -- Terms & Privacy
    terms_accepted BOOLEAN DEFAULT FALSE,
    terms_version VARCHAR(20),
    terms_accepted_at TIMESTAMP WITH TIME ZONE,
    privacy_accepted BOOLEAN DEFAULT FALSE,
    privacy_version VARCHAR(20),
    privacy_accepted_at TIMESTAMP WITH TIME ZONE,
    hipaa_acknowledged BOOLEAN DEFAULT FALSE,
    
    -- Reminders
    reminder_preference_set BOOLEAN DEFAULT FALSE,
    reminder_channel VARCHAR(20),
    reminder_time VARCHAR(10),
    reminder_timezone VARCHAR(50),
    
    -- Completion
    is_fully_onboarded BOOLEAN DEFAULT FALSE,
    onboarding_completed_at TIMESTAMP WITH TIME ZONE,
    first_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Notifications
    welcome_email_sent BOOLEAN DEFAULT FALSE,
    welcome_email_sent_at TIMESTAMP WITH TIME ZONE,
    welcome_sms_sent BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE referral_documents (
    id SERIAL PRIMARY KEY,
    referral_uuid UUID REFERENCES patient_referrals(uuid),
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    page_count INTEGER DEFAULT 1,
    textract_job_id VARCHAR(255),
    raw_ocr_text TEXT,
    ocr_confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE onboarding_notification_log (
    id SERIAL PRIMARY KEY,
    patient_uuid UUID,
    referral_uuid UUID,
    notification_type VARCHAR(50),
    channel VARCHAR(20),
    recipient VARCHAR(255),
    status VARCHAR(20),
    status_message TEXT,
    aws_message_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_referrals_status ON patient_referrals(status);
CREATE INDEX idx_referrals_patient_uuid ON patient_referrals(patient_uuid);
CREATE INDEX idx_onboarding_patient_uuid ON patient_onboarding_status(patient_uuid);
CREATE INDEX idx_notification_log_patient ON onboarding_notification_log(patient_uuid);
```

---

## Testing

### Manual Referral (for testing)

```bash
curl -X POST "http://localhost:8000/api/v1/onboarding/referral/manual" \
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
    "send_welcome": true
  }'
```

### Check Onboarding Status

```bash
curl "http://localhost:8000/api/v1/onboarding/status" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Fax Service Integration

### Supported Providers
- Phaxio
- eFax
- RingCentral Fax
- Twilio Fax

### Webhook Payload Example (Phaxio)

```json
{
  "fax_id": "12345678",
  "from_number": "+15551234567",
  "to_number": "+18005551234",
  "received_at": "2026-01-04T12:00:00Z",
  "pages": 3,
  "s3_bucket": "oncolife-referrals",
  "s3_key": "faxes/2026/01/04/12345678.pdf"
}
```

### Webhook Security

Validate incoming requests using HMAC signature:

```python
expected_sig = hmac.new(
    settings.fax_webhook_secret.encode(),
    request_body,
    hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(x_webhook_signature, expected_sig):
    raise HTTPException(status_code=401)
```

---

## Compliance Notes

### HIPAA
- All PHI encrypted in transit (TLS) and at rest (S3, RDS)
- Access logging enabled
- IP addresses logged for legal compliance
- Consent and acceptance timestamps stored

### Data Retention
- Referral documents: 7 years (HIPAA requirement)
- Notification logs: 3 years
- Onboarding status: Indefinite (linked to patient)

---

*Last Updated: January 2026*

