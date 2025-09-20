# OncoLife Doctor API

A FastAPI-based backend service for the OncoLife doctor platform, providing authentication, patient management, staff management, and dashboard functionality for healthcare providers.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [Authentication Routes](#authentication-routes)
  - [Dashboard Routes](#dashboard-routes)
  - [Patient Management](#patient-management)
  - [Staff Management](#staff-management)
  - [Patient Dashboard](#patient-dashboard)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [Setup and Installation](#setup-and-installation)

## Overview

The OncoLife Doctor API is built with FastAPI and integrates with AWS Cognito for authentication. It provides comprehensive functionality for healthcare providers to manage patients, staff, and view patient analytics.

### Key Features

- **AWS Cognito Integration**: Secure authentication and user management
- **Patient Management**: CRUD operations for patient records
- **Staff Management**: Manage healthcare staff and clinic associations
- **Dashboard Analytics**: View patient conversation data and summaries
- **Role-based Access**: Different access levels for physicians, staff, and admins

## Authentication

All endpoints (except health check and authentication routes) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

The API uses AWS Cognito for authentication, and tokens are validated on each request.

## API Endpoints

### Health Check

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "ok",
  "service": "doctor-api"
}
```

---

## Authentication Routes

### POST /auth/doctor/signup
Register a new doctor/staff member.

**Required Parameters:**
- `email` (string): Valid email address
- `first_name` (string): First name
- `last_name` (string): Last name

**Optional Parameters:**
- `role` (string): User role, defaults to "admin"
- `npi_number` (string): National Provider Identifier
- `physician_uuids` (array): List of physician UUIDs to associate with
- `clinic_uuid` (string): Clinic UUID, will use existing clinic if not provided

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "physician",
  "npi_number": "1234567890",
  "physician_uuids": ["uuid1", "uuid2"],
  "clinic_uuid": "clinic-uuid"
}
```

**Response:**
```json
{
  "message": "Doctor/Staff member doctor@example.com created successfully. A temporary password has been sent to their email.",
  "email": "doctor@example.com",
  "user_status": "FORCE_CHANGE_PASSWORD",
  "staff_uuid": "generated-uuid"
}
```

### POST /auth/admin/signup
Register a new admin user.

**Required Parameters:**
- `email` (string): Valid email address
- `first_name` (string): First name
- `last_name` (string): Last name

**Optional Parameters:**
- `npi_number` (string): National Provider Identifier
- `physician_uuids` (array): List of physician UUIDs to associate with
- `clinic_uuid` (string): Clinic UUID, will use existing clinic if not provided

**Note:** Role is automatically set to "admin" regardless of request.

**Request Body:**
```json
{
  "email": "admin@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "admin",
  "npi_number": "0987654321",
  "physician_uuids": ["uuid1"],
  "clinic_uuid": "clinic-uuid"
}
```

**Response:**
```json
{
  "message": "Admin user admin@example.com created successfully. A temporary password has been sent to their email.",
  "email": "admin@example.com",
  "user_status": "FORCE_CHANGE_PASSWORD",
  "staff_uuid": "generated-uuid"
}
```

### POST /auth/doctor/login
Authenticate doctor/staff member.

**Required Parameters:**
- `email` (string): Valid email address
- `password` (string): User password

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "password": "password123"
}
```

**Response (Successful Login):**
```json
{
  "valid": true,
  "message": "Login credentials are valid",
  "user_status": "CONFIRMED",
  "tokens": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...",
    "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  },
  "requiresPasswordChange": false
}
```

**Response (Password Change Required):**
```json
{
  "valid": true,
  "message": "Login credentials are valid but password change is required.",
  "user_status": "FORCE_CHANGE_PASSWORD",
  "session": "session-token",
  "requiresPasswordChange": true
}
```

### POST /auth/doctor/complete-new-password
Complete password setup for new users.

**Required Parameters:**
- `email` (string): Valid email address
- `new_password` (string): New password meeting Cognito requirements
- `session` (string): Session token from login response

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "new_password": "newpassword123",
  "session": "session-token"
}
```

**Response:**
```json
{
  "message": "Password successfully changed and doctor authenticated.",
  "tokens": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ...",
    "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  }
}
```

### POST /auth/forgot-password
Initiate password reset flow.

**Required Parameters:**
- `email` (string): Valid email address

**Request Body:**
```json
{
  "email": "doctor@example.com"
}
```

**Response:**
```json
{
  "message": "Password reset code has been sent to your email",
  "email": "doctor@example.com"
}
```

### POST /auth/reset-password
Complete password reset.

**Required Parameters:**
- `email` (string): Valid email address
- `confirmation_code` (string): 6-digit code sent to email
- `new_password` (string): New password meeting Cognito requirements

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "confirmation_code": "123456",
  "new_password": "newpassword123"
}
```

**Response:**
```json
{
  "message": "Password has been reset successfully",
  "email": "doctor@example.com"
}
```

### GET /auth/doctor/profile
Get current user's profile information.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response:**
```json
{
  "staff_uuid": "user-uuid",
  "email_address": "doctor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "physician",
  "npi_number": "1234567890",
  "clinic_name": "OncoLife Clinic"
}
```

### DELETE /auth/remove-staff
Remove a staff member from the system.

**Required Parameters:**
- `email` (string): Valid email address of staff member to remove

**Optional Parameters:**
- `skip_aws` (boolean): Skip AWS Cognito deletion, defaults to false

**Request Body:**
```json
{
  "email": "staff@example.com",
  "skip_aws": false
}
```

**Response:** `204 No Content`

### POST /auth/logout
Client-side logout (formality endpoint).

**Response:**
```json
{
  "message": "Logout successful"
}
```

---

## Dashboard Routes

### GET /dashboard/get-dashboard-info
Get paginated dashboard information for patients.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Optional Query Parameters:**
- `page` (int): Page number (default: 1, min: 1)
- `page_size` (int): Number of patients per page (default: 20, min: 1, max: 100)

**Response:**
```json
{
  "patients": [
    {
      "patient_uuid": "patient-uuid",
      "full_name": "John Smith",
      "dob": "1980-01-15",
      "mrn": "MRN123456",
      "last_conversation": {
        "bulleted_summary": "Patient reported fatigue and nausea. Symptoms are manageable.",
        "symptom_list": ["fatigue", "nausea"],
        "conversation_state": "COMPLETED"
      }
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

## Patient Management

### GET /patients/get-patients
Get paginated list of patients.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Optional Query Parameters:**
- `page` (int): Page number (default: 1, min: 1)
- `page_size` (int): Number of patients per page (default: 20, min: 1, max: 100)

**Response:**
```json
{
  "patients": [
    {
      "uuid": "patient-uuid",
      "mrn": "MRN123456",
      "first_name": "John",
      "last_name": "Smith",
      "email": "john.smith@example.com",
      "dob": "1980-01-15",
      "sex": "M"
    }
  ],
  "total_count": 25,
  "page": 1,
  "page_size": 20,
  "total_pages": 2
}
```

### POST /patients/add-patient
Add a new patient.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Parameters:**
- `email_address` (string): Valid email address
- `first_name` (string): Patient's first name
- `last_name` (string): Patient's last name
- `mrn` (string): Medical Record Number (must be unique)
- `physician_uuid` (string): UUID of associated physician
- `clinic_uuid` (string): UUID of associated clinic

**Optional Parameters:**
- `sex` (string): Patient's sex (M/F)
- `dob` (date): Date of birth (YYYY-MM-DD)
- `ethnicity` (string): Patient's ethnicity
- `phone_number` (string): Contact phone number
- `disease_type` (string): Type of disease/condition
- `treatment_type` (string): Type of treatment

**Request Body:**
```json
{
  "email_address": "patient@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "sex": "F",
  "dob": "1985-05-20",
  "mrn": "MRN789012",
  "ethnicity": "Caucasian",
  "phone_number": "+1234567890",
  "disease_type": "Breast Cancer",
  "treatment_type": "Chemotherapy",
  "physician_uuid": "physician-uuid",
  "clinic_uuid": "clinic-uuid"
}
```

**Response:**
```json
{
  "message": "Patient added successfully",
  "patient_uuid": "new-patient-uuid",
  "mrn": "MRN789012"
}
```

### PATCH /patients/edit-patient/{patient_uuid}
Edit patient information.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Path Parameters:**
- `patient_uuid` (string): UUID of the patient to edit

**Optional Parameters (all fields are optional for updates):**
- `first_name` (string): Patient's first name
- `last_name` (string): Patient's last name
- `sex` (string): Patient's sex (M/F)
- `dob` (date): Date of birth (YYYY-MM-DD)
- `ethnicity` (string): Patient's ethnicity
- `phone_number` (string): Contact phone number
- `disease_type` (string): Type of disease/condition
- `treatment_type` (string): Type of treatment

**Note:** Email, MRN, physician, and clinic cannot be changed.

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "sex": "F",
  "dob": "1985-05-20",
  "ethnicity": "Caucasian",
  "phone_number": "+1234567890",
  "disease_type": "Breast Cancer",
  "treatment_type": "Chemotherapy"
}
```

**Response:**
```json
{
  "message": "Patient updated successfully",
  "patient_uuid": "patient-uuid"
}
```

---

## Staff Management

### GET /staff/get-staff
Get paginated list of staff members in the same clinic.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Optional Query Parameters:**
- `page` (int): Page number (default: 1, min: 1)
- `page_size` (int): Number of staff per page (default: 20, min: 1, max: 100)

**Response:**
```json
{
  "staff": [
    {
      "staff_uuid": "staff-uuid",
      "first_name": "John",
      "last_name": "Doe",
      "email_address": "john.doe@example.com",
      "role": "physician"
    }
  ],
  "total_count": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### POST /staff/add-clinic
Add a new clinic.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Parameters:**
- `clinic_name` (string): Name of the clinic
- `address` (string): Full address of the clinic
- `phone_number` (string): Primary phone number
- `fax_number` (string): Fax number

**Request Body:**
```json
{
  "clinic_name": "OncoLife Main Clinic",
  "address": "123 Medical Drive, City, State 12345",
  "phone_number": "+1234567890",
  "fax_number": "+1234567891"
}
```

**Response:**
```json
{
  "message": "Clinic added successfully",
  "clinic_uuid": "new-clinic-uuid"
}
```

### POST /staff/add-physician
Add a new physician.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Parameters:**
- `email_address` (string): Valid email address
- `first_name` (string): Physician's first name
- `last_name` (string): Physician's last name
- `npi_number` (string): National Provider Identifier
- `clinic_uuid` (string): UUID of the clinic

**Request Body:**
```json
{
  "email_address": "physician@example.com",
  "first_name": "Dr. Sarah",
  "last_name": "Johnson",
  "npi_number": "1234567890",
  "clinic_uuid": "clinic-uuid"
}
```

**Response:**
```json
{
  "message": "Physician added successfully",
  "staff_uuid": "new-physician-uuid"
}
```

### POST /staff/add-staff
Add a new staff member.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Parameters:**
- `email_address` (string): Valid email address
- `first_name` (string): Staff member's first name
- `last_name` (string): Staff member's last name
- `role` (string): Staff role (e.g., "nurse", "admin", "staff")
- `physician_uuid` (string): UUID of associated physician
- `clinic_uuid` (string): UUID of associated clinic

**Optional Parameters:**
- `npi_number` (string): National Provider Identifier

**Request Body:**
```json
{
  "email_address": "staff@example.com",
  "first_name": "Mike",
  "last_name": "Wilson",
  "role": "nurse",
  "npi_number": "0987654321",
  "physician_uuid": "physician-uuid",
  "clinic_uuid": "clinic-uuid"
}
```

**Response:**
```json
{
  "message": "Staff member added successfully",
  "staff_uuid": "new-staff-uuid"
}
```

### PATCH /staff/edit-staff/{staff_uuid}
Edit staff member information.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Path Parameters:**
- `staff_uuid` (string): UUID of the staff member to edit

**Optional Parameters (all fields are optional for updates):**
- `email_address` (string): Valid email address
- `first_name` (string): Staff member's first name
- `last_name` (string): Staff member's last name
- `role` (string): Staff role
- `npi_number` (string): National Provider Identifier
- `physician_uuid` (string): UUID of associated physician
- `clinic_uuid` (string): UUID of associated clinic

**Request Body:**
```json
{
  "email_address": "new.email@example.com",
  "first_name": "Michael",
  "last_name": "Wilson",
  "role": "senior_nurse",
  "npi_number": "0987654321",
  "physician_uuid": "new-physician-uuid",
  "clinic_uuid": "new-clinic-uuid"
}
```

**Response:**
```json
{
  "message": "Staff member updated successfully",
  "staff_uuid": "staff-uuid"
}
```

### GET /staff/clinic-from-physician/{physician_uuid}
Get clinic UUID from physician UUID.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Path Parameters:**
- `physician_uuid` (string): UUID of the physician

**Response:**
```json
{
  "physician_uuid": "physician-uuid",
  "clinic_uuid": "clinic-uuid"
}
```

---

## Patient Dashboard

### GET /patient-dashboard/{patient_uuid}/conversations
Get patient conversation data within a date range.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Path Parameters:**
- `patient_uuid` (string): UUID of the patient

**Required Query Parameters:**
- `start_date` (date): Start date for the range (YYYY-MM-DD)
- `end_date` (date): End date for the range (YYYY-MM-DD)

**Response:**
```json
{
  "patient_uuid": "patient-uuid",
  "date_range_start": "2024-01-01",
  "date_range_end": "2024-01-31",
  "total_conversations": 5,
  "conversations": [
    {
      "conversation_uuid": "conversation-uuid",
      "conversation_date": "2024-01-15",
      "symptom_list": ["fatigue", "nausea", "pain"],
      "severity_list": {
        "fatigue": "3",
        "nausea": "2",
        "pain": "4"
      },
      "medication_list": [
        {
          "medicationName": "Ondansetron",
          "dosage": "4mg",
          "frequency": "twice daily"
        }
      ],
      "conversation_state": "COMPLETED",
      "overall_feeling": "moderate"
    }
  ]
}
```

### GET /patient-dashboard/{patient_uuid}/conversations/summary
Get summary statistics for patient conversations.

**Required Headers:**
- `Authorization: Bearer <jwt-token>`

**Required Path Parameters:**
- `patient_uuid` (string): UUID of the patient

**Required Query Parameters:**
- `start_date` (date): Start date for the range (YYYY-MM-DD)
- `end_date` (date): End date for the range (YYYY-MM-DD)

**Response:**
```json
{
  "patient_uuid": "patient-uuid",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "total_conversations": 5,
  "symptom_summary": {
    "total_unique_symptoms": 8,
    "top_symptoms": [
      ["fatigue", 4],
      ["nausea", 3],
      ["pain", 2]
    ],
    "average_severity_by_symptom": {
      "fatigue": 3.25,
      "nausea": 2.67,
      "pain": 4.0
    }
  },
  "medication_summary": {
    "total_unique_medications": 3,
    "top_medications": [
      ["Ondansetron", 3],
      ["Morphine", 2],
      ["Acetaminophen", 1]
    ]
  },
  "conversation_summary": {
    "states": {
      "COMPLETED": 4,
      "EMERGENCY": 1
    },
    "feelings": {
      "moderate": 3,
      "severe": 1,
      "mild": 1
    }
  }
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Access denied. Staff member not authorized for this physician/clinic combination."
}
```

**404 Not Found:**
```json
{
  "detail": "Patient not found"
}
```

**409 Conflict:**
```json
{
  "detail": "Patient with this MRN already exists"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Setup and Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database
- AWS Cognito User Pool
- Required environment variables

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/doctor_db
PATIENT_DATABASE_URL=postgresql://username:password@localhost:5432/patient_db

# AWS Cognito
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
```

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd doctor-api
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Dependencies

The API uses the following main dependencies:

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Boto3**: AWS SDK for Cognito integration
- **Pydantic**: Data validation and serialization
- **psycopg2-binary**: PostgreSQL adapter
- **python-jose**: JWT token handling

### API Documentation

Once the server is running, you can access:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

---

## Notes

- All timestamps are in UTC
- UUIDs are used for all entity identifiers
- The API supports pagination for list endpoints
- Authentication is required for all endpoints except health check and authentication routes
- Staff members can only access data within their associated clinic
- Patient data is filtered based on physician associations
