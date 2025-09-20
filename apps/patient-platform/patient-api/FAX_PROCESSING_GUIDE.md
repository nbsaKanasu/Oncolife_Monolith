# PDF Fax Processing for Patient Onboarding

This guide explains how to use the new `/auth/process-fax` endpoint to onboard patients from PDF fax documents.

## Overview

The system now supports automated patient onboarding through PDF fax processing. The workflow is:

1. **AI Processing**: Use GPT-4O vision to directly analyze the PDF and extract patient information
2. **Physician Lookup**: Find physician UUID from staff_profiles table
3. **Patient Creation**: Create Cognito account and database records
4. **Association**: Link patient with physician

## API Endpoint

### POST `/auth/process-fax`

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- File Parameter: `fax_file` (PDF file)

**Response:**
```json
{
  "message": "Patient email@example.com created successfully. A temporary password has been sent to their email.",
  "patient_email": "email@example.com",
  "patient_name": "John Doe",
  "physician_name": "Dr. Smith",
  "success": true,
  "errors": null
}
```

## Required Information in PDF

The AI system looks for these fields in the fax document:

1. **Patient Name** - Full name of the patient
2. **Patient Email** - Email address for account creation
3. **Physician Name** - Name of the attending physician

## Environment Variables

Make sure these environment variables are set:

- `OPENAI_API_KEY` - OpenAI API key for GPT-4O access
- `COGNITO_USER_POOL_ID` - AWS Cognito User Pool ID
- `COGNITO_CLIENT_ID` - AWS Cognito Client ID
- `COGNITO_CLIENT_SECRET` - AWS Cognito Client Secret (optional)

## Testing with cURL

```bash
curl -X POST "http://localhost:8000/auth/process-fax" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "fax_file=@path/to/patient_fax.pdf"
```

## Error Handling

The endpoint handles various error scenarios:

- **Invalid file type**: Only PDF files are accepted
- **Processing errors**: Issues with GPT-4O document analysis are handled gracefully
- **Missing fields**: If required information isn't found, detailed errors are returned
- **Duplicate patients**: Existing patients are detected and creation is skipped
- **Unknown physicians**: Falls back to default physician if not found in database

## Database Integration

### Tables Updated

1. **patient_info**: New patient record with extracted information
2. **patient_configurations**: Default configuration for new patient  
3. **patient_physician_associations**: Links patient with physician and clinic

### Default Values

- **Default Physician UUID**: `bea3fce0-42f9-4a00-ae56-4e2591ca17c5`
- **Default Clinic UUID**: `ab4dac8e-f9dc-4399-b9bd-781a9d540139`

## AWS Cognito Integration

The system creates a new user in AWS Cognito with:
- Username: Patient's email address
- Email verified: `true`
- Given name: Patient's first name
- Family name: Patient's last name
- Temporary password: Auto-generated and sent via email

## Logging

All operations are logged with prefixes:
- `[FAX]` - Main processing steps
- `[GPT4O]` - AI processing
- `[PHYSICIAN]` - Physician lookup
- `[AUTH]` - Cognito operations

## Future Enhancements

The current implementation extracts basic fields. Future versions could extract:
- Patient date of birth
- Medical record number (MRN)
- Disease type
- Treatment type
- Phone number
- Address information
