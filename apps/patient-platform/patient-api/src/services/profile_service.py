"""
Profile Service - Patient API
==============================

Service for patient profile operations.

Usage:
    from services import ProfileService
    
    profile_service = ProfileService(patient_db, doctor_db)
    profile = profile_service.get_profile(patient_uuid)
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import time

from sqlalchemy.orm import Session

from db.repositories import ProfileRepository
from db.doctor_models import StaffProfiles, AllClinics, StaffAssociations
from core.logging import get_logger
from core.exceptions import NotFoundError

logger = get_logger(__name__)


class ProfileService:
    """
    Service for patient profile operations.
    
    Provides:
    - Get complete patient profile
    - Update patient configuration
    - Get physician/clinic information
    """
    
    def __init__(
        self,
        patient_db: Session,
        doctor_db: Optional[Session] = None,
    ):
        """
        Initialize the profile service.
        
        Args:
            patient_db: Patient database session
            doctor_db: Doctor database session (optional)
        """
        self.patient_db = patient_db
        self.doctor_db = doctor_db
        self.profile_repo = ProfileRepository(patient_db)
    
    def get_profile(
        self,
        patient_uuid: UUID,
    ) -> Dict[str, Any]:
        """
        Get complete patient profile.
        
        Combines data from patient database and doctor database
        to create a comprehensive profile view.
        
        Args:
            patient_uuid: The patient's UUID
            
        Returns:
            Complete patient profile
            
        Raises:
            NotFoundError: If patient not found
        """
        logger.info(f"Get profile: patient={patient_uuid}")
        
        # Get patient data
        patient, config, association = self.profile_repo.get_full_profile(patient_uuid)
        
        # Get physician and clinic info from doctor database
        doctor_name = None
        clinic_name = None
        
        if association and self.doctor_db:
            doctor_name, clinic_name = self._get_physician_info(association.physician_uuid)
        
        logger.info(f"Profile fetched: patient={patient_uuid} doctor={doctor_name}")
        
        return {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email_address": patient.email_address,
            "phone_number": patient.phone_number,
            "date_of_birth": patient.dob,
            "reminder_time": config.reminder_time if config else None,
            "doctor_name": doctor_name,
            "clinic_name": clinic_name,
        }
    
    def _get_physician_info(
        self,
        physician_uuid: UUID,
    ) -> tuple:
        """Get physician name and clinic name."""
        doctor_name = None
        clinic_name = None
        
        try:
            physician = self.doctor_db.query(StaffProfiles).filter(
                StaffProfiles.staff_uuid == physician_uuid
            ).first()
            
            if physician:
                doctor_name = f"{physician.first_name} {physician.last_name}"
                
                # Get clinic association
                staff_assoc = self.doctor_db.query(StaffAssociations).filter(
                    StaffAssociations.physician_uuid == physician_uuid
                ).first()
                
                if staff_assoc:
                    clinic = self.doctor_db.query(AllClinics).filter(
                        AllClinics.uuid == staff_assoc.clinic_uuid
                    ).first()
                    
                    if clinic:
                        clinic_name = clinic.clinic_name
                        
        except Exception as e:
            logger.error(f"Error fetching physician info: {e}")
        
        return doctor_name, clinic_name
    
    def update_configuration(
        self,
        patient_uuid: UUID,
        reminder_method: Optional[str] = None,
        reminder_time: Optional[time] = None,
        acknowledgement_done: Optional[bool] = None,
        agreed_conditions: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update patient configuration.
        
        Args:
            patient_uuid: The patient's UUID
            reminder_method: New reminder method
            reminder_time: New reminder time
            acknowledgement_done: Acknowledgement status
            agreed_conditions: Terms agreement status
            
        Returns:
            Updated configuration
        """
        logger.info(f"Update configuration: patient={patient_uuid}")
        
        config = self.profile_repo.update_configuration(
            patient_uuid=patient_uuid,
            reminder_method=reminder_method,
            reminder_time=reminder_time,
            acknowledgement_done=acknowledgement_done,
            agreed_conditions=agreed_conditions,
        )
        
        logger.info(f"Configuration updated: patient={patient_uuid}")
        
        return {
            "uuid": str(config.uuid),
            "reminder_method": config.reminder_method,
            "reminder_time": config.reminder_time,
            "acknowledgement_done": config.acknowledgement_done,
            "agreed_conditions": config.agreed_conditions,
        }
    
    def update_consent(
        self,
        patient_uuid: UUID,
        acknowledgement_done: Optional[bool] = None,
        agreed_conditions: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update patient consent status.
        
        Args:
            patient_uuid: The patient's UUID
            acknowledgement_done: Acknowledgement status
            agreed_conditions: Terms agreement status
            
        Returns:
            Updated consent status
        """
        logger.info(f"Update consent: patient={patient_uuid}")
        
        return self.update_configuration(
            patient_uuid=patient_uuid,
            acknowledgement_done=acknowledgement_done,
            agreed_conditions=agreed_conditions,
        )
    
    def get_patient_info(
        self,
        patient_uuid: UUID,
    ) -> Dict[str, Any]:
        """
        Get detailed patient info.
        
        Args:
            patient_uuid: The patient's UUID
            
        Returns:
            Patient information
            
        Raises:
            NotFoundError: If patient not found
        """
        patient = self.profile_repo.get_by_uuid_or_fail(patient_uuid)
        
        return {
            "uuid": str(patient.uuid),
            "created_at": patient.created_at.isoformat() if patient.created_at else None,
            "email_address": patient.email_address,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "sex": patient.sex,
            "dob": patient.dob,
            "mrn": patient.mrn,
            "ethnicity": patient.ethnicity,
            "phone_number": patient.phone_number,
            "disease_type": patient.disease_type,
            "treatment_type": patient.treatment_type,
            "is_deleted": patient.is_deleted,
        }





