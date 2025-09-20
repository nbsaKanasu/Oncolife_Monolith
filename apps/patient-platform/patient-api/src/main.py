from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from routers.auth.auth_routes import router as auth_router
from routers.patient.patient_routes import router as patient_router
from routers.profile.profile_routes import router as profile_router
from routers.diary.diary_routes import router as diary_router
from routers.summaries.summaries_routes import router as summaries_router
from routers.chemo.chemo_routes import router as chemo_router
from routers.chat.chat_routes import router as chat_router

app = FastAPI()

# CORS
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_env_origins = os.getenv("CORS_ORIGINS")
allow_origins = [o.strip() for o in _env_origins.split(",")] if _env_origins else _default_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(profile_router)
app.include_router(diary_router)
app.include_router(summaries_router)
app.include_router(chemo_router)
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/test-faxes/test-pdf")
async def get_test_pdf():
    """Serve the local test PDF for Sinch to download via contentUrl."""
    pdf_path = os.path.join(os.path.dirname(__file__), "Test Fax.pdf")
    if not os.path.exists(pdf_path):
        return {"error": "Test Fax.pdf not found"}
    return FileResponse(pdf_path, media_type="application/pdf", filename="Test Fax.pdf")


## Removed older testing helpers in favor of a single inline full-flow test endpoint


@app.post("/test-faxes/run-full-inline")
async def run_full_inline():
    """Run the full fax processing pipeline inline (no internal HTTP), to avoid deadlocks."""
    from sqlalchemy.orm import Session
    from db.database import get_patient_db, get_doctor_db
    from routers.auth.auth_routes import _process_pdf_bytes_with_ocr_llm, _find_physician_by_name, _create_patient_from_fax_data

    # Read the test PDF
    pdf_path = os.path.join(os.path.dirname(__file__), "Test Fax.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Test Fax.pdf not found")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Extract fields
    extracted_data = _process_pdf_bytes_with_ocr_llm(pdf_bytes)
    patient_name = extracted_data.get("patient_name")
    patient_email = extracted_data.get("patient_email")
    physician_name = extracted_data.get("physician_name")

    # Open DB sessions
    patient_db: Session = next(get_patient_db())
    doctor_db: Session = next(get_doctor_db())

    try:
        # Resolve physician
        physician_uuid = _find_physician_by_name(physician_name or "", doctor_db)
        if not physician_uuid:
            physician_uuid = 'bea3fce0-42f9-4a00-ae56-4e2591ca17c5'

        # Create patient
        creation_result = _create_patient_from_fax_data(
            extracted_data,
            physician_uuid,
            patient_db,
            doctor_db
        )
        return {
            "extracted": extracted_data,
            "creation": creation_result
        }
    finally:
        try:
            patient_db.close()
        except Exception:
            pass
        try:
            doctor_db.close()
        except Exception:
            pass
