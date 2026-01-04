"""
Patient Onboarding Service.

This is the main orchestration service for the patient onboarding flow:
1. Receive and process referral faxes (OCR)
2. Create patient accounts in Cognito
3. Send welcome notifications
4. Track onboarding progress
5. Handle multi-step first login

Flow:
    Fax → OCR → Parse → Create Account → Send Welcome → Track Progress → Complete

Usage:
    from services import OnboardingService
    
    onboarding_service = OnboardingService(patient_db, doctor_db)
    result = await onboarding_service.process_referral(s3_bucket, s3_key)
"""

import secrets
import string
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from uuid import UUID

from sqlalchemy.orm import Session

from core.config import settings
from core.logging import get_logger
from core.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
)

from db.models.referral import (
    PatientReferral,
    PatientOnboardingStatus,
    ReferralDocument,
    OnboardingNotificationLog,
    ReferralStatus,
    OnboardingStep,
)
from db.patient_models import PatientInfo, PatientConfigurations, PatientPhysicianAssociations

from services.ocr_service import OCRService
from services.notification_service import NotificationService
from services.auth_service import AuthService

logger = get_logger(__name__)


class OnboardingService:
    """
    Main service for patient onboarding.
    
    Orchestrates:
    - Referral processing (fax → OCR → database)
    - Patient account creation (Cognito + local DB)
    - Welcome notifications (email + SMS)
    - Onboarding step tracking
    """
    
    def __init__(
        self,
        patient_db: Session,
        doctor_db: Optional[Session] = None,
        ocr_service: Optional[OCRService] = None,
        notification_service: Optional[NotificationService] = None,
        auth_service: Optional[AuthService] = None,
    ):
        """
        Initialize onboarding service.
        
        Args:
            patient_db: Patient database session
            doctor_db: Doctor database session (optional)
            ocr_service: OCR service instance (optional)
            notification_service: Notification service instance (optional)
            auth_service: Auth service instance (optional)
        """
        self.patient_db = patient_db
        self.doctor_db = doctor_db
        
        self.ocr_service = ocr_service or OCRService()
        self.notification_service = notification_service or NotificationService()
        self.auth_service = auth_service or AuthService(patient_db, doctor_db)
    
    # =========================================================================
    # REFERRAL PROCESSING
    # =========================================================================
    
    async def process_referral(
        self,
        s3_bucket: str,
        s3_key: str,
        fax_number: Optional[str] = None,
        fax_received_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Process a referral document from S3.
        
        Full flow:
        1. Create referral record
        2. Process document with OCR
        3. Parse extracted data
        4. Create patient account
        5. Send welcome notifications
        
        Args:
            s3_bucket: S3 bucket containing the document
            s3_key: S3 object key
            fax_number: Source fax number (optional)
            fax_received_at: When fax was received (optional)
            
        Returns:
            Dict with referral status and patient info
        """
        logger.info(f"Processing referral: s3://{s3_bucket}/{s3_key}")
        
        # Step 1: Create referral record
        referral = PatientReferral(
            status=ReferralStatus.PROCESSING.value,
            fax_number=fax_number,
            fax_received_at=fax_received_at or datetime.utcnow(),
        )
        self.patient_db.add(referral)
        self.patient_db.flush()
        
        referral_uuid = referral.uuid
        logger.info(f"Created referral record: {referral_uuid}")
        
        try:
            # Step 2: Create document record
            document = ReferralDocument(
                referral_uuid=referral_uuid,
                s3_bucket=s3_bucket,
                s3_key=s3_key,
            )
            self.patient_db.add(document)
            
            # Step 3: Process with OCR
            ocr_result = await self.ocr_service.process_document(s3_bucket, s3_key)
            
            # Update document with OCR results
            document.raw_ocr_text = ocr_result["raw_text"]
            document.ocr_confidence = ocr_result["confidence"]
            document.page_count = ocr_result["page_count"]
            document.processed_at = datetime.utcnow()
            
            # Step 4: Parse and store extracted data
            extracted = ocr_result["extracted_fields"]
            self._populate_referral_from_ocr(referral, extracted)
            
            referral.raw_extracted_data = extracted
            referral.extraction_confidence = ocr_result["confidence"]
            referral.status = ReferralStatus.PARSED.value
            
            self.patient_db.flush()
            
            # Step 5: Validate required fields
            validation_errors = self._validate_referral(referral)
            if validation_errors:
                referral.status = ReferralStatus.REVIEW_NEEDED.value
                referral.fields_needing_review = validation_errors
                self.patient_db.commit()
                
                logger.warning(f"Referral needs review: {referral_uuid}")
                return {
                    "success": False,
                    "referral_uuid": str(referral_uuid),
                    "status": ReferralStatus.REVIEW_NEEDED.value,
                    "validation_errors": validation_errors,
                }
            
            # Step 6: Create patient account
            patient_result = await self._create_patient_from_referral(referral)
            
            # Step 7: Send welcome notifications
            await self._send_welcome_notifications(referral)
            
            referral.status = ReferralStatus.WELCOME_SENT.value
            self.patient_db.commit()
            
            logger.info(f"Referral processed successfully: {referral_uuid}")
            
            return {
                "success": True,
                "referral_uuid": str(referral_uuid),
                "patient_uuid": str(referral.patient_uuid),
                "status": ReferralStatus.WELCOME_SENT.value,
                "patient_email": referral.patient_email,
            }
            
        except Exception as e:
            referral.status = ReferralStatus.FAILED.value
            referral.status_message = str(e)
            self.patient_db.commit()
            
            logger.error(f"Referral processing failed: {referral_uuid} - {e}")
            raise
    
    def _populate_referral_from_ocr(
        self,
        referral: PatientReferral,
        extracted: Dict[str, Any],
    ) -> None:
        """Populate referral fields from OCR extracted data."""
        # Patient demographics
        patient = extracted.get("patient", {})
        referral.patient_first_name = patient.get("first_name")
        referral.patient_last_name = patient.get("last_name")
        referral.patient_email = patient.get("email")
        referral.patient_phone = patient.get("phone")
        referral.patient_mrn = patient.get("mrn")
        
        if patient.get("dob"):
            referral.patient_dob = patient["dob"]
        if patient.get("sex"):
            referral.patient_sex = patient["sex"]
        
        # Physician
        physician = extracted.get("physician", {})
        referral.attending_physician_name = physician.get("name")
        referral.clinic_name = physician.get("clinic")
        
        # Diagnosis
        diagnosis = extracted.get("diagnosis", {})
        referral.cancer_type = diagnosis.get("cancer_type")
        referral.cancer_staging = diagnosis.get("staging") or diagnosis.get("ajcc_stage")
        
        # Treatment
        treatment = extracted.get("treatment", {})
        referral.chemo_plan_name = treatment.get("plan_name")
        if treatment.get("start_date"):
            referral.chemo_start_date = treatment["start_date"]
        if treatment.get("end_date"):
            referral.chemo_end_date = treatment["end_date"]
        referral.chemo_current_cycle = treatment.get("current_cycle")
        referral.chemo_total_cycles = treatment.get("total_cycles")
        referral.treatment_goal = treatment.get("treatment_goal")
        
        # Vitals
        vitals = extracted.get("vitals", {})
        referral.bmi = vitals.get("bmi")
        referral.height_cm = vitals.get("height_cm")
        referral.weight_kg = vitals.get("weight_kg")
        referral.blood_pressure = vitals.get("blood_pressure")
        referral.pulse = vitals.get("pulse")
        referral.spo2 = vitals.get("spo2")
        
        # History
        history = extracted.get("history", {})
        referral.past_medical_history = history.get("past_medical")
        referral.past_surgical_history = history.get("past_surgical")
        
        # Medications
        medications = extracted.get("medications", [])
        if medications:
            referral.current_medications = medications
        
        # Social
        social = extracted.get("social", {})
        referral.tobacco_use = social.get("tobacco")
        referral.alcohol_use = social.get("alcohol")
    
    def _validate_referral(self, referral: PatientReferral) -> List[str]:
        """
        Validate required fields are present.
        
        Returns:
            List of field names that need review
        """
        errors = []
        
        # Required fields
        if not referral.patient_first_name:
            errors.append("patient_first_name")
        if not referral.patient_last_name:
            errors.append("patient_last_name")
        if not referral.patient_email and not referral.patient_phone:
            errors.append("patient_email_or_phone")
        
        # Highly recommended fields
        if not referral.patient_dob:
            errors.append("patient_dob")
        if not referral.cancer_type:
            errors.append("cancer_type")
        if not referral.attending_physician_name:
            errors.append("attending_physician_name")
        
        return errors
    
    # =========================================================================
    # PATIENT ACCOUNT CREATION
    # =========================================================================
    
    async def _create_patient_from_referral(
        self,
        referral: PatientReferral,
    ) -> Dict[str, Any]:
        """
        Create patient account from referral data.
        
        Creates:
        1. Cognito user with temporary password
        2. PatientInfo record
        3. PatientConfigurations record
        4. PatientPhysicianAssociations record
        5. PatientOnboardingStatus record
        """
        logger.info(f"Creating patient from referral: {referral.uuid}")
        
        # Generate temporary password
        temp_password = self._generate_temp_password()
        
        # Prepare email (use provided or generate from phone)
        email = referral.patient_email
        if not email and referral.patient_phone:
            # Generate email from phone for Cognito (can be updated later)
            phone_clean = referral.patient_phone.replace("-", "").replace(" ", "")[-10:]
            email = f"{phone_clean}@patient.oncolife.local"
        
        if not email:
            raise ValidationError(
                message="Cannot create account: no email or phone number",
                field="patient_email",
            )
        
        # Create via auth service (handles Cognito + DB records)
        # Note: We need to use admin_create_user with temp password
        auth_result = await self._create_cognito_user(
            email=email,
            first_name=referral.patient_first_name,
            last_name=referral.patient_last_name,
            temp_password=temp_password,
        )
        
        patient_uuid = auth_result["uuid"]
        
        # Update patient info with referral data
        patient = self.patient_db.query(PatientInfo).filter(
            PatientInfo.uuid == patient_uuid
        ).first()
        
        if patient:
            patient.phone_number = referral.patient_phone
            patient.dob = referral.patient_dob
            patient.sex = referral.patient_sex
            patient.mrn = referral.patient_mrn
            patient.disease_type = referral.cancer_type
        
        # Link referral to patient
        referral.patient_uuid = patient_uuid
        referral.cognito_user_id = patient_uuid
        referral.status = ReferralStatus.PATIENT_CREATED.value
        
        # Create onboarding status record
        onboarding_status = PatientOnboardingStatus(
            referral_uuid=referral.uuid,
            patient_uuid=patient_uuid,
            current_step=OnboardingStep.PASSWORD_RESET.value,
        )
        self.patient_db.add(onboarding_status)
        
        self.patient_db.flush()
        
        logger.info(f"Patient created: {patient_uuid}")
        
        return {
            "uuid": patient_uuid,
            "email": email,
            "temp_password": temp_password,
        }
    
    async def _create_cognito_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        temp_password: str,
    ) -> Dict[str, Any]:
        """Create Cognito user with temporary password."""
        import boto3
        from botocore.exceptions import ClientError
        
        cognito_client = boto3.client(
            "cognito-idp",
            region_name=settings.aws_region,
        )
        
        try:
            response = cognito_client.admin_create_user(
                UserPoolId=settings.cognito_user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                    {"Name": "given_name", "Value": first_name},
                    {"Name": "family_name", "Value": last_name},
                ],
                TemporaryPassword=temp_password,
                ForceAliasCreation=False,
                MessageAction="SUPPRESS",  # We send our own welcome email
            )
            
            user_sub = None
            for attr in response["User"]["Attributes"]:
                if attr["Name"] == "sub":
                    user_sub = attr["Value"]
                    break
            
            if not user_sub:
                raise ExternalServiceError(
                    message="Cognito user created but UUID not returned",
                    service_name="Cognito",
                )
            
            # Create local database records
            self._create_patient_records(
                user_sub=user_sub,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            
            return {"uuid": user_sub, "email": email}
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            if error_code == "UsernameExistsException":
                raise ConflictError(
                    message=f"A patient with email {email} already exists",
                    resource_type="Patient",
                    resource_id=email,
                )
            
            raise ExternalServiceError(
                message=f"Failed to create Cognito user: {error_message}",
                service_name="Cognito",
            )
    
    def _create_patient_records(
        self,
        user_sub: str,
        email: str,
        first_name: str,
        last_name: str,
    ) -> None:
        """Create patient database records."""
        # Check if already exists
        existing = self.patient_db.query(PatientInfo).filter(
            PatientInfo.uuid == user_sub
        ).first()
        
        if existing:
            return
        
        # Create patient info
        patient = PatientInfo(
            uuid=user_sub,
            email_address=email,
            first_name=first_name,
            last_name=last_name,
        )
        self.patient_db.add(patient)
        
        # Create configuration
        config = PatientConfigurations(uuid=user_sub)
        self.patient_db.add(config)
        
        # Create physician association (use defaults)
        association = PatientPhysicianAssociations(
            patient_uuid=user_sub,
            physician_uuid=AuthService.DEFAULT_PHYSICIAN_UUID,
            clinic_uuid=AuthService.DEFAULT_CLINIC_UUID,
        )
        self.patient_db.add(association)
    
    def _generate_temp_password(self, length: int = None) -> str:
        """
        Generate a secure temporary password.
        
        Meets Cognito requirements:
        - At least 8 characters
        - Contains uppercase
        - Contains lowercase
        - Contains number
        - Contains special character
        """
        length = length or settings.onboarding_temp_password_length
        
        # Ensure minimum requirements
        password_chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*"),
        ]
        
        # Fill remaining with mix
        remaining = length - len(password_chars)
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password_chars.extend(secrets.choice(all_chars) for _ in range(remaining))
        
        # Shuffle
        secrets.SystemRandom().shuffle(password_chars)
        
        return "".join(password_chars)
    
    # =========================================================================
    # WELCOME NOTIFICATIONS
    # =========================================================================
    
    async def _send_welcome_notifications(
        self,
        referral: PatientReferral,
    ) -> None:
        """Send welcome email and SMS."""
        # Get temp password (stored during creation)
        # In production, you'd retrieve this securely or regenerate
        temp_password = self._generate_temp_password()  # Regenerate for demo
        
        # Get onboarding status
        onboarding = self.patient_db.query(PatientOnboardingStatus).filter(
            PatientOnboardingStatus.referral_uuid == referral.uuid
        ).first()
        
        # Send email
        if referral.patient_email:
            try:
                result = await self.notification_service.send_welcome_email(
                    email=referral.patient_email,
                    first_name=referral.patient_first_name,
                    temp_password=temp_password,
                    physician_name=referral.attending_physician_name,
                )
                
                if onboarding:
                    onboarding.welcome_email_sent = True
                    onboarding.welcome_email_sent_at = datetime.utcnow()
                
                # Log notification
                self._log_notification(
                    patient_uuid=referral.patient_uuid,
                    referral_uuid=referral.uuid,
                    notification_type="welcome",
                    channel="email",
                    recipient=referral.patient_email,
                    status="sent",
                    message_id=result.get("message_id"),
                )
                
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")
                self._log_notification(
                    patient_uuid=referral.patient_uuid,
                    referral_uuid=referral.uuid,
                    notification_type="welcome",
                    channel="email",
                    recipient=referral.patient_email,
                    status="failed",
                    status_message=str(e),
                )
        
        # Send SMS
        if referral.patient_phone and settings.sns_enabled:
            try:
                result = await self.notification_service.send_welcome_sms(
                    phone_number=referral.patient_phone,
                    first_name=referral.patient_first_name,
                )
                
                if onboarding:
                    onboarding.welcome_sms_sent = True
                    onboarding.welcome_sms_sent_at = datetime.utcnow()
                
                self._log_notification(
                    patient_uuid=referral.patient_uuid,
                    referral_uuid=referral.uuid,
                    notification_type="welcome",
                    channel="sms",
                    recipient=referral.patient_phone,
                    status="sent",
                    message_id=result.get("message_id"),
                )
                
            except Exception as e:
                logger.error(f"Failed to send welcome SMS: {e}")
                self._log_notification(
                    patient_uuid=referral.patient_uuid,
                    referral_uuid=referral.uuid,
                    notification_type="welcome",
                    channel="sms",
                    recipient=referral.patient_phone,
                    status="failed",
                    status_message=str(e),
                )
    
    def _log_notification(
        self,
        patient_uuid: UUID,
        referral_uuid: UUID,
        notification_type: str,
        channel: str,
        recipient: str,
        status: str,
        message_id: Optional[str] = None,
        status_message: Optional[str] = None,
    ) -> None:
        """Log notification for audit trail."""
        log_entry = OnboardingNotificationLog(
            patient_uuid=patient_uuid,
            referral_uuid=referral_uuid,
            notification_type=notification_type,
            channel=channel,
            recipient=recipient,
            status=status,
            aws_message_id=message_id,
            status_message=status_message,
        )
        self.patient_db.add(log_entry)
    
    # =========================================================================
    # ONBOARDING FLOW MANAGEMENT
    # =========================================================================
    
    def get_onboarding_status(
        self,
        patient_uuid: str,
    ) -> Dict[str, Any]:
        """
        Get current onboarding status for a patient.
        
        Args:
            patient_uuid: Patient UUID
            
        Returns:
            Dict with current step and completion status
        """
        status = self.patient_db.query(PatientOnboardingStatus).filter(
            PatientOnboardingStatus.patient_uuid == patient_uuid
        ).first()
        
        if not status:
            return {
                "is_onboarded": True,  # No record means legacy patient
                "current_step": None,
            }
        
        return {
            "is_onboarded": status.is_fully_onboarded,
            "current_step": status.current_step,
            "steps": {
                "password_reset": status.password_reset_completed,
                "acknowledgement": status.acknowledgement_completed,
                "terms_privacy": status.terms_accepted and status.privacy_accepted,
                "reminder_setup": status.reminder_preference_set,
            },
            "first_login_at": status.first_login_at.isoformat() if status.first_login_at else None,
            "onboarding_completed_at": status.onboarding_completed_at.isoformat() if status.onboarding_completed_at else None,
        }
    
    def complete_password_reset(
        self,
        patient_uuid: str,
    ) -> Dict[str, Any]:
        """
        Mark password reset step as complete.
        
        Args:
            patient_uuid: Patient UUID
            
        Returns:
            Updated status
        """
        status = self._get_or_create_onboarding_status(patient_uuid)
        
        status.password_reset_completed = True
        status.password_reset_at = datetime.utcnow()
        status.current_step = OnboardingStep.ACKNOWLEDGEMENT.value
        
        if not status.first_login_at:
            status.first_login_at = datetime.utcnow()
        
        self.patient_db.commit()
        
        return self.get_onboarding_status(patient_uuid)
    
    def complete_acknowledgement(
        self,
        patient_uuid: str,
        acknowledgement_text: str,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark acknowledgement step as complete.
        
        Args:
            patient_uuid: Patient UUID
            acknowledgement_text: The exact text the patient acknowledged
            ip_address: Client IP for audit
            
        Returns:
            Updated status
        """
        status = self._get_or_create_onboarding_status(patient_uuid)
        
        status.acknowledgement_completed = True
        status.acknowledgement_text = acknowledgement_text
        status.acknowledgement_at = datetime.utcnow()
        status.acknowledgement_ip = ip_address
        status.current_step = OnboardingStep.TERMS_PRIVACY.value
        
        self.patient_db.commit()
        
        return self.get_onboarding_status(patient_uuid)
    
    def complete_terms_privacy(
        self,
        patient_uuid: str,
        terms_accepted: bool,
        privacy_accepted: bool,
        hipaa_acknowledged: bool = True,
    ) -> Dict[str, Any]:
        """
        Mark terms and privacy step as complete.
        
        Args:
            patient_uuid: Patient UUID
            terms_accepted: Whether terms were accepted
            privacy_accepted: Whether privacy policy was accepted
            hipaa_acknowledged: Whether HIPAA notice was acknowledged
            
        Returns:
            Updated status
        """
        if not terms_accepted or not privacy_accepted:
            raise ValidationError(
                message="Both terms and privacy policy must be accepted",
                field="acceptance",
            )
        
        status = self._get_or_create_onboarding_status(patient_uuid)
        
        status.terms_accepted = True
        status.terms_version = settings.terms_version
        status.terms_accepted_at = datetime.utcnow()
        
        status.privacy_accepted = True
        status.privacy_version = settings.privacy_version
        status.privacy_accepted_at = datetime.utcnow()
        
        status.hipaa_acknowledged = hipaa_acknowledged
        status.hipaa_version = settings.hipaa_version
        status.hipaa_acknowledged_at = datetime.utcnow()
        
        status.current_step = OnboardingStep.REMINDER_SETUP.value
        
        # Also update patient configurations
        config = self.patient_db.query(PatientConfigurations).filter(
            PatientConfigurations.uuid == patient_uuid
        ).first()
        
        if config:
            config.acknowledgement_done = True
            config.agreed_conditions = True
        
        self.patient_db.commit()
        
        return self.get_onboarding_status(patient_uuid)
    
    def complete_reminder_setup(
        self,
        patient_uuid: str,
        channel: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        reminder_time: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete reminder setup and finalize onboarding.
        
        Args:
            patient_uuid: Patient UUID
            channel: 'email', 'sms', or 'both'
            email: Email for reminders (optional, uses account email)
            phone: Phone for reminders (optional, uses account phone)
            reminder_time: Time for daily reminders (HH:MM format)
            timezone: User's timezone
            
        Returns:
            Updated status
        """
        status = self._get_or_create_onboarding_status(patient_uuid)
        
        status.reminder_preference_set = True
        status.reminder_channel = channel
        status.reminder_email = email
        status.reminder_phone = phone
        status.reminder_time = reminder_time
        status.reminder_timezone = timezone
        status.reminder_preference_at = datetime.utcnow()
        
        # Mark onboarding as complete
        status.current_step = OnboardingStep.COMPLETED.value
        status.is_fully_onboarded = True
        status.onboarding_completed_at = datetime.utcnow()
        
        # Update patient configuration
        config = self.patient_db.query(PatientConfigurations).filter(
            PatientConfigurations.uuid == patient_uuid
        ).first()
        
        if config:
            config.reminder_method = channel
            if reminder_time:
                from datetime import time as time_type
                try:
                    hours, minutes = map(int, reminder_time.split(":"))
                    config.reminder_time = time_type(hours, minutes)
                except ValueError:
                    pass
        
        # Update referral status
        if status.referral_uuid:
            referral = self.patient_db.query(PatientReferral).filter(
                PatientReferral.uuid == status.referral_uuid
            ).first()
            if referral:
                referral.status = ReferralStatus.COMPLETED.value
        
        self.patient_db.commit()
        
        logger.info(f"Patient onboarding completed: {patient_uuid}")
        
        return self.get_onboarding_status(patient_uuid)
    
    def _get_or_create_onboarding_status(
        self,
        patient_uuid: str,
    ) -> PatientOnboardingStatus:
        """Get or create onboarding status record."""
        status = self.patient_db.query(PatientOnboardingStatus).filter(
            PatientOnboardingStatus.patient_uuid == patient_uuid
        ).first()
        
        if not status:
            status = PatientOnboardingStatus(
                patient_uuid=patient_uuid,
                current_step=OnboardingStep.PASSWORD_RESET.value,
            )
            self.patient_db.add(status)
            self.patient_db.flush()
        
        return status
    
    # =========================================================================
    # MANUAL REFERRAL ENTRY
    # =========================================================================
    
    async def create_manual_referral(
        self,
        patient_data: Dict[str, Any],
        physician_data: Optional[Dict[str, Any]] = None,
        treatment_data: Optional[Dict[str, Any]] = None,
        send_welcome: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a referral manually (for cases where OCR fails or for testing).
        
        Args:
            patient_data: Patient demographics
            physician_data: Physician and clinic info (optional)
            treatment_data: Treatment/chemo info (optional)
            send_welcome: Whether to send welcome notifications
            
        Returns:
            Dict with referral and patient info
        """
        logger.info(f"Creating manual referral for: {patient_data.get('email')}")
        
        # Create referral
        referral = PatientReferral(
            status=ReferralStatus.PARSED.value,
            patient_first_name=patient_data.get("first_name"),
            patient_last_name=patient_data.get("last_name"),
            patient_email=patient_data.get("email"),
            patient_phone=patient_data.get("phone"),
            patient_dob=patient_data.get("dob"),
            patient_sex=patient_data.get("sex"),
            patient_mrn=patient_data.get("mrn"),
        )
        
        if physician_data:
            referral.attending_physician_name = physician_data.get("name")
            referral.clinic_name = physician_data.get("clinic")
        
        if treatment_data:
            referral.cancer_type = treatment_data.get("cancer_type")
            referral.cancer_staging = treatment_data.get("staging")
            referral.chemo_plan_name = treatment_data.get("plan_name")
            referral.chemo_start_date = treatment_data.get("start_date")
            referral.chemo_end_date = treatment_data.get("end_date")
        
        self.patient_db.add(referral)
        self.patient_db.flush()
        
        # Create patient account
        patient_result = await self._create_patient_from_referral(referral)
        
        # Send welcome if requested
        if send_welcome:
            await self._send_welcome_notifications(referral)
            referral.status = ReferralStatus.WELCOME_SENT.value
        
        self.patient_db.commit()
        
        return {
            "success": True,
            "referral_uuid": str(referral.uuid),
            "patient_uuid": str(referral.patient_uuid),
            "status": referral.status,
        }



