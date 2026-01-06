#!/bin/bash
# =============================================================================
# OncoLife - Create Education S3 Bucket
# =============================================================================
# This script creates and configures the S3 bucket for education content.
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions
#   - ACCOUNT_ID and AWS_REGION environment variables set
#
# Usage:
#   chmod +x scripts/aws/create-education-bucket.sh
#   ./scripts/aws/create-education-bucket.sh
# =============================================================================

set -e

# Check required environment variables
if [ -z "$AWS_REGION" ]; then
    echo "Error: AWS_REGION not set"
    echo "Run: export AWS_REGION=us-west-2"
    exit 1
fi

# Get account ID if not set
if [ -z "$ACCOUNT_ID" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

BUCKET_NAME="oncolife-education-${ACCOUNT_ID}"

echo "=============================================="
echo "Creating OncoLife Education Bucket"
echo "=============================================="
echo "Bucket: $BUCKET_NAME"
echo "Region: $AWS_REGION"
echo "=============================================="

# Create bucket
echo "Creating bucket..."
if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$AWS_REGION"
else
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION"
fi

# Enable versioning
echo "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

# Enable encryption (KMS)
echo "Enabling encryption..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "aws:kms"
            },
            "BucketKeyEnabled": true
        }]
    }'

# Block public access
echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration '{
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }'

# Create folder structure
echo "Creating folder structure..."
aws s3api put-object --bucket "$BUCKET_NAME" --key "symptoms/"
aws s3api put-object --bucket "$BUCKET_NAME" --key "care-team/"
aws s3api put-object --bucket "$BUCKET_NAME" --key "handouts/"

# Set lifecycle policy (optional - for cost management)
echo "Setting lifecycle policy..."
aws s3api put-bucket-lifecycle-configuration \
    --bucket "$BUCKET_NAME" \
    --lifecycle-configuration '{
        "Rules": [{
            "ID": "MoveToIAAfter90Days",
            "Status": "Enabled",
            "Filter": {},
            "Transitions": [{
                "Days": 90,
                "StorageClass": "STANDARD_IA"
            }]
        }]
    }'

# Enable access logging (optional but recommended for HIPAA)
echo "Note: For HIPAA compliance, enable access logging to a separate log bucket."

echo ""
echo "=============================================="
echo "SUCCESS: Education bucket created!"
echo "=============================================="
echo "Bucket Name: $BUCKET_NAME"
echo "Bucket ARN:  arn:aws:s3:::$BUCKET_NAME"
echo ""
echo "Next Steps:"
echo "1. Upload education PDFs: ./scripts/aws/upload-education-pdfs.sh"
echo "2. Run seed script: python scripts/seed_education.py"
echo "=============================================="
