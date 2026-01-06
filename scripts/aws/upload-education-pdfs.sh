#!/bin/bash
# =============================================================================
# OncoLife - Upload Education PDFs to S3
# =============================================================================
# This script uploads clinician-approved education content to S3.
#
# Prerequisites:
#   - Education bucket created (run create-education-bucket.sh first)
#   - PDF files in apps/patient-platform/patient-api/model_inputs/education/
#
# Usage:
#   chmod +x scripts/aws/upload-education-pdfs.sh
#   ./scripts/aws/upload-education-pdfs.sh
#
# Note: In production, education content should be uploaded by clinical team.
# =============================================================================

set -e

# Get account ID
if [ -z "$ACCOUNT_ID" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

BUCKET_NAME="oncolife-education-${ACCOUNT_ID}"
LOCAL_PATH="apps/patient-platform/patient-api/model_inputs/education"

echo "=============================================="
echo "Uploading Education Content to S3"
echo "=============================================="
echo "Bucket: $BUCKET_NAME"
echo "Source: $LOCAL_PATH"
echo "=============================================="

# Check if bucket exists
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "Error: Bucket $BUCKET_NAME does not exist."
    echo "Run create-education-bucket.sh first."
    exit 1
fi

# Check if local path exists
if [ ! -d "$LOCAL_PATH" ]; then
    echo "Warning: Local education path does not exist: $LOCAL_PATH"
    echo "Creating sample directory structure..."
    
    mkdir -p "$LOCAL_PATH/symptoms"
    mkdir -p "$LOCAL_PATH/care-team"
    mkdir -p "$LOCAL_PATH/handouts"
    
    echo "Please add your clinician-approved PDFs to:"
    echo "  $LOCAL_PATH/symptoms/     - Symptom-specific education"
    echo "  $LOCAL_PATH/care-team/    - Care team handouts"
    echo "  $LOCAL_PATH/handouts/     - General handouts"
    exit 0
fi

# Upload symptom education files
if [ -d "$LOCAL_PATH/symptoms" ] && [ "$(ls -A $LOCAL_PATH/symptoms 2>/dev/null)" ]; then
    echo "Uploading symptom education files..."
    aws s3 sync "$LOCAL_PATH/symptoms/" "s3://$BUCKET_NAME/symptoms/" \
        --content-type "application/pdf" \
        --metadata "uploaded-by=deploy-script,upload-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "  Symptom files uploaded."
else
    echo "  No symptom files found in $LOCAL_PATH/symptoms/"
fi

# Upload care team files
if [ -d "$LOCAL_PATH/care-team" ] && [ "$(ls -A $LOCAL_PATH/care-team 2>/dev/null)" ]; then
    echo "Uploading care team files..."
    aws s3 sync "$LOCAL_PATH/care-team/" "s3://$BUCKET_NAME/care-team/" \
        --content-type "application/pdf" \
        --metadata "uploaded-by=deploy-script,upload-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "  Care team files uploaded."
else
    echo "  No care team files found in $LOCAL_PATH/care-team/"
fi

# Upload general handouts
if [ -d "$LOCAL_PATH/handouts" ] && [ "$(ls -A $LOCAL_PATH/handouts 2>/dev/null)" ]; then
    echo "Uploading handout files..."
    aws s3 sync "$LOCAL_PATH/handouts/" "s3://$BUCKET_NAME/handouts/" \
        --content-type "application/pdf" \
        --metadata "uploaded-by=deploy-script,upload-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "  Handout files uploaded."
else
    echo "  No handout files found in $LOCAL_PATH/handouts/"
fi

# List uploaded files
echo ""
echo "=============================================="
echo "Uploaded Files:"
echo "=============================================="
aws s3 ls "s3://$BUCKET_NAME/" --recursive --human-readable

echo ""
echo "=============================================="
echo "SUCCESS: Education content uploaded!"
echo "=============================================="
echo ""
echo "Next Steps:"
echo "1. Seed database: python scripts/seed_education.py"
echo "2. Verify in application"
echo "=============================================="
