#!/bin/bash
# =============================================================================
# OncoLife AWS Deployment Script
# =============================================================================
# Usage: ./scripts/aws/deploy.sh [patient-api|doctor-api|all]
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - Docker installed and running
# - Environment variables set (or .env file present)
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-west-2}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECS_CLUSTER="${ECS_CLUSTER:-oncolife-production}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"

# Service configurations
PATIENT_API_ECR_REPO="oncolife-patient-api"
PATIENT_API_SERVICE="patient-api-service"
DOCTOR_API_ECR_REPO="oncolife-doctor-api"
DOCTOR_API_SERVICE="doctor-api-service"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install it first."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check AWS credentials
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        log_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    log_success "All prerequisites met."
}

login_ecr() {
    log_info "Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $ECR_URI
    log_success "ECR login successful."
}

# =============================================================================
# Build Functions
# =============================================================================

build_patient_api() {
    log_info "Building Patient API Docker image..."
    
    docker build \
        -t $PATIENT_API_ECR_REPO:$IMAGE_TAG \
        -t $PATIENT_API_ECR_REPO:latest \
        -f apps/patient-platform/patient-api/Dockerfile \
        apps/patient-platform/patient-api/
    
    log_success "Patient API image built: $PATIENT_API_ECR_REPO:$IMAGE_TAG"
}

build_doctor_api() {
    log_info "Building Doctor API Docker image..."
    
    docker build \
        -t $DOCTOR_API_ECR_REPO:$IMAGE_TAG \
        -t $DOCTOR_API_ECR_REPO:latest \
        -f apps/doctor-platform/doctor-api/Dockerfile \
        apps/doctor-platform/doctor-api/
    
    log_success "Doctor API image built: $DOCTOR_API_ECR_REPO:$IMAGE_TAG"
}

# =============================================================================
# Push Functions
# =============================================================================

push_patient_api() {
    log_info "Pushing Patient API image to ECR..."
    
    docker tag $PATIENT_API_ECR_REPO:$IMAGE_TAG $ECR_URI/$PATIENT_API_ECR_REPO:$IMAGE_TAG
    docker tag $PATIENT_API_ECR_REPO:latest $ECR_URI/$PATIENT_API_ECR_REPO:latest
    
    docker push $ECR_URI/$PATIENT_API_ECR_REPO:$IMAGE_TAG
    docker push $ECR_URI/$PATIENT_API_ECR_REPO:latest
    
    log_success "Patient API image pushed: $ECR_URI/$PATIENT_API_ECR_REPO:$IMAGE_TAG"
}

push_doctor_api() {
    log_info "Pushing Doctor API image to ECR..."
    
    docker tag $DOCTOR_API_ECR_REPO:$IMAGE_TAG $ECR_URI/$DOCTOR_API_ECR_REPO:$IMAGE_TAG
    docker tag $DOCTOR_API_ECR_REPO:latest $ECR_URI/$DOCTOR_API_ECR_REPO:latest
    
    docker push $ECR_URI/$DOCTOR_API_ECR_REPO:$IMAGE_TAG
    docker push $ECR_URI/$DOCTOR_API_ECR_REPO:latest
    
    log_success "Doctor API image pushed: $ECR_URI/$DOCTOR_API_ECR_REPO:$IMAGE_TAG"
}

# =============================================================================
# Deploy Functions
# =============================================================================

deploy_patient_api() {
    log_info "Deploying Patient API to ECS..."
    
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $PATIENT_API_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    log_info "Waiting for deployment to stabilize..."
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $PATIENT_API_SERVICE \
        --region $AWS_REGION
    
    log_success "Patient API deployed successfully!"
}

deploy_doctor_api() {
    log_info "Deploying Doctor API to ECS..."
    
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $DOCTOR_API_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    log_info "Waiting for deployment to stabilize..."
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $DOCTOR_API_SERVICE \
        --region $AWS_REGION
    
    log_success "Doctor API deployed successfully!"
}

# =============================================================================
# Main Deployment Workflows
# =============================================================================

deploy_patient() {
    log_info "=========================================="
    log_info "Deploying Patient API"
    log_info "=========================================="
    
    check_prerequisites
    login_ecr
    build_patient_api
    push_patient_api
    deploy_patient_api
    
    log_success "=========================================="
    log_success "Patient API deployment complete!"
    log_success "Image: $ECR_URI/$PATIENT_API_ECR_REPO:$IMAGE_TAG"
    log_success "=========================================="
}

deploy_doctor() {
    log_info "=========================================="
    log_info "Deploying Doctor API"
    log_info "=========================================="
    
    check_prerequisites
    login_ecr
    build_doctor_api
    push_doctor_api
    deploy_doctor_api
    
    log_success "=========================================="
    log_success "Doctor API deployment complete!"
    log_success "Image: $ECR_URI/$DOCTOR_API_ECR_REPO:$IMAGE_TAG"
    log_success "=========================================="
}

deploy_all() {
    log_info "=========================================="
    log_info "Deploying All Services"
    log_info "=========================================="
    
    check_prerequisites
    login_ecr
    
    # Build all images
    build_patient_api
    build_doctor_api
    
    # Push all images
    push_patient_api
    push_doctor_api
    
    # Deploy all services
    deploy_patient_api
    deploy_doctor_api
    
    log_success "=========================================="
    log_success "All services deployed successfully!"
    log_success "=========================================="
}

# =============================================================================
# Entry Point
# =============================================================================

print_usage() {
    echo "Usage: $0 [patient-api|doctor-api|all]"
    echo ""
    echo "Commands:"
    echo "  patient-api  - Deploy Patient API only"
    echo "  doctor-api   - Deploy Doctor API only"
    echo "  all          - Deploy all services"
    echo ""
    echo "Environment Variables:"
    echo "  AWS_REGION   - AWS region (default: us-west-2)"
    echo "  ECS_CLUSTER  - ECS cluster name (default: oncolife-production)"
    echo "  IMAGE_TAG    - Docker image tag (default: git commit hash)"
}

case "${1:-all}" in
    patient-api)
        deploy_patient
        ;;
    doctor-api)
        deploy_doctor
        ;;
    all)
        deploy_all
        ;;
    -h|--help)
        print_usage
        exit 0
        ;;
    *)
        log_error "Unknown command: $1"
        print_usage
        exit 1
        ;;
esac



