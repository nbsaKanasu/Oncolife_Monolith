"""
OCR Service - AWS Textract Integration.

This service processes referral documents using AWS Textract to extract
patient and treatment information from clinic fax referrals.

Features:
- Asynchronous document processing (for large multi-page faxes)
- Synchronous processing (for single-page documents)
- Form and table extraction
- Confidence scoring
- Field-specific parsing (dates, names, medications, etc.)

Usage:
    from services import OCRService
    
    ocr_service = OCRService()
    result = await ocr_service.process_document(s3_bucket, s3_key)
"""

import re
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
import asyncio

import boto3
from botocore.exceptions import ClientError

from core.config import settings
from core.logging import get_logger
from core.exceptions import ExternalServiceError, ValidationError

logger = get_logger(__name__)


class OCRService:
    """
    AWS Textract OCR service for processing referral documents.
    
    Provides:
    - Document text extraction
    - Form field extraction
    - Table extraction
    - Smart field parsing for medical data
    """
    
    # Field patterns for extracting specific data
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",
        "date_mdy": r"\d{1,2}/\d{1,2}/\d{2,4}",
        "date_iso": r"\d{4}-\d{2}-\d{2}",
        "mrn": r"(?:MRN|Medical Record Number|Patient ID)[:\s#]*([A-Z0-9-]+)",
        "bmi": r"BMI[:\s]*(\d+\.?\d*)",
        "height": r"Height[:\s]*(\d+)['\"]?\s*(\d+)?",
        "weight": r"Weight[:\s]*(\d+\.?\d*)\s*(kg|lb|lbs)?",
        "bp": r"(?:BP|Blood Pressure)[:\s]*(\d{2,3}/\d{2,3})",
        "pulse": r"(?:Pulse|Heart Rate|HR)[:\s]*(\d{2,3})",
        "spo2": r"(?:SpO2|O2 Sat|Oxygen)[:\s]*(\d{2,3})%?",
        "temp": r"(?:Temp|Temperature)[:\s]*(\d{2,3}\.?\d*)\s*°?([FCfc])?",
    }
    
    # Keywords for section identification
    SECTION_KEYWORDS = {
        "patient_info": ["patient", "demographics", "name", "dob", "date of birth"],
        "physician": ["physician", "provider", "doctor", "attending", "referring"],
        "diagnosis": ["diagnosis", "cancer", "staging", "tumor", "malignancy"],
        "treatment": ["treatment", "chemotherapy", "regimen", "plan", "cycle"],
        "history": ["history", "medical history", "surgical history", "past medical"],
        "medications": ["medications", "meds", "current medications", "drugs"],
        "vitals": ["vitals", "height", "weight", "bmi", "blood pressure"],
        "labs": ["labs", "laboratory", "results", "cbc", "cmp"],
        "social": ["social", "tobacco", "alcohol", "drug use", "smoking"],
    }
    
    def __init__(self, textract_client: Optional[Any] = None, s3_client: Optional[Any] = None):
        """
        Initialize the OCR service.
        
        Args:
            textract_client: AWS Textract client (optional)
            s3_client: AWS S3 client (optional)
        """
        self._textract_client = textract_client
        self._s3_client = s3_client
        self.aws_region = settings.aws_region
    
    @property
    def textract_client(self):
        """Get or create Textract client."""
        if self._textract_client is None:
            self._textract_client = boto3.client(
                "textract",
                region_name=self.aws_region,
            )
        return self._textract_client
    
    @property
    def s3_client(self):
        """Get or create S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                region_name=self.aws_region,
            )
        return self._s3_client
    
    # =========================================================================
    # DOCUMENT PROCESSING
    # =========================================================================
    
    async def process_document(
        self,
        s3_bucket: str,
        s3_key: str,
        use_async: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a document from S3 using AWS Textract.
        
        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 object key
            use_async: Use async processing for large documents
            
        Returns:
            Dict containing extracted text, forms, tables, and parsed fields
            
        Raises:
            ExternalServiceError: If Textract fails
        """
        logger.info(f"Processing document: s3://{s3_bucket}/{s3_key}")
        
        try:
            if use_async:
                # Start async job
                job_id = await self._start_async_job(s3_bucket, s3_key)
                result = await self._wait_for_job(job_id)
            else:
                # Synchronous processing
                result = await self._process_sync(s3_bucket, s3_key)
            
            # Parse the Textract result
            parsed_data = self._parse_textract_result(result)
            
            # Extract specific medical fields
            extracted_fields = self._extract_medical_fields(parsed_data)
            
            logger.info(f"Document processed successfully: {s3_key}")
            
            return {
                "raw_text": parsed_data["raw_text"],
                "forms": parsed_data["forms"],
                "tables": parsed_data["tables"],
                "extracted_fields": extracted_fields,
                "confidence": parsed_data.get("avg_confidence", 0),
                "page_count": parsed_data.get("page_count", 1),
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Textract error: {error_code} - {error_message}")
            raise ExternalServiceError(
                message=f"OCR processing failed: {error_message}",
                service_name="AWS Textract",
            )
    
    async def _start_async_job(self, s3_bucket: str, s3_key: str) -> str:
        """Start an async Textract job."""
        response = self.textract_client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": s3_bucket,
                    "Name": s3_key,
                }
            },
            FeatureTypes=["FORMS", "TABLES"],
        )
        
        job_id = response["JobId"]
        logger.info(f"Started Textract job: {job_id}")
        return job_id
    
    async def _wait_for_job(
        self,
        job_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """Wait for an async Textract job to complete."""
        elapsed = 0
        
        while elapsed < max_wait_seconds:
            response = self.textract_client.get_document_analysis(JobId=job_id)
            status = response["JobStatus"]
            
            if status == "SUCCEEDED":
                logger.info(f"Textract job completed: {job_id}")
                return response
            elif status == "FAILED":
                raise ExternalServiceError(
                    message=f"Textract job failed: {response.get('StatusMessage', 'Unknown error')}",
                    service_name="AWS Textract",
                )
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise ExternalServiceError(
            message=f"Textract job timed out after {max_wait_seconds} seconds",
            service_name="AWS Textract",
        )
    
    async def _process_sync(self, s3_bucket: str, s3_key: str) -> Dict[str, Any]:
        """Process document synchronously (for small documents)."""
        response = self.textract_client.analyze_document(
            Document={
                "S3Object": {
                    "Bucket": s3_bucket,
                    "Name": s3_key,
                }
            },
            FeatureTypes=["FORMS", "TABLES"],
        )
        return response
    
    # =========================================================================
    # RESULT PARSING
    # =========================================================================
    
    def _parse_textract_result(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Textract response into structured data."""
        blocks = response.get("Blocks", [])
        
        raw_text_lines = []
        forms = {}
        tables = []
        confidences = []
        
        # Create block lookup for relationships
        block_map = {block["Id"]: block for block in blocks}
        
        for block in blocks:
            block_type = block.get("BlockType")
            confidence = block.get("Confidence", 0)
            confidences.append(confidence)
            
            if block_type == "LINE":
                raw_text_lines.append(block.get("Text", ""))
            
            elif block_type == "KEY_VALUE_SET":
                if "KEY" in block.get("EntityTypes", []):
                    key_text = self._get_text_from_block(block, block_map)
                    value_block_id = self._get_value_block_id(block)
                    if value_block_id:
                        value_text = self._get_text_from_block(
                            block_map.get(value_block_id, {}),
                            block_map,
                        )
                        if key_text:
                            forms[key_text.strip()] = value_text.strip()
            
            elif block_type == "TABLE":
                table = self._parse_table(block, block_map)
                if table:
                    tables.append(table)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "raw_text": "\n".join(raw_text_lines),
            "forms": forms,
            "tables": tables,
            "avg_confidence": avg_confidence,
            "page_count": response.get("DocumentMetadata", {}).get("Pages", 1),
        }
    
    def _get_text_from_block(
        self,
        block: Dict[str, Any],
        block_map: Dict[str, Dict],
    ) -> str:
        """Extract text from a block and its children."""
        text_parts = []
        
        if "Relationships" in block:
            for rel in block["Relationships"]:
                if rel["Type"] == "CHILD":
                    for child_id in rel["Ids"]:
                        child_block = block_map.get(child_id, {})
                        if child_block.get("BlockType") == "WORD":
                            text_parts.append(child_block.get("Text", ""))
        
        return " ".join(text_parts)
    
    def _get_value_block_id(self, key_block: Dict[str, Any]) -> Optional[str]:
        """Get the value block ID from a key block."""
        if "Relationships" in key_block:
            for rel in key_block["Relationships"]:
                if rel["Type"] == "VALUE":
                    return rel["Ids"][0] if rel["Ids"] else None
        return None
    
    def _parse_table(
        self,
        table_block: Dict[str, Any],
        block_map: Dict[str, Dict],
    ) -> List[List[str]]:
        """Parse a table block into rows and columns."""
        cells = {}
        
        if "Relationships" not in table_block:
            return []
        
        for rel in table_block["Relationships"]:
            if rel["Type"] == "CHILD":
                for cell_id in rel["Ids"]:
                    cell_block = block_map.get(cell_id, {})
                    if cell_block.get("BlockType") == "CELL":
                        row = cell_block.get("RowIndex", 0)
                        col = cell_block.get("ColumnIndex", 0)
                        text = self._get_text_from_block(cell_block, block_map)
                        cells[(row, col)] = text
        
        if not cells:
            return []
        
        # Convert to 2D array
        max_row = max(r for r, c in cells.keys())
        max_col = max(c for r, c in cells.keys())
        
        table = []
        for row in range(1, max_row + 1):
            row_data = []
            for col in range(1, max_col + 1):
                row_data.append(cells.get((row, col), ""))
            table.append(row_data)
        
        return table
    
    # =========================================================================
    # MEDICAL FIELD EXTRACTION
    # =========================================================================
    
    def _extract_medical_fields(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific medical fields from parsed OCR data."""
        raw_text = parsed_data.get("raw_text", "")
        forms = parsed_data.get("forms", {})
        
        extracted = {
            "patient": {},
            "physician": {},
            "diagnosis": {},
            "treatment": {},
            "vitals": {},
            "history": {},
            "medications": [],
            "labs": {},
            "social": {},
        }
        
        # Extract from forms (key-value pairs)
        extracted["patient"] = self._extract_patient_info(forms, raw_text)
        extracted["physician"] = self._extract_physician_info(forms, raw_text)
        extracted["diagnosis"] = self._extract_diagnosis(forms, raw_text)
        extracted["treatment"] = self._extract_treatment(forms, raw_text)
        extracted["vitals"] = self._extract_vitals(forms, raw_text)
        extracted["history"] = self._extract_history(raw_text)
        extracted["medications"] = self._extract_medications(raw_text)
        extracted["social"] = self._extract_social(raw_text)
        
        return extracted
    
    def _extract_patient_info(
        self,
        forms: Dict[str, str],
        raw_text: str,
    ) -> Dict[str, Any]:
        """Extract patient demographic information."""
        info = {}
        
        # Look for name
        for key, value in forms.items():
            key_lower = key.lower()
            if "name" in key_lower and "physician" not in key_lower:
                parts = value.split()
                if len(parts) >= 2:
                    info["first_name"] = parts[0]
                    info["last_name"] = parts[-1]
                elif len(parts) == 1:
                    info["first_name"] = parts[0]
            elif "first" in key_lower and "name" in key_lower:
                info["first_name"] = value
            elif "last" in key_lower and "name" in key_lower:
                info["last_name"] = value
            elif "dob" in key_lower or "date of birth" in key_lower or "birth" in key_lower:
                info["dob"] = self._parse_date(value)
            elif "sex" in key_lower or "gender" in key_lower:
                info["sex"] = value.strip().capitalize()
        
        # Extract from raw text
        email_match = re.search(self.PATTERNS["email"], raw_text)
        if email_match:
            info["email"] = email_match.group(0)
        
        phone_matches = re.findall(self.PATTERNS["phone"], raw_text)
        if phone_matches:
            info["phone"] = phone_matches[0]
        
        mrn_match = re.search(self.PATTERNS["mrn"], raw_text, re.IGNORECASE)
        if mrn_match:
            info["mrn"] = mrn_match.group(1)
        
        return info
    
    def _extract_physician_info(
        self,
        forms: Dict[str, str],
        raw_text: str,
    ) -> Dict[str, Any]:
        """Extract physician and clinic information."""
        info = {}
        
        for key, value in forms.items():
            key_lower = key.lower()
            if "physician" in key_lower or "provider" in key_lower or "doctor" in key_lower:
                info["name"] = value.strip()
            elif "clinic" in key_lower or "facility" in key_lower or "department" in key_lower:
                info["clinic"] = value.strip()
        
        # Look for physician name patterns in text
        physician_pattern = r"(?:Dr\.|Doctor|MD|DO)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
        match = re.search(physician_pattern, raw_text)
        if match and "name" not in info:
            info["name"] = match.group(0)
        
        return info
    
    def _extract_diagnosis(
        self,
        forms: Dict[str, str],
        raw_text: str,
    ) -> Dict[str, Any]:
        """Extract cancer diagnosis and staging."""
        info = {}
        
        # Look for cancer type
        cancer_patterns = [
            r"(?:carcinoma|cancer|malignancy|tumor)\s+(?:of\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)",
            r"(\w+(?:\s+\w+)?)\s+(?:carcinoma|cancer|malignancy)",
        ]
        for pattern in cancer_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                info["cancer_type"] = match.group(0).strip()
                break
        
        # Look for staging
        staging_pattern = r"(?:Stage|Staging)[:\s]*([IViv0-4ABC]+)"
        match = re.search(staging_pattern, raw_text)
        if match:
            info["staging"] = match.group(1).upper()
        
        # AJCC staging
        ajcc_pattern = r"AJCC\s+(?:Stage|Staging)?[:\s]*([IViv0-4ABC]+)"
        match = re.search(ajcc_pattern, raw_text)
        if match:
            info["ajcc_stage"] = match.group(1).upper()
        
        return info
    
    def _extract_treatment(
        self,
        forms: Dict[str, str],
        raw_text: str,
    ) -> Dict[str, Any]:
        """Extract treatment/chemotherapy information."""
        info = {}
        
        for key, value in forms.items():
            key_lower = key.lower()
            if "plan name" in key_lower or "regimen" in key_lower:
                info["plan_name"] = value.strip()
            elif "start date" in key_lower:
                info["start_date"] = self._parse_date(value)
            elif "end date" in key_lower:
                info["end_date"] = self._parse_date(value)
            elif "cycle" in key_lower:
                cycle_match = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", value)
                if cycle_match:
                    info["current_cycle"] = int(cycle_match.group(1))
                    info["total_cycles"] = int(cycle_match.group(2))
        
        # Look for treatment goal
        goal_pattern = r"(?:Treatment Goal|Line of Treatment)[:\s]*(\w+)"
        match = re.search(goal_pattern, raw_text)
        if match:
            info["treatment_goal"] = match.group(1)
        
        return info
    
    def _extract_vitals(
        self,
        forms: Dict[str, str],
        raw_text: str,
    ) -> Dict[str, Any]:
        """Extract vital signs."""
        vitals = {}
        
        # BMI
        bmi_match = re.search(self.PATTERNS["bmi"], raw_text)
        if bmi_match:
            vitals["bmi"] = float(bmi_match.group(1))
        
        # Blood Pressure
        bp_match = re.search(self.PATTERNS["bp"], raw_text)
        if bp_match:
            vitals["blood_pressure"] = bp_match.group(1)
        
        # Pulse
        pulse_match = re.search(self.PATTERNS["pulse"], raw_text)
        if pulse_match:
            vitals["pulse"] = int(pulse_match.group(1))
        
        # SpO2
        spo2_match = re.search(self.PATTERNS["spo2"], raw_text)
        if spo2_match:
            vitals["spo2"] = int(spo2_match.group(1))
        
        # Height and Weight
        height_pattern = r"Height[:\s]*(\d+)['\s]?(?:ft)?\s*(\d+)?[\"']?\s*(?:in)?"
        height_match = re.search(height_pattern, raw_text, re.IGNORECASE)
        if height_match:
            feet = int(height_match.group(1))
            inches = int(height_match.group(2) or 0)
            vitals["height_cm"] = round((feet * 12 + inches) * 2.54, 1)
        
        weight_match = re.search(self.PATTERNS["weight"], raw_text, re.IGNORECASE)
        if weight_match:
            weight = float(weight_match.group(1))
            unit = (weight_match.group(2) or "").lower()
            if unit in ["lb", "lbs", "pounds"]:
                weight = round(weight * 0.453592, 1)
            vitals["weight_kg"] = weight
        
        return vitals
    
    def _extract_history(self, raw_text: str) -> Dict[str, str]:
        """Extract medical and surgical history."""
        history = {}
        
        # Look for history sections
        pmh_pattern = r"(?:Past Medical History|PMH)[:\s]*(.+?)(?=Past Surgical|PSH|Medications|$)"
        pmh_match = re.search(pmh_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if pmh_match:
            history["past_medical"] = pmh_match.group(1).strip()[:2000]  # Limit length
        
        psh_pattern = r"(?:Past Surgical History|PSH)[:\s]*(.+?)(?=Medications|Social|Family|$)"
        psh_match = re.search(psh_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if psh_match:
            history["past_surgical"] = psh_match.group(1).strip()[:2000]
        
        return history
    
    def _extract_medications(self, raw_text: str) -> List[Dict[str, str]]:
        """Extract current medications."""
        medications = []
        
        # Look for medications section
        meds_pattern = r"(?:Current\s+)?(?:Outpatient\s+)?Medications[:\s]*(.+?)(?=Allergies|Past|Review|$)"
        meds_match = re.search(meds_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        
        if meds_match:
            meds_text = meds_match.group(1)
            # Split by common patterns (bullets, newlines)
            med_lines = re.split(r"[•\n\r]+", meds_text)
            
            for line in med_lines:
                line = line.strip()
                if line and len(line) > 3:
                    # Try to parse medication name and dosage
                    med_match = re.match(r"([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s*(.+)?", line)
                    if med_match:
                        medications.append({
                            "name": med_match.group(1).strip(),
                            "details": (med_match.group(2) or "").strip(),
                        })
        
        return medications[:20]  # Limit to 20 medications
    
    def _extract_social(self, raw_text: str) -> Dict[str, str]:
        """Extract social history (tobacco, alcohol, etc.)."""
        social = {}
        
        # Tobacco
        tobacco_pattern = r"(?:Tobacco|Smoking)[:\s]*(\w+(?:\s+\w+)?)"
        tobacco_match = re.search(tobacco_pattern, raw_text, re.IGNORECASE)
        if tobacco_match:
            social["tobacco"] = tobacco_match.group(1).strip()
        
        # Alcohol
        alcohol_pattern = r"(?:Alcohol)[:\s]*(\w+(?:\s+\w+)?)"
        alcohol_match = re.search(alcohol_pattern, raw_text, re.IGNORECASE)
        if alcohol_match:
            social["alcohol"] = alcohol_match.group(1).strip()
        
        return social
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string into a date object."""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Try various formats
        formats = [
            "%m/%d/%Y",
            "%m/%d/%y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    async def upload_document(
        self,
        file_content: bytes,
        file_name: str,
        content_type: str = "application/pdf",
    ) -> Tuple[str, str]:
        """
        Upload a document to S3 for processing.
        
        Args:
            file_content: File bytes
            file_name: Original file name
            content_type: MIME type
            
        Returns:
            Tuple of (bucket, key)
        """
        bucket = settings.s3_referral_bucket
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        key = f"referrals/{timestamp}/{file_name}"
        
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type,
            )
            
            logger.info(f"Uploaded document: s3://{bucket}/{key}")
            return bucket, key
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise ExternalServiceError(
                message="Failed to upload document",
                service_name="AWS S3",
            )

