"""
Authentication Routes

This module provides authentication endpoints using AWS Cognito:

Routes:
- POST /auth/signup: Register a new user account with email, first name, and last name
- POST /auth/login: Authenticate user with email/password and return JWT tokens
- POST /auth/complete-new-password: Complete password setup for users with temporary passwords
- POST /auth/forgot-password: Send password reset code to user's email
- POST /auth/reset-password: Reset password using confirmation code from email
- POST /auth/logout: Client-side logout (formality endpoint)
- POST /auth/process-fax: Process PDF fax files to onboard patients using GPT-4O extraction
- DELETE /auth/delete-patient: Delete patient account and all associated data (testing only)

All routes handle Cognito integration and manage user data in the patient database.
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Request, BackgroundTasks
from sqlalchemy.orm import Session
from dotenv import load_dotenv, find_dotenv
import os
import boto3
from botocore.exceptions import ClientError
import logging
import hmac
import hashlib
import base64
from pydantic import BaseModel
from uuid import UUID
import openai
import json
import base64
import requests
from urllib.parse import urlparse
import re

# Use absolute imports from the 'backend' directory
from routers.auth.models import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    CompleteNewPasswordRequest,
    CompleteNewPasswordResponse,
    AuthTokens,
    DeletePatientRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ProcessFaxRequest,
    ProcessFaxResponse,
    UpdateSinchWebhookRequest,
)
# Import DB session and models
from db.database import get_patient_db, get_doctor_db
from db.patient_models import (
    PatientInfo,
    PatientConfigurations,
    PatientDiaryEntries,
    Conversations,
    Messages,
    PatientChemoDates,
    PatientPhysicianAssociations
)
from db.doctor_models import StaffProfiles
# Import shared dependencies
from routers.auth.dependencies import get_cognito_client, get_current_user, TokenData


class LogoutResponse(BaseModel):
    message: str
class ForceDeleteRequest(BaseModel):
    email: str



# Load environment variables (search up the tree for a .env)
try:
    dotenv_path = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path)
    if dotenv_path:
        logging.getLogger(__name__).info(f"[ENV] Loaded .env from {dotenv_path}")
    else:
        logging.getLogger(__name__).info("[ENV] No .env file found via find_dotenv")
except Exception:
    logging.getLogger(__name__).warning("[ENV] Failed to load .env via find_dotenv; proceeding with process env only")

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calculates the SecretHash for Cognito API calls."""
    msg = username + client_id
    dig = hmac.new(
        key=client_secret.encode("utf-8"),
        msg=msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()
def _decode_base64_payload(value: str) -> bytes:
    """Decode base64 payloads that may include a data URI prefix.

    Accepts strings like 'data:application/pdf;base64,AAA...' or plain base64.
    Performs lenient padding if missing.
    """
    try:
        if not isinstance(value, str):
            value = str(value)
        # Strip data URI prefix if present
        if "," in value and re.match(r"^data:.*;base64,", value[:40] if len(value) > 40 else value):
            value = value.split(",", 1)[1]
        # Remove whitespace
        value = re.sub(r"\s+", "", value)
        # Add padding if needed
        missing_padding = (-len(value)) % 4
        if missing_padding:
            value += "=" * missing_padding
        return base64.b64decode(value, validate=False)
    except Exception as e:
        raise e


def _extract_inline_and_url_from_payload(payload: dict) -> tuple[str | None, str | None]:
    """Heuristically locate inline base64 or a downloadable URL anywhere in the Sinch webhook payload.

    Searches common locations and key variants (e.g., file, fileUrl, downloadUrl, contentUrl, url, href),
    including nested objects like fax/media/attachments/files. Returns (inline_base64, url).
    """
    if not isinstance(payload, dict):
        return (None, None)

    # Priority key names
    inline_keys = {"file", "data", "content", "body"}
    url_keys = {"fileUrl", "file_url", "downloadUrl", "download_url", "contentUrl", "content_url", "url", "href"}

    def _first_inline(d: dict) -> str | None:
        for k in inline_keys:
            v = d.get(k)
            if isinstance(v, str) and len(v.strip()) > 0:
                return v
        return None

    def _first_url(d: dict) -> str | None:
        for k in url_keys:
            v = d.get(k)
            if isinstance(v, str) and v.startswith("http"):
                return v
        # Some APIs use nested 'links': {'download': '...'}
        links = d.get("links")
        if isinstance(links, dict):
            for v in links.values():
                if isinstance(v, str) and v.startswith("http"):
                    return v
        return None

    # Check top-level first
    inline = _first_inline(payload)
    url = _first_url(payload)
    if inline or url:
        return (inline, url)

    # Common nested containers
    containers = []
    for key in ("fax", "media", "document", "data"):
        c = payload.get(key)
        if isinstance(c, dict):
            containers.append(c)
        elif isinstance(c, list):
            containers.extend([i for i in c if isinstance(i, dict)])

    # Also check generic arrays that might contain file descriptors
    for key in ("attachments", "files", "pages", "items"):
        arr = payload.get(key)
        if isinstance(arr, list):
            containers.extend([i for i in arr if isinstance(i, dict)])

    # Search containers
    for c in containers:
        ci = _first_inline(c)
        cu = _first_url(c)
        if ci or cu:
            return (ci, cu)

    # Fallback: shallow recursive search up to limited depth
    def _walk(d: dict, depth: int = 0) -> tuple[str | None, str | None]:
        if depth > 3:
            return (None, None)
        ci = _first_inline(d)
        cu = _first_url(d)
        if ci or cu:
            return (ci, cu)
        for v in d.values():
            if isinstance(v, dict):
                r = _walk(v, depth + 1)
                if r[0] or r[1]:
                    return r
            elif isinstance(v, list):
                for i in v:
                    if isinstance(i, dict):
                        r = _walk(i, depth + 1)
                        if r[0] or r[1]:
                            return r
        return (None, None)

    return _walk(payload, 0)


def _process_pdf_with_gpt4o(pdf_file: UploadFile) -> dict:
    """Process the PDF fax document directly using GPT-4O vision to extract patient information."""
    try:
        # Read the PDF file content
        content = pdf_file.file.read()
        pdf_file.file.seek(0)  # Reset file pointer
        
        # Encode PDF to base64
        pdf_base64 = base64.b64encode(content).decode('utf-8')
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = """
You are a medical document processing assistant. Analyze this PDF fax document and extract the following information:

1. Patient Name (full name)
2. Patient Email (if available)
3. Physician Name (doctor's name)

Return the information in JSON format with these exact keys:
- "patient_name": string (full name)
- "patient_email": string or null (if not found)
- "physician_name": string (doctor's name)

If any field is not found or unclear, use null for that field.
        """.strip()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a medical document processing assistant that extracts structured data from fax documents."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse the JSON response
        result_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            logger.error(f"[GPT4O] Failed to parse JSON response: {result_text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to parse AI response"
            )
            
    except Exception as e:
        logger.error(f"[GPT4O] Failed to process PDF with GPT-4O: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document with AI: {str(e)}"
        )


def _process_pdf_bytes_with_ocr_llm(pdf_bytes: bytes) -> dict:
    """Process raw PDF bytes using OCR + LLM to extract patient information."""
    try:
        import io
        from pdf2image import convert_from_bytes
        import pytesseract
        
        logger.info("[OCR] Converting PDF to images")
        # Convert PDF to images (first page only for fax documents)
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=300)
        if not images:
            raise Exception("Failed to convert PDF to images")
        
        # Extract text using OCR
        logger.info("[OCR] Extracting text from image")
        image = images[0]
        extracted_text = pytesseract.image_to_string(image, config='--psm 6')
        logger.info(f"[OCR] Extracted text length: {len(extracted_text)} chars")
        logger.info(f"[OCR] Text preview: {extracted_text[:200]}...")

        # Use a simpler LLM (like GPT-3.5) to process the text
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
You are a medical document processing assistant. Analyze this extracted text from a fax document and extract the following information:

TEXT FROM DOCUMENT:
{extracted_text}

Extract:
1. Patient Name (full name)
2. Patient Email (if available)
3. Physician Name (doctor's name)

Return ONLY a JSON object with these exact keys:
- "patient_name": string (full name) or null
- "patient_email": string or null
- "physician_name": string (doctor's name) or null

If any field is not found or unclear, use null for that field.
        """.strip()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical document processing assistant that extracts structured data from text. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=300,
            timeout=30  # 30 second timeout
        )

        # Parse the JSON response
        result_text = response.choices[0].message.content.strip()
        logger.info(f"[LLM] Raw response: {result_text}")

        # Try to extract JSON from the response
        try:
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            logger.error(f"[LLM] Failed to parse JSON response: {result_text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to parse AI response"
            )

    except Exception as e:
        logger.error(f"[OCR+LLM] Failed to process PDF bytes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document with OCR+LLM: {str(e)}"
        )


def _is_pdf_bytes(data: bytes) -> bool:
    try:
        return data.startswith(b"%PDF")
    except Exception:
        return False


def _is_tiff_bytes(data: bytes) -> bool:
    try:
        # TIFF magic numbers: II*\x00 (little-endian) or MM\x00* (big-endian)
        return data[:4] in (b"II*\x00", b"MM\x00*")
    except Exception:
        return False


def _process_document_bytes_with_ocr_llm(doc_bytes: bytes) -> dict:
    """Process fax bytes (PDF or TIFF/image) using OCR + LLM to extract fields.

    - If PDF, render first page via pdf2image.
    - If TIFF or other image, open with Pillow and use the first frame.
    """
    try:
        import io
        from pdf2image import convert_from_bytes
        from PIL import Image
        import pytesseract

        images = []
        if _is_pdf_bytes(doc_bytes):
            logger.info("[OCR] Detected PDF; converting first page to image")
            images = convert_from_bytes(doc_bytes, first_page=1, last_page=1, dpi=300)
        else:
            # Try to open as image (TIFF, PNG, JPG, etc.)
            logger.info("[OCR] Non-PDF detected; attempting to open as image (TIFF/PNG/JPG)")
            try:
                img = Image.open(io.BytesIO(doc_bytes))
                # Seek to first frame if multi-page TIFF
                try:
                    if getattr(img, "n_frames", 1) > 0:
                        img.seek(0)
                except Exception:
                    pass
                images = [img.convert("RGB")]
            except Exception as e:
                logger.error(f"[OCR] Unsupported or invalid image bytes: {str(e)}")
                raise HTTPException(status_code=400, detail="Unsupported fax file type; expected PDF or TIFF/image")

        if not images:
            raise Exception("Failed to obtain an image frame from document")

        logger.info("[OCR] Extracting text from image")
        image = images[0]
        extracted_text = pytesseract.image_to_string(image, config='--psm 6')
        logger.info(f"[OCR] Extracted text length: {len(extracted_text)} chars")
        logger.info(f"[OCR] Text preview: {extracted_text[:200]}...")

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
You are a medical document processing assistant. Analyze this extracted text from a fax document and extract the following information:

TEXT FROM DOCUMENT:
{extracted_text}

Extract:
1. Patient Name (full name)
2. Patient Email (if available)
3. Physician Name (doctor's name)

Return ONLY a JSON object with these exact keys:
- "patient_name": string (full name) or null
- "patient_email": string or null
- "physician_name": string (doctor's name) or null

If any field is not found or unclear, use null for that field.
        """.strip()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical document processing assistant that extracts structured data from text. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=300,
            timeout=30
        )

        result_text = response.choices[0].message.content.strip()
        logger.info(f"[LLM] Raw response: {result_text}")

        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            logger.error(f"[LLM] Failed to parse JSON response: {result_text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to parse AI response"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OCR+LLM] Failed to process document bytes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document with OCR+LLM: {str(e)}"
        )

def _find_physician_by_name(physician_name: str, doctor_db: Session) -> str:
    """Find physician UUID by name in the staff_profiles table."""
    try:
        # Clean up the physician name
        physician_name = physician_name.strip()
        
        # Try to find physician by exact name match (first + last name)
        physician = doctor_db.query(StaffProfiles).filter(
            StaffProfiles.role == 'physician'
        ).all()
        
        # Search through all physicians to find the best match
        for staff in physician:
            full_name = f"{staff.first_name} {staff.last_name}".strip()
            if physician_name.lower() in full_name.lower() or full_name.lower() in physician_name.lower():
                logger.info(f"[PHYSICIAN] Found physician match: {full_name} -> {staff.staff_uuid}")
                return str(staff.staff_uuid)
        
        # If no match found, log warning and return default
        logger.warning(f"[PHYSICIAN] No physician found for name: {physician_name}")
        return None
        
    except Exception as e:
        logger.error(f"[PHYSICIAN] Error finding physician by name '{physician_name}': {str(e)}")
        return None


def _download_file_with_basic_auth(file_url: str, key: str, secret: str) -> bytes:
    """Download a binary file from a URL using HTTP Basic Auth and return raw bytes."""
    try:
        resp = requests.get(file_url, auth=(key, secret), timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"[SINCH] Failed to download file from URL: {file_url} error={str(e)}")
        raise HTTPException(status_code=400, detail="Failed to download fax content from Sinch")


def _create_patient_from_fax_data(
    patient_data: dict, 
    physician_uuid: str, 
    patient_db: Session, 
    doctor_db: Session
) -> dict:
    """Create patient in database and Cognito based on fax data."""
    try:
        patient_name = patient_data.get("patient_name", "")
        patient_email = patient_data.get("patient_email")
        
        if not patient_name:
            raise HTTPException(
                status_code=400,
                detail="Patient name is required"
            )
        
        if not patient_email:
            raise HTTPException(
                status_code=400,
                detail="Patient email is required for account creation"
            )
        
        # Parse patient name into first and last name
        name_parts = patient_name.strip().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:])
        else:
            first_name = patient_name
            last_name = ""
        
        # Check if patient already exists
        existing_patient = patient_db.query(PatientInfo).filter(
            PatientInfo.email_address == patient_email,
            PatientInfo.is_deleted == False
        ).first()
        
        if existing_patient:
            logger.warning(f"[FAX] Patient already exists: {patient_email}")
            return {
                "success": False,
                "message": f"Patient with email {patient_email} already exists",
                "patient_email": patient_email
            }
        
        # Create signup request to reuse existing logic
        signup_request = SignupRequest(
            email=patient_email,
            first_name=first_name,
            last_name=last_name,
            physician_email=None  # We'll use UUID directly
        )
        
        # Create user in Cognito (similar to signup endpoint)
        user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        if not user_pool_id:
            raise HTTPException(
                status_code=500, 
                detail="COGNITO_USER_POOL_ID not configured"
            )
        
        cognito_client = get_cognito_client()
        
        user_attributes = [
            {"Name": "email", "Value": patient_email},
            {"Name": "email_verified", "Value": "true"},
            {"Name": "given_name", "Value": first_name},
            {"Name": "family_name", "Value": last_name},
        ]
        
        logger.info(f"[FAX] Creating Cognito user for {patient_email}")
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=patient_email,
            UserAttributes=user_attributes,
            ForceAliasCreation=False,
        )
        logger.info(f"[FAX] Cognito user created successfully")
        
        # Extract the UUID (sub) from Cognito response
        user_sub = None
        for attribute in response["User"]["Attributes"]:
            if attribute["Name"] == "sub":
                user_sub = attribute["Value"]
                break
        
        if not user_sub:
            raise HTTPException(
                status_code=500, 
                detail="User created in Cognito, but failed to retrieve UUID."
            )
        
        # Create database records
        new_patient_info = PatientInfo(
            uuid=user_sub,
            email_address=patient_email,
            first_name=first_name,
            last_name=last_name,
        )
        new_patient_config = PatientConfigurations(uuid=user_sub)
        
        logger.info(f"[FAX] Adding patient records to database")
        patient_db.add(new_patient_info)
        patient_db.add(new_patient_config)
        
        # Associate with physician
        default_clinic_uuid = 'ab4dac8e-f9dc-4399-b9bd-781a9d540139'
        
        new_association = PatientPhysicianAssociations(
            patient_uuid=user_sub,
            physician_uuid=physician_uuid,
            clinic_uuid=default_clinic_uuid
        )
        patient_db.add(new_association)
        
        logger.info(f"[FAX] Committing database transaction")
        patient_db.commit()
        logger.info(f"[FAX] Database commit successful")
        
        logger.info(f"[FAX] Successfully created patient: {patient_email} with physician: {physician_uuid}")
        
        return {
            "success": True,
            "message": f"Patient {patient_email} created successfully. A temporary password has been sent to their email.",
            "patient_email": patient_email,
            "patient_uuid": user_sub
        }
        
    except Exception as e:
        patient_db.rollback()
        logger.error(f"[FAX] Failed to create patient from fax data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create patient account: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """
    Client-side logout. The real action is the client deleting the token.
    This endpoint is a formality.
    """
    logger.info("[AUTH] /logout called")
    return {"message": "Logout successful"}


@router.post("/signup", response_model=SignupResponse)
async def signup_user(
    request: SignupRequest,
    patient_db: Session = Depends(get_patient_db),
    doctor_db: Session = Depends(get_doctor_db)
):
    """
    Create a new user in AWS Cognito User Pool.
    On success, also creates corresponding records in the patient_info
    and patient_configurations tables.
    If a physician_email is provided, it links the patient to the physician.
    """
    logger.info(f"[AUTH] /signup email={request.email} physician_email={getattr(request, 'physician_email', None)}")
    # Check if a non-deleted user with this email already exists in the local DB
    existing_patient = patient_db.query(PatientInfo).filter(
        PatientInfo.email_address == request.email,
        PatientInfo.is_deleted == False
    ).first()

    if existing_patient:
        logger.warning(f"[AUTH] /signup conflict email={request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A user with email {request.email} already exists and is active."
        )

    try:
        user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        if not user_pool_id:
            logger.error("[AUTH] /signup missing COGNITO_USER_POOL_ID")
            raise HTTPException(
                status_code=500, detail="COGNITO_USER_POOL_ID not configured"
            )

        cognito_client = get_cognito_client()

        user_attributes = [
            {"Name": "email", "Value": request.email},
            {"Name": "email_verified", "Value": "true"},
            {"Name": "given_name", "Value": request.first_name},
            {"Name": "family_name", "Value": request.last_name},
        ]

        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=request.email,
            UserAttributes=user_attributes,
            ForceAliasCreation=False,
        )
        logger.info(f"[AUTH] /signup created in Cognito email={request.email}")

        # Extract the UUID (sub) that Cognito automatically generates
        user_sub = None
        for attribute in response["User"]["Attributes"]:
            if attribute["Name"] == "sub":
                user_sub = attribute["Value"]
                break
        
        if not user_sub:
            logger.error(f"[AUTH] /signup missing sub in Cognito response email={request.email}")
            raise HTTPException(status_code=500, detail="User created in Cognito, but failed to retrieve UUID.")

        logger.info(
            f"[AUTH] /signup success email={request.email} uuid={user_sub}"
        )

        # Now, create the corresponding records in our own database
        new_patient_info = PatientInfo(
            uuid=user_sub,
            email_address=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        new_patient_config = PatientConfigurations(uuid=user_sub)

        patient_db.add(new_patient_info)
        patient_db.add(new_patient_config)

        # Step 3: Associate a physician for all new patients
        # Prefer the physician by email if provided; otherwise use the default UUID
        default_physician_uuid = 'bea3fce0-42f9-4a00-ae56-4e2591ca17c5'
        default_clinic_uuid = 'ab4dac8e-f9dc-4399-b9bd-781a9d540139'
        associated_physician_uuid = None

        if request.physician_email:
            physician_profile = doctor_db.query(StaffProfiles).filter(
                StaffProfiles.email_address == request.physician_email,
                StaffProfiles.role == 'physician'
            ).first()

            if physician_profile:
                associated_physician_uuid = physician_profile.staff_uuid
            else:
                logger.warning(
                    f"[AUTH] /signup physician email not found '{request.physician_email}', falling back to default physician"
                )

        if not associated_physician_uuid:
            associated_physician_uuid = default_physician_uuid

        new_association = PatientPhysicianAssociations(
            patient_uuid=user_sub,
            physician_uuid=associated_physician_uuid,
            clinic_uuid=default_clinic_uuid
        )
        patient_db.add(new_association)
        
        patient_db.commit()
        logger.info(f"[AUTH] /signup DB records created uuid={user_sub}")

        return SignupResponse(
            message=f"User {request.email} created successfully. A temporary password has been sent to their email.",
            email=request.email,
            user_status=response["User"]["UserStatus"],
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"[AUTH] /signup Cognito error code={error_code} message='{error_message}' email={request.email}")
        raise HTTPException(
            status_code=500, detail=f"AWS Cognito error: {error_message}"
        )
    except Exception as e:
        logger.error(f"[AUTH] /signup unexpected error email={request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=LoginResponse)
async def validate_login(request: LoginRequest):
    """
    Validate if a user's email and password is valid for login.
    If a temporary password is used, it returns a session token for the password change flow.
    """
    logger.info(f"[AUTH] /login email={request.email}")
    try:
        user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        client_id = os.getenv("COGNITO_CLIENT_ID")
        client_secret = os.getenv("COGNITO_CLIENT_SECRET")

        if not user_pool_id or not client_id:
            logger.error("[AUTH] /login missing Cognito envs")
            raise HTTPException(
                status_code=500,
                detail="COGNITO_USER_POOL_ID or COGNITO_CLIENT_ID not configured",
            )

        cognito_client = get_cognito_client()

        auth_parameters = {"USERNAME": request.email, "PASSWORD": request.password}

        if client_secret:
            auth_parameters["SECRET_HASH"] = _get_secret_hash(
                request.email, client_id, client_secret
            )

        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters=auth_parameters,
        )

        logger.info(f"[AUTH] /login Cognito response keys={list(auth_response.keys())}")

        if "AuthenticationResult" in auth_response:
            logger.info(f"[AUTH] /login success email={request.email}")
            auth_result = auth_response["AuthenticationResult"]
            tokens = AuthTokens(
                access_token=auth_result["AccessToken"],
                refresh_token=auth_result["RefreshToken"],
                id_token=auth_result["IdToken"],
                token_type=auth_result["TokenType"],
            )
            return LoginResponse(
                valid=True,
                message="Login credentials are valid",
                user_status="CONFIRMED",
                tokens=tokens
            )

        elif "ChallengeName" in auth_response:
            challenge_name = auth_response["ChallengeName"]
            session = auth_response.get("Session")
            logger.info(f"[AUTH] /login challenge email={request.email} name={challenge_name}")

            if challenge_name == "NEW_PASSWORD_REQUIRED":
                return LoginResponse(
                    valid=True,
                    message="Login credentials are valid but password change is required.",
                    user_status="FORCE_CHANGE_PASSWORD",
                    session=session,
                )
            else:
                return LoginResponse(
                    valid=True,
                    message=f"Login credentials are valid but challenge required: {challenge_name}",
                    user_status="CHALLENGE_REQUIRED",
                    session=session,
                )
        else:
            logger.warning(f"[AUTH] /login unexpected response email={request.email}")
            return LoginResponse(valid=False, message="Unexpected authentication response")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"[AUTH] /login Cognito error email={request.email} code={error_code} msg='{error_message}'")
        if error_code == "NotAuthorizedException":
            return LoginResponse(valid=False, message="Invalid email or password")
        elif error_code == "UserNotFoundException":
            return LoginResponse(valid=False, message="User not found")
        else:
            raise HTTPException(
                status_code=500, detail=f"AWS Cognito error: {error_message}"
            )
    except Exception as e:
        logger.error(f"[AUTH] /login unexpected error email={request.email}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/complete-new-password", response_model=CompleteNewPasswordResponse)
async def complete_new_password(request: CompleteNewPasswordRequest):
    """
    Complete the new password setup for a user who was created with a temporary password.
    """
    logger.info(f"[AUTH] /complete-new-password email={request.email}")
    try:
        user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        client_id = os.getenv("COGNITO_CLIENT_ID")
        client_secret = os.getenv("COGNITO_CLIENT_SECRET")

        if not user_pool_id or not client_id:
            logger.error("[AUTH] /complete-new-password missing Cognito envs")
            raise HTTPException(
                status_code=500,
                detail="COGNITO_USER_POOL_ID or COGNITO_CLIENT_ID not configured",
            )

        cognito_client = get_cognito_client()

        challenge_responses = {
            "USERNAME": request.email,
            "NEW_PASSWORD": request.new_password,
        }

        if client_secret:
            challenge_responses["SECRET_HASH"] = _get_secret_hash(
                request.email, client_id, client_secret
            )

        response = cognito_client.admin_respond_to_auth_challenge(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            ChallengeName="NEW_PASSWORD_REQUIRED",
            Session=request.session,
            ChallengeResponses=challenge_responses,
        )

        if "AuthenticationResult" in response:
            logger.info(f"[AUTH] /complete-new-password success email={request.email}")
            auth_result = response["AuthenticationResult"]
            tokens = AuthTokens(
                access_token=auth_result["AccessToken"],
                refresh_token=auth_result["RefreshToken"],
                id_token=auth_result["IdToken"],
                token_type=auth_result["TokenType"],
            )
            return CompleteNewPasswordResponse(
                message="Password successfully changed and user authenticated.",
                tokens=tokens,
            )
        else:
            logger.error(f"[AUTH] /complete-new-password unexpected response email={request.email}")
            raise HTTPException(
                status_code=400,
                detail="Could not set new password. Unexpected response from authentication service.",
            )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(
            f"[AUTH] /complete-new-password Cognito error email={request.email} code={error_code} msg='{error_message}'"
        )
        if error_code in [
            "NotAuthorizedException",
            "CodeMismatchException",
            "ExpiredCodeException",
        ]:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired session. Please try logging in again.",
            )
        if error_code == "InvalidPasswordException":
            raise HTTPException(
                status_code=400,
                detail=f"New password does not meet requirements: {error_message}",
            )
        raise HTTPException(
            status_code=500, detail=f"AWS Cognito error: {error_message}"
        )

    except Exception as e:
        logger.error(
            f"[AUTH] /complete-new-password unexpected error email={request.email}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send a password reset code to the user's email via AWS Cognito.
    This initiates the password reset flow.
    """
    logger.info(f"[AUTH] /forgot-password email={request.email}")
    try:
        client_id = os.getenv("COGNITO_CLIENT_ID")
        client_secret = os.getenv("COGNITO_CLIENT_SECRET")

        if not client_id:
            logger.error("[AUTH] /forgot-password missing COGNITO_CLIENT_ID")
            raise HTTPException(
                status_code=500,
                detail="COGNITO_CLIENT_ID not configured",
            )

        cognito_client = get_cognito_client()

        # Prepare the request parameters
        params = {
            "ClientId": client_id,
            "Username": request.email,
        }

        # Add SecretHash if client secret is configured
        if client_secret:
            params["SecretHash"] = _get_secret_hash(
                request.email, client_id, client_secret
            )

        # Initiate the forgot password flow
        cognito_client.forgot_password(**params)

        logger.info(f"[AUTH] /forgot-password success email={request.email}")
        return ForgotPasswordResponse(
            message="Password reset code sent to your email address",
            email=request.email
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"[AUTH] /forgot-password Cognito error email={request.email} code={error_code} msg='{error_message}'")

        if error_code == "UserNotFoundException":
            # For security, we don't reveal if the user exists or not
            logger.info(f"[AUTH] /forgot-password user not found email={request.email}")
            return ForgotPasswordResponse(
                message="If an account with this email exists, a password reset code has been sent",
                email=request.email
            )
        elif error_code == "LimitExceededException":
            raise HTTPException(
                status_code=429,
                detail="Too many password reset attempts. Please wait before trying again."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to initiate password reset: {error_message}"
            )

    except Exception as e:
        logger.error(f"[AUTH] /forgot-password unexpected error email={request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset the user's password using the confirmation code sent to their email.
    This completes the password reset flow initiated by forgot-password.
    """
    logger.info(f"[AUTH] /reset-password email={request.email}")
    try:
        client_id = os.getenv("COGNITO_CLIENT_ID")
        client_secret = os.getenv("COGNITO_CLIENT_SECRET")

        if not client_id:
            logger.error("[AUTH] /reset-password missing COGNITO_CLIENT_ID")
            raise HTTPException(
                status_code=500,
                detail="COGNITO_CLIENT_ID not configured",
            )

        cognito_client = get_cognito_client()

        # Prepare the request parameters
        params = {
            "ClientId": client_id,
            "Username": request.email,
            "ConfirmationCode": request.confirmation_code,
            "Password": request.new_password,
        }

        # Add SecretHash if client secret is configured
        if client_secret:
            params["SecretHash"] = _get_secret_hash(
                request.email, client_id, client_secret
            )

        # Confirm the password reset
        cognito_client.confirm_forgot_password(**params)

        logger.info(f"[AUTH] /reset-password success email={request.email}")
        return ResetPasswordResponse(
            message="Password has been successfully reset. You can now log in with your new password.",
            email=request.email
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"[AUTH] /reset-password Cognito error email={request.email} code={error_code} msg='{error_message}'")

        if error_code == "CodeMismatchException":
            raise HTTPException(
                status_code=400,
                detail="Invalid confirmation code. Please check the code and try again."
            )
        elif error_code == "ExpiredCodeException":
            raise HTTPException(
                status_code=400,
                detail="Confirmation code has expired. Please request a new password reset."
            )
        elif error_code == "UserNotFoundException":
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )
        elif error_code == "InvalidPasswordException":
            raise HTTPException(
                status_code=400,
                detail=f"New password does not meet requirements: {error_message}"
            )
        elif error_code == "LimitExceededException":
            raise HTTPException(
                status_code=429,
                detail="Too many password reset attempts. Please wait before trying again."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to reset password: {error_message}"
            )

    except Exception as e:
        logger.error(f"[AUTH] /reset-password unexpected error email={request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/delete-patient", status_code=status.HTTP_204_NO_CONTENT, summary="Delete patient account")
async def delete_patient(
    request: DeletePatientRequest,
    db: Session = Depends(get_patient_db)
):
    """
    Deletes all data for the specified user from the application database.
    Can delete by email or UUID. Optionally skips AWS Cognito deletion.
    This is an irreversible action.
    """
    # Validate that either email or UUID is provided
    if not request.email and not request.uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or uuid must be provided"
        )
    
    # Find the user(s) by email or UUID
    user_ids = []
    user_email_for_aws = None
    if request.uuid:
        try:
            patient_uuid = UUID(request.uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format"
            )
        patient_info = db.query(PatientInfo).filter(PatientInfo.uuid == patient_uuid).first()
        if not patient_info:
            logger.error(f"[AUTH] /delete-patient patient not found identifier={request.uuid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Patient not found with identifier: {request.uuid}"
            )
        user_ids = [patient_info.uuid]
        user_email_for_aws = patient_info.email_address
        logger.warning(f"[AUTH] /delete-patient start uuid={request.uuid}")
    else:
        patient_infos = db.query(PatientInfo).filter(PatientInfo.email_address == request.email).all()
        logger.warning(f"[AUTH] /delete-patient start email={request.email} count={len(patient_infos)}")
        if not patient_infos:
            logger.error(f"[AUTH] /delete-patient patient not found identifier={request.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Patient not found with identifier: {request.email}"
            )
        user_ids = [p.uuid for p in patient_infos]
        user_email_for_aws = request.email

    # --- Step 1: Soft-delete all related data in the database for ALL matching user IDs ---
    try:
        # Remove diary entries (no is_deleted column on this table)
        db.query(PatientDiaryEntries).filter(PatientDiaryEntries.patient_uuid.in_(user_ids)).delete(synchronize_session=False)
        # Remove chemo dates (no is_deleted column on this table)
        db.query(PatientChemoDates).filter(PatientChemoDates.patient_uuid.in_(user_ids)).delete(synchronize_session=False)
        # Delete conversations and their messages (neither table has is_deleted)
        sub_conv_uuids = db.query(Conversations.uuid).filter(Conversations.patient_uuid.in_(user_ids)).subquery()
        db.query(Messages).filter(Messages.chat_uuid.in_(sub_conv_uuids)).delete(synchronize_session=False)
        db.query(Conversations).filter(Conversations.patient_uuid.in_(user_ids)).delete(synchronize_session=False)
        # Soft delete associations and configs and info (these tables have is_deleted)
        db.query(PatientPhysicianAssociations).filter(PatientPhysicianAssociations.patient_uuid.in_(user_ids)).update({"is_deleted": True}, synchronize_session=False)
        db.query(PatientConfigurations).filter(PatientConfigurations.uuid.in_(user_ids)).update({"is_deleted": True}, synchronize_session=False)
        db.query(PatientInfo).filter(PatientInfo.uuid.in_(user_ids)).update({"is_deleted": True}, synchronize_session=False)
        # Commit DB changes before attempting AWS deletion
        db.commit()
        logger.info(f"[AUTH] /delete-patient DB records processed for user_ids={list(map(str, user_ids))}")
    except Exception as e:
        db.rollback()
        logger.error(f"[AUTH] /delete-patient DB cleanup failed user_ids={list(map(str, user_ids))} error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete user data. Please try again.")

    # --- Step 2: Delete the user from Cognito (unless skipped) ---
    if not request.skip_aws:
        try:
            cognito_client = get_cognito_client()
            cognito_client.admin_delete_user(
                UserPoolId=os.getenv("COGNITO_USER_POOL_ID"),
                Username=user_email_for_aws
            )
            logger.info(f"[AUTH] /delete-patient deleted from Cognito email={user_email_for_aws}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == "UserNotFoundException":
                logger.info(f"[AUTH] /delete-patient Cognito user not found for email={user_email_for_aws}; proceeding without error")
            else:
                logger.error(f"[AUTH] /delete-patient Cognito delete failed email={user_email_for_aws} code={error_code} msg='{error_message}'")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user from authentication service.")
    else:
        logger.info(f"[AUTH] /delete-patient skipped AWS Cognito deletion for email={user_email_for_aws}")
    
    logger.warning(f"[AUTH] /delete-patient complete user_ids={list(map(str, user_ids))} email={user_email_for_aws}")
    
    return


@router.post("/process-fax", response_model=ProcessFaxResponse)
async def process_fax(
    fax_file: UploadFile = File(...),
    patient_db: Session = Depends(get_patient_db),
    doctor_db: Session = Depends(get_doctor_db)
):
    """
    Process a PDF fax file to onboard a new patient.
    
    This endpoint:
    1. Uses GPT-4O vision to directly analyze the PDF and extract patient name, email, and physician name
    2. Finds the physician UUID from the staff_profiles table
    3. Creates a new patient account in Cognito
    4. Inserts patient records into the database
    5. Associates the patient with the physician
    """
    logger.info(f"[FAX] Processing fax file: {fax_file.filename}")
    
    # Validate file type
    if not fax_file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    

@router.post("/admin/force-soft-delete")
async def force_soft_delete(
    payload: ForceDeleteRequest,
    db: Session = Depends(get_patient_db)
):
    """Admin helper: force soft-delete a patient and related records by email only (no AWS)."""
    try:
        patient_info = db.query(PatientInfo).filter(PatientInfo.email_address == payload.email).first()
        if not patient_info:
            raise HTTPException(status_code=404, detail=f"Patient not found with email: {payload.email}")

        user_id = patient_info.uuid
        # Remove diary entries (no is_deleted column on this table)
        db.query(PatientDiaryEntries).filter(PatientDiaryEntries.patient_uuid == user_id).delete(synchronize_session=False)
        # Soft delete associations and configs and info (these tables have is_deleted)
        db.query(PatientPhysicianAssociations).filter(PatientPhysicianAssociations.patient_uuid == user_id).update({"is_deleted": True})
        db.query(PatientConfigurations).filter(PatientConfigurations.uuid == user_id).update({"is_deleted": True})
        db.query(PatientInfo).filter(PatientInfo.uuid == user_id).update({"is_deleted": True})
        db.commit()
        return {"status": "ok", "email": payload.email, "uuid": str(user_id)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[ADMIN] force-soft-delete failed email={payload.email} error={e}")
        raise HTTPException(status_code=500, detail="Force soft delete failed")

@router.post("/fax-webhook/sinch")
async def sinch_fax_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Sinch Incoming Fax webhook handler.
    Expects JSON payload with fields including 'event' and 'file' (base64 PDF) or 'fileUrl'.
    """
    client_host = request.client.host if getattr(request, "client", None) else "unknown"
    content_type = request.headers.get("content-type", "?")
    logger.info(f"[SINCH] Webhook received from {client_host} content_type={content_type}")

    body = None
    # Try JSON first
    try:
        body = await request.json()
        logger.info(f"[SINCH] Parsed JSON payload keys={list(body.keys())}")
    except Exception:
        # Try form/multipart
        try:
            form = await request.form()
            body = dict(form)
            logger.info(f"[SINCH] Parsed FORM payload keys={list(body.keys())}")
        except Exception:
            # Fallback to raw body for visibility
            raw = await request.body()
            logger.warning(f"[SINCH] Unable to parse body; raw_len={len(raw)}")
            return {"status": "received", "parsed": False}

    event_type = body.get("event")
    logger.info(f"[SINCH] Event={event_type} has_file={'file' in body} has_fileUrl={'fileUrl' in body}")
    if not event_type:
        # Be lenient with webhook payloads: log and ack instead of erroring
        logger.warning("[SINCH] Missing 'event' in webhook payload; acknowledging without processing")
        return {"status": "ack", "event": None}

    if event_type != "INCOMING_FAX":
        # Outbound status callbacks or other events
        logger.info(f"[SINCH] Non-incoming event received: {event_type}")
        return {"status": "ack", "event": event_type}

    # Queue the heavy work so we can ACK immediately to Sinch
    try:
        background_tasks.add_task(_process_incoming_fax_async, body)
        logger.info("[SINCH] Incoming fax accepted for async processing")
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"[SINCH] Failed to enqueue async processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to accept fax for processing")


def _process_incoming_fax_async(body: dict) -> None:
    """Process an incoming fax payload asynchronously (own DB sessions)."""
    # Open DB sessions locally
    patient_db: Session = next(get_patient_db())
    doctor_db: Session = next(get_doctor_db())
    try:
        logger.info("[SINCH][ASYNC] Starting async processing of incoming fax")
        # Obtain document bytes from inline base64 or a file URL (search broadly)
        inline_guess, url_guess = _extract_inline_and_url_from_payload(body)

        doc_bytes: bytes = b""
        if isinstance(inline_guess, str) and inline_guess.strip():
            try:
                logger.info(f"[SINCH][ASYNC] Attempting inline base64 decode length={len(inline_guess)}")
                doc_bytes = _decode_base64_payload(inline_guess)
                logger.info(f"[SINCH][ASYNC] Decoded inline bytes size={len(doc_bytes)}")
            except Exception as e:
                logger.warning(f"[SINCH][ASYNC] Inline base64 decode failed: {str(e)}; will try fileUrl if present")
                doc_bytes = b""

        if not doc_bytes and url_guess:
            sinch_key = (
                os.getenv("SINCH_FAX_KEY") or os.getenv("SINCH_KEY") or os.getenv("SINCH_KEY_ID")
            )
            sinch_secret = (
                os.getenv("SINCH_FAX_SECRET") or os.getenv("SINCH_SECRET") or os.getenv("SINCH_KEY_SECRET")
            )
            if not sinch_key or not sinch_secret:
                logger.error("[SINCH][ASYNC] Missing SINCH credentials for file download")
                return
            try:
                host = urlparse(url_guess).netloc
            except Exception:
                host = "unknown"
            logger.info(f"[SINCH][ASYNC] Downloading file from fileUrl host={host}")
            doc_bytes = _download_file_with_basic_auth(url_guess, sinch_key, sinch_secret)
            logger.info(f"[SINCH][ASYNC] Downloaded file bytes size={len(doc_bytes)}")

        if not doc_bytes:
            logger.error("[SINCH][ASYNC] No usable 'file' or 'fileUrl' content; skipping")
            return

        # Extract fields via OCR + LLM
        logger.info("[SINCH][ASYNC] Starting OCR + LLM extraction")
        extracted_data = _process_document_bytes_with_ocr_llm(doc_bytes)
        patient_name = extracted_data.get("patient_name")
        patient_email = extracted_data.get("patient_email")
        physician_name = extracted_data.get("physician_name")
        logger.info(f"[SINCH][ASYNC] Extraction result name={patient_name} email={patient_email} physician={physician_name}")
        
        # Validate
        errors = []
        if not patient_name:
            errors.append("Patient name not found in document")
        if not patient_email:
            errors.append("Patient email not found in document")
        if not physician_name:
            errors.append("Physician name not found in document")
        if errors:
            logger.warning(f"[SINCH][ASYNC] Extraction errors: {errors}")
            return

        # Resolve physician UUID
        logger.info("[SINCH][ASYNC] Resolving physician UUID")
        physician_uuid = _find_physician_by_name(physician_name, doctor_db)
        if not physician_uuid:
            default_physician_uuid = 'bea3fce0-42f9-4a00-ae56-4e2591ca17c5'
            physician_uuid = default_physician_uuid
            logger.warning(f"[SINCH][ASYNC] Physician not found; using default {default_physician_uuid}")

        # Create patient and associations
        logger.info("[SINCH][ASYNC] Creating patient and associations")
        creation_result = _create_patient_from_fax_data(
            extracted_data,
            physician_uuid,
            patient_db,
            doctor_db
        )
        if not creation_result.get("success"):
            logger.warning(f"[SINCH][ASYNC] Patient creation not successful: {creation_result}")
            return
        logger.info(f"[SINCH][ASYNC] Fax processed successfully for email={patient_email}")
    except Exception as e:
        logger.error(f"[SINCH][ASYNC] Unexpected error: {str(e)}")
    finally:
        try:
            patient_db.close()
        except Exception:
            pass
        try:
            doctor_db.close()
        except Exception:
            pass
    # End async processing


@router.post("/sinch/update-webhook")
async def update_sinch_webhook(body: UpdateSinchWebhookRequest):
    """
    Updates the Sinch Fax service incoming webhook URL.
    Provide body.url or set env SINCH_WEBHOOK_URL. Requires SINCH_FAX_KEY/SECRET, SINCH_FAX_PROJECT_ID, SINCH_FAX_SERVICE_ID.
    """
    key = os.getenv("SINCH_FAX_KEY") or os.getenv("SINCH_KEY") or os.getenv("SINCH_KEY_ID")
    secret = os.getenv("SINCH_FAX_SECRET") or os.getenv("SINCH_SECRET") or os.getenv("SINCH_KEY_SECRET")
    project_id = os.getenv("SINCH_FAX_PROJECT_ID") or os.getenv("SINCH_PROJECT_ID")
    service_id = os.getenv("SINCH_FAX_SERVICE_ID") or os.getenv("SINCH_SERVICE_ID")
    base_url = os.getenv("SINCH_FAX_API_BASE_URL", "https://fax.api.sinch.com/v3")

    target_url = body.url or os.getenv("SINCH_WEBHOOK_URL")
    if not target_url:
        raise HTTPException(status_code=400, detail="Provide 'url' or set SINCH_WEBHOOK_URL env var")

    if not all([key, secret, project_id, service_id]):
        missing = []
        if not key:
            missing.append("SINCH_FAX_KEY|SINCH_KEY|SINCH_KEY_ID")
        if not secret:
            missing.append("SINCH_FAX_SECRET|SINCH_SECRET|SINCH_KEY_SECRET")
        if not project_id:
            missing.append("SINCH_FAX_PROJECT_ID|SINCH_PROJECT_ID")
        if not service_id:
            missing.append("SINCH_FAX_SERVICE_ID|SINCH_SERVICE_ID")
        logger.error(f"[SINCH] Missing env vars: {missing}")
        raise HTTPException(status_code=500, detail="Missing SINCH credentials or identifiers")

    url = f"{base_url}/projects/{project_id}/services/{service_id}"
    payload = {"incomingWebhookUrl": target_url, "webhookContentType": "application/json"}
    try:
        logger.info(f"[SINCH] Updating webhook for project={project_id} service={service_id} url={target_url}")
        resp = requests.patch(url, json=payload, headers={"Content-Type": "application/json"}, auth=(key, secret), timeout=30)
        logger.info(f"[SINCH] Update webhook response code={resp.status_code}")
        return {"status": "ok", "code": resp.status_code, "response": resp.text}
    except Exception as e:
        logger.error(f"[SINCH] Failed to update webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update Sinch webhook URL")
    