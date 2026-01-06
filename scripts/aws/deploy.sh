#!/bin/bash
# =============================================================================
# OncoLife AWS Deployment Script
# =============================================================================
# Usage: ./scripts/aws/deploy.sh [patient-api|doctor-api|all]
#
# This script handles BOTH first-time deployment AND updates:
# - If ECS services don't exist, it will guide you to create them
# - If ECS services exist, it will update them with new images
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - Docker installed and running
# - For first-time: VPC, ALB, Target Groups must exist
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
PATIENT_API_TASK_FAMILY="oncolife-patient-api"
DOCTOR_API_ECR_REPO="oncolife-doctor-api"
DOCTOR_API_SERVICE="doctor-api-service"
DOCTOR_API_TASK_FAMILY="oncolife-doctor-api"

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# =============================================================================
# Service Existence Check
# =============================================================================

check_service_exists() {
    local service_name=$1
    local result=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $service_name \
        --region $AWS_REGION \
        --query 'services[?status==`ACTIVE`].serviceName' \
        --output text 2>/dev/null)
    
    if [ -n "$result" ] && [ "$result" != "None" ]; then
        return 0  # Service exists
    else
        return 1  # Service doesn't exist
    fi
}

check_task_definition_exists() {
    local family=$1
    local result=$(aws ecs list-task-definitions \
        --family-prefix $family \
        --region $AWS_REGION \
        --query 'taskDefinitionArns[0]' \
        --output text 2>/dev/null)
    
    if [ -n "$result" ] && [ "$result" != "None" ]; then
        return 0
    else
        return 1
    fi
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
    
    # Check if service exists
    if check_service_exists $PATIENT_API_SERVICE; then
        log_info "Service exists, updating..."
        aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $PATIENT_API_SERVICE \
            --force-new-deployment \
            --region $AWS_REGION > /dev/null
        
        log_info "Waiting for deployment to stabilize..."
        aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $PATIENT_API_SERVICE \
            --region $AWS_REGION
        
        log_success "Patient API deployed successfully!"
    else
        log_error "=========================================="
        log_error "ECS Service '$PATIENT_API_SERVICE' does not exist!"
        log_error "=========================================="
        echo ""
        log_warning "This appears to be a FIRST-TIME deployment."
        log_warning "You need to create the AWS infrastructure first."
        echo ""
        log_info "Required infrastructure (in order):"
        echo "  1. VPC with public/private subnets"
        echo "  2. Security Groups (ALB, ECS, RDS)"
        echo "  3. RDS PostgreSQL database"
        echo "  4. Cognito User Pool"
        echo "  5. ALB and Target Groups"
        echo "  6. Secrets Manager secrets"
        echo "  7. ECS Task Definitions"
        echo "  8. ECS Services"
        echo ""
        log_info "Options:"
        echo "  A) Use AWS Console to create infrastructure manually"
        echo "  B) Run: ./scripts/aws/setup-infrastructure.sh (partial setup)"
        echo "  C) If you have Windows: Run full-deploy.ps1 in PowerShell"
        echo ""
        log_info "See docs/STEP_BY_STEP_DEPLOYMENT.md for detailed instructions."
        echo ""
        
        # Offer to check what exists
        log_info "Checking what infrastructure exists..."
        echo ""
        
        # Check task definition
        if check_task_definition_exists $PATIENT_API_TASK_FAMILY; then
            log_success "  ✓ Task definition exists: $PATIENT_API_TASK_FAMILY"
        else
            log_error "  ✗ Task definition missing: $PATIENT_API_TASK_FAMILY"
        fi
        
        # Check ALB
        local alb=$(aws elbv2 describe-load-balancers \
            --region $AWS_REGION \
            --query "LoadBalancers[?contains(LoadBalancerName, 'patient')].LoadBalancerName" \
            --output text 2>/dev/null)
        if [ -n "$alb" ]; then
            log_success "  ✓ ALB exists: $alb"
        else
            log_error "  ✗ ALB missing (need patient ALB)"
        fi
        
        # Check target group
        local tg=$(aws elbv2 describe-target-groups \
            --region $AWS_REGION \
            --query "TargetGroups[?contains(TargetGroupName, 'patient')].TargetGroupName" \
            --output text 2>/dev/null)
        if [ -n "$tg" ]; then
            log_success "  ✓ Target Group exists: $tg"
        else
            log_error "  ✗ Target Group missing"
        fi
        
        echo ""
        exit 1
    fi
}

deploy_doctor_api() {
    log_info "Deploying Doctor API to ECS..."
    
    # Check if service exists
    if check_service_exists $DOCTOR_API_SERVICE; then
        log_info "Service exists, updating..."
        aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $DOCTOR_API_SERVICE \
            --force-new-deployment \
            --region $AWS_REGION > /dev/null
        
        log_info "Waiting for deployment to stabilize..."
        aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $DOCTOR_API_SERVICE \
            --region $AWS_REGION
        
        log_success "Doctor API deployed successfully!"
    else
        log_error "=========================================="
        log_error "ECS Service '$DOCTOR_API_SERVICE' does not exist!"
        log_error "=========================================="
        echo ""
        log_warning "This appears to be a FIRST-TIME deployment."
        log_warning "You need to create the AWS infrastructure first."
        echo ""
        log_info "Required infrastructure (in order):"
        echo "  1. VPC with public/private subnets"
        echo "  2. Security Groups (ALB, ECS, RDS)"
        echo "  3. RDS PostgreSQL database"
        echo "  4. Cognito User Pool"
        echo "  5. ALB and Target Groups"
        echo "  6. Secrets Manager secrets"
        echo "  7. ECS Task Definitions"
        echo "  8. ECS Services"
        echo ""
        log_info "See docs/STEP_BY_STEP_DEPLOYMENT.md for detailed instructions."
        echo ""
        
        # Offer to check what exists
        log_info "Checking what infrastructure exists..."
        echo ""
        
        # Check task definition
        if check_task_definition_exists $DOCTOR_API_TASK_FAMILY; then
            log_success "  ✓ Task definition exists: $DOCTOR_API_TASK_FAMILY"
        else
            log_error "  ✗ Task definition missing: $DOCTOR_API_TASK_FAMILY"
        fi
        
        # Check ALB
        local alb=$(aws elbv2 describe-load-balancers \
            --region $AWS_REGION \
            --query "LoadBalancers[?contains(LoadBalancerName, 'doctor')].LoadBalancerName" \
            --output text 2>/dev/null)
        if [ -n "$alb" ]; then
            log_success "  ✓ ALB exists: $alb"
        else
            log_error "  ✗ ALB missing (need doctor ALB)"
        fi
        
        # Check target group
        local tg=$(aws elbv2 describe-target-groups \
            --region $AWS_REGION \
            --query "TargetGroups[?contains(TargetGroupName, 'doctor')].TargetGroupName" \
            --output text 2>/dev/null)
        if [ -n "$tg" ]; then
            log_success "  ✓ Target Group exists: $tg"
        else
            log_error "  ✗ Target Group missing"
        fi
        
        echo ""
        exit 1
    fi
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
# Infrastructure Check Command
# =============================================================================

check_infrastructure() {
    log_info "=========================================="
    log_info "Checking AWS Infrastructure Status"
    log_info "Region: $AWS_REGION"
    log_info "=========================================="
    echo ""
    
    # Check AWS Account
    log_info "AWS Account: $AWS_ACCOUNT_ID"
    echo ""
    
    # Check ECS Cluster
    log_step "Checking ECS Cluster..."
    if aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION 2>/dev/null | grep -q "ACTIVE"; then
        log_success "  ✓ ECS Cluster: $ECS_CLUSTER"
    else
        log_error "  ✗ ECS Cluster missing: $ECS_CLUSTER"
    fi
    
    # Check ECR Repositories
    log_step "Checking ECR Repositories..."
    for repo in $PATIENT_API_ECR_REPO $DOCTOR_API_ECR_REPO; do
        if aws ecr describe-repositories --repository-names $repo --region $AWS_REGION 2>/dev/null > /dev/null; then
            log_success "  ✓ ECR Repository: $repo"
        else
            log_error "  ✗ ECR Repository missing: $repo"
        fi
    done
    
    # Check Task Definitions
    log_step "Checking Task Definitions..."
    for family in $PATIENT_API_TASK_FAMILY $DOCTOR_API_TASK_FAMILY; do
        if check_task_definition_exists $family; then
            log_success "  ✓ Task Definition: $family"
        else
            log_error "  ✗ Task Definition missing: $family"
        fi
    done
    
    # Check ALBs
    log_step "Checking Load Balancers..."
    local albs=$(aws elbv2 describe-load-balancers \
        --region $AWS_REGION \
        --query "LoadBalancers[?contains(LoadBalancerName, 'oncolife')].LoadBalancerName" \
        --output text 2>/dev/null)
    if [ -n "$albs" ]; then
        for alb in $albs; do
            log_success "  ✓ ALB: $alb"
        done
    else
        log_error "  ✗ No ALBs found with 'oncolife' in name"
    fi
    
    # Check Target Groups
    log_step "Checking Target Groups..."
    local tgs=$(aws elbv2 describe-target-groups \
        --region $AWS_REGION \
        --query "TargetGroups[?contains(TargetGroupName, 'patient') || contains(TargetGroupName, 'doctor')].TargetGroupName" \
        --output text 2>/dev/null)
    if [ -n "$tgs" ]; then
        for tg in $tgs; do
            log_success "  ✓ Target Group: $tg"
        done
    else
        log_error "  ✗ No Target Groups found"
    fi
    
    # Check ECS Services
    log_step "Checking ECS Services..."
    for service in $PATIENT_API_SERVICE $DOCTOR_API_SERVICE; do
        if check_service_exists $service; then
            log_success "  ✓ ECS Service: $service"
        else
            log_error "  ✗ ECS Service missing: $service"
        fi
    done
    
    # Check Secrets
    log_step "Checking Secrets Manager..."
    for secret in "oncolife/db" "oncolife/cognito"; do
        if aws secretsmanager describe-secret --secret-id $secret --region $AWS_REGION 2>/dev/null > /dev/null; then
            log_success "  ✓ Secret: $secret"
        else
            log_error "  ✗ Secret missing: $secret"
        fi
    done
    
    echo ""
    log_info "=========================================="
    log_info "Infrastructure check complete!"
    log_info "=========================================="
}

# =============================================================================
# Entry Point
# =============================================================================

print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all          - Deploy all services (default)"
    echo "  patient-api  - Deploy Patient API only"
    echo "  doctor-api   - Deploy Doctor API only"
    echo "  check        - Check infrastructure status (no deployment)"
    echo ""
    echo "Environment Variables:"
    echo "  AWS_REGION   - AWS region (default: us-west-2)"
    echo "  ECS_CLUSTER  - ECS cluster name (default: oncolife-production)"
    echo "  IMAGE_TAG    - Docker image tag (default: git commit hash)"
    echo ""
    echo "First-time deployment?"
    echo "  Run: $0 check"
    echo "  This will show what infrastructure is missing."
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
    check|status)
        check_infrastructure
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





