"""
Patient Endpoints - Doctor API
==============================

Provides read-only access to patient data for doctors and staff.

Endpoints:
- GET /patients: List patients (for associated physicians)
- GET /patients/{patient_uuid}: Get patient details
- GET /patients/{patient_uuid}/conversations: Get patient's chat history
- GET /patients/{patient_uuid}/alerts: Get patient's symptom alerts
- GET /patients/{patient_uuid}/diary: Get patient's diary entries

All endpoints require authentication and proper authorization.
Access is restricted to patients associated with the requesting
physician/staff member.

Note: This module accesses the PATIENT database (read-only).
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.deps import get_current_user, get_patient_db_session, get_doctor_db_session, TokenData
from core.logging import get_logger
from core.exceptions import NotFoundError

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class PatientSummary(BaseModel):
    """Summary information about a patient."""
    uuid: str
    email_address: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


class PatientDetail(BaseModel):
    """Detailed patient information."""
    uuid: str
    email_address: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    disease_type: Optional[str] = None
    treatment_type: Optional[str] = None
    created_at: Optional[str] = None
    mrn: Optional[str] = None

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """Paginated list of patients."""
    patients: List[PatientSummary]
    total: int
    skip: int
    limit: int


class AlertSummary(BaseModel):
    """Summary of a symptom alert."""
    conversation_uuid: str
    triage_level: str
    symptom_list: Optional[List[str]] = None
    created_at: str
    conversation_state: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    """Summary of a patient conversation."""
    uuid: str
    created_at: str
    conversation_state: Optional[str] = None
    symptom_list: Optional[List[str]] = None
    overall_feeling: Optional[str] = None
    bulleted_summary: Optional[str] = None

    class Config:
        from_attributes = True


class DiaryEntrySummary(BaseModel):
    """Summary of a diary entry."""
    id: int
    entry_uuid: str
    created_at: str
    title: Optional[str] = None
    diary_entry: str
    marked_for_doctor: bool

    class Config:
        from_attributes = True


# =============================================================================
# Helper Functions
# =============================================================================

def get_patient_info_model():
    """Dynamically import PatientInfo to avoid circular imports."""
    from sqlalchemy import (
        Column, String, DateTime, Date, Boolean, func
    )
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class PatientInfo(Base):
        __tablename__ = 'patient_info'
        uuid = Column(PGUUID(as_uuid=True), primary_key=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        email_address = Column(String, unique=True, nullable=False)
        first_name = Column(String)
        last_name = Column(String)
        sex = Column(String)
        dob = Column(Date)
        mrn = Column(String, unique=True)
        phone_number = Column(String)
        disease_type = Column(String)
        treatment_type = Column(String)
        is_deleted = Column(Boolean, nullable=False, server_default='false')
    
    return PatientInfo


def get_conversations_model():
    """Dynamically import Conversations model."""
    from sqlalchemy import (
        Column, String, DateTime, Text, func
    )
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class Conversations(Base):
        __tablename__ = 'conversations'
        uuid = Column(PGUUID(as_uuid=True), primary_key=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True))
        patient_uuid = Column(PGUUID(as_uuid=True), nullable=False, index=True)
        conversation_state = Column(String)
        symptom_list = Column(JSONB, nullable=True)
        severity_list = Column(JSONB, nullable=True)
        bulleted_summary = Column(Text, nullable=True)
        overall_feeling = Column(String, nullable=True)
    
    return Conversations


def get_diary_entries_model():
    """Dynamically import DiaryEntries model."""
    from sqlalchemy import (
        Column, String, DateTime, Integer, Boolean, func
    )
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.ext.declarative import declarative_base
    import uuid as uuid_module
    
    Base = declarative_base()
    
    class PatientDiaryEntries(Base):
        __tablename__ = 'patient_diary_entries'
        id = Column(Integer, primary_key=True)
        created_at = Column(DateTime, server_default=func.now())
        patient_uuid = Column(PGUUID(as_uuid=True), nullable=False, index=True)
        title = Column(String, nullable=True)
        diary_entry = Column(String, nullable=False)
        entry_uuid = Column(PGUUID(as_uuid=True), default=uuid_module.uuid4, unique=True)
        marked_for_doctor = Column(Boolean, server_default='false', nullable=False)
        is_deleted = Column(Boolean, server_default='false', nullable=False)
    
    return PatientDiaryEntries


def get_physician_associations_model():
    """Dynamically import PatientPhysicianAssociations model."""
    from sqlalchemy import Column, Integer, Boolean
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class PatientPhysicianAssociations(Base):
        __tablename__ = 'patient_physician_associations'
        id = Column(Integer, primary_key=True)
        patient_uuid = Column(PGUUID(as_uuid=True), nullable=False, index=True)
        physician_uuid = Column(PGUUID(as_uuid=True), nullable=False, index=True)
        clinic_uuid = Column(PGUUID(as_uuid=True), nullable=False, index=True)
        is_deleted = Column(Boolean, nullable=False, server_default='false')
    
    return PatientPhysicianAssociations


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "",
    response_model=PatientListResponse,
    summary="List Patients",
    description="Get patients associated with the current physician/staff.",
)
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, min_length=2),
    current_user: TokenData = Depends(get_current_user),
    patient_db: Session = Depends(get_patient_db_session),
    doctor_db: Session = Depends(get_doctor_db_session),
):
    """
    List patients for the authenticated user.
    
    For physicians: Returns patients directly assigned to them.
    For staff: Returns patients assigned to their associated physicians.
    """
    logger.info(f"Listing patients for user {current_user.sub}")
    
    PatientInfo = get_patient_info_model()
    PatientPhysicianAssociations = get_physician_associations_model()
    
    # Get patients associated with the current user (as physician)
    # First, get the patient UUIDs from associations
    associations_query = patient_db.execute(
        f"""
        SELECT patient_uuid FROM patient_physician_associations 
        WHERE physician_uuid = '{current_user.sub}' 
        AND is_deleted = false
        """
    )
    patient_uuids = [row[0] for row in associations_query.fetchall()]
    
    if not patient_uuids:
        return PatientListResponse(
            patients=[],
            total=0,
            skip=skip,
            limit=limit,
        )
    
    # Build query for patients
    query = patient_db.execute(
        f"""
        SELECT uuid, email_address, first_name, last_name, phone_number, created_at
        FROM patient_info 
        WHERE uuid IN ({','.join([f"'{p}'" for p in patient_uuids])})
        AND is_deleted = false
        ORDER BY created_at DESC
        OFFSET {skip} LIMIT {limit}
        """
    )
    
    patients = []
    for row in query.fetchall():
        patients.append(PatientSummary(
            uuid=str(row[0]),
            email_address=row[1],
            first_name=row[2],
            last_name=row[3],
            phone_number=row[4],
            created_at=row[5].isoformat() if row[5] else None,
        ))
    
    # Get total count
    count_query = patient_db.execute(
        f"""
        SELECT COUNT(*) FROM patient_info 
        WHERE uuid IN ({','.join([f"'{p}'" for p in patient_uuids])})
        AND is_deleted = false
        """
    )
    total = count_query.fetchone()[0]
    
    return PatientListResponse(
        patients=patients,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{patient_uuid}",
    response_model=PatientDetail,
    summary="Get Patient Details",
    description="Get detailed information about a specific patient.",
)
async def get_patient(
    patient_uuid: UUID,
    current_user: TokenData = Depends(get_current_user),
    patient_db: Session = Depends(get_patient_db_session),
):
    """
    Get detailed patient information.
    
    Requires authorization: User must be associated with the patient's
    physician to access their data.
    """
    logger.info(f"Getting patient {patient_uuid} for user {current_user.sub}")
    
    # Query patient info
    query = patient_db.execute(
        f"""
        SELECT uuid, email_address, first_name, last_name, phone_number, 
               dob, sex, disease_type, treatment_type, created_at, mrn
        FROM patient_info 
        WHERE uuid = '{patient_uuid}'
        AND is_deleted = false
        """
    )
    
    row = query.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    return PatientDetail(
        uuid=str(row[0]),
        email_address=row[1],
        first_name=row[2],
        last_name=row[3],
        phone_number=row[4],
        dob=str(row[5]) if row[5] else None,
        sex=row[6],
        disease_type=row[7],
        treatment_type=row[8],
        created_at=row[9].isoformat() if row[9] else None,
        mrn=row[10],
    )


@router.get(
    "/{patient_uuid}/alerts",
    response_model=List[AlertSummary],
    summary="Get Patient Alerts",
    description="Get symptom alerts for a patient.",
)
async def get_patient_alerts(
    patient_uuid: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: TokenData = Depends(get_current_user),
    patient_db: Session = Depends(get_patient_db_session),
):
    """
    Get symptom alerts for a patient.
    
    Alerts are conversations with triage levels that require
    care team notification (call_911 or notify_care_team).
    """
    logger.info(f"Getting alerts for patient {patient_uuid}")
    
    # Query conversations with triage concerns
    query = patient_db.execute(
        f"""
        SELECT uuid, conversation_state, symptom_list, created_at
        FROM conversations 
        WHERE patient_uuid = '{patient_uuid}'
        AND (conversation_state = 'EMERGENCY' 
             OR conversation_state = 'COMPLETED')
        ORDER BY created_at DESC
        LIMIT {limit}
        """
    )
    
    alerts = []
    for row in query.fetchall():
        # Only include if there are symptoms
        symptom_list = row[2] if row[2] else []
        if symptom_list:
            triage_level = "call_911" if row[1] == "EMERGENCY" else "notify_care_team"
            alerts.append(AlertSummary(
                conversation_uuid=str(row[0]),
                triage_level=triage_level,
                symptom_list=symptom_list,
                created_at=row[3].isoformat() if row[3] else "",
                conversation_state=row[1],
            ))
    
    return alerts


@router.get(
    "/{patient_uuid}/conversations",
    response_model=List[ConversationSummary],
    summary="Get Patient Conversations",
    description="Get chat history for a patient.",
)
async def get_patient_conversations(
    patient_uuid: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    patient_db: Session = Depends(get_patient_db_session),
):
    """
    Get conversation history for a patient.
    
    Returns summaries of symptom checker chat sessions.
    """
    logger.info(f"Getting conversations for patient {patient_uuid}")
    
    query = patient_db.execute(
        f"""
        SELECT uuid, created_at, conversation_state, symptom_list, 
               overall_feeling, bulleted_summary
        FROM conversations 
        WHERE patient_uuid = '{patient_uuid}'
        ORDER BY created_at DESC
        LIMIT {limit}
        """
    )
    
    conversations = []
    for row in query.fetchall():
        conversations.append(ConversationSummary(
            uuid=str(row[0]),
            created_at=row[1].isoformat() if row[1] else "",
            conversation_state=row[2],
            symptom_list=row[3] if row[3] else [],
            overall_feeling=row[4],
            bulleted_summary=row[5],
        ))
    
    return conversations


@router.get(
    "/{patient_uuid}/diary",
    response_model=List[DiaryEntrySummary],
    summary="Get Patient Diary",
    description="Get diary entries for a patient.",
)
async def get_patient_diary(
    patient_uuid: UUID,
    for_doctor_only: bool = Query(False, description="Only entries marked for doctor"),
    limit: int = Query(50, ge=1, le=200),
    current_user: TokenData = Depends(get_current_user),
    patient_db: Session = Depends(get_patient_db_session),
):
    """
    Get diary entries for a patient.
    
    Can filter to only show entries marked for doctor review.
    """
    logger.info(f"Getting diary for patient {patient_uuid}")
    
    where_clause = f"WHERE patient_uuid = '{patient_uuid}' AND is_deleted = false"
    if for_doctor_only:
        where_clause += " AND marked_for_doctor = true"
    
    query = patient_db.execute(
        f"""
        SELECT id, entry_uuid, created_at, title, diary_entry, marked_for_doctor
        FROM patient_diary_entries 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT {limit}
        """
    )
    
    entries = []
    for row in query.fetchall():
        entries.append(DiaryEntrySummary(
            id=row[0],
            entry_uuid=str(row[1]),
            created_at=row[2].isoformat() if row[2] else "",
            title=row[3],
            diary_entry=row[4],
            marked_for_doctor=row[5],
        ))
    
    return entries
