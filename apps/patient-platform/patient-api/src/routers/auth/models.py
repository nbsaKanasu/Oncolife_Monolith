from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi import UploadFile

class SignupRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    physician_email: Optional[EmailStr] = None

class SignupResponse(BaseModel):
    message: str
    email: str
    user_status: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    id_token: str
    token_type: str

class LoginResponse(BaseModel):
    valid: bool
    message: str
    user_status: Optional[str] = None
    session: Optional[str] = None
    tokens: Optional[AuthTokens] = None

class CompleteNewPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
    session: str
    
class CompleteNewPasswordResponse(BaseModel):
    message: str
    tokens: AuthTokens

class DeletePatientRequest(BaseModel):
    email: Optional[EmailStr] = None
    uuid: Optional[str] = None
    skip_aws: Optional[bool] = False

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    email: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    confirmation_code: str
    new_password: str

class ResetPasswordResponse(BaseModel):
    message: str
    email: str

class ProcessFaxRequest(BaseModel):
    """Request model for processing PDF fax files"""
    pass

class ProcessFaxResponse(BaseModel):
    """Response model for PDF fax processing"""
    message: str
    patient_email: Optional[str] = None
    patient_name: Optional[str] = None
    physician_name: Optional[str] = None
    success: bool
    errors: Optional[list] = None


class UpdateSinchWebhookRequest(BaseModel):
    """Request model to update Sinch incoming webhook URL"""
    url: Optional[str] = None