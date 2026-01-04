# OncoLife - Complete Step-by-Step AWS Deployment Guide

## 📋 Pre-Deployment Checklist

Before starting, ensure you have:

- [ ] AWS Account with Administrator access
- [ ] AWS CLI v2 installed and configured (`aws configure`)
- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (for frontends)

---

## 🗂️ Project Structure Overview

```
OncoLife_Monolith/
├── apps/
│   ├── patient-platform/
│   │   └── patient-api/          # Main Patient API
│   │       ├── src/              # Source code
│   │       ├── scripts/          # Seed scripts
│   │       ├── Dockerfile        # Production container
│   │       ├── requirements.txt  # Python dependencies
│   │       └── env.example       # Environment template
│   └── doctor-platform/
│       └── doctor-api/           # Doctor API
├── scripts/
│   ├── aws/                      # AWS deployment scripts
│   └── db/                       # Database scripts
└── docker-compose.yml            # Local development
```

---

## Phase 1: AWS Infrastructure Setup (One-Time)

### Step 1.1: Create VPC and Networking

```bash
# Create VPC with public and private subnets
aws cloudformation create-stack \
  --stack-name oncolife-vpc \
  --template-body file://cloudformation/vpc.yaml \
  --parameters \
    ParameterKey=VPCCidr,ParameterValue=10.0.0.0/16

# Or use AWS Console:
# VPC → Create VPC → VPC and more
# - IPv4 CIDR: 10.0.0.0/16
# - 2 Availability Zones
# - 2 Public subnets, 2 Private subnets
# - NAT Gateway: 1 per AZ
# - VPC Endpoints: S3
```

### Step 1.2: Create RDS PostgreSQL

```bash
# Create DB Subnet Group
aws rds create-db-subnet-group \
  --db-subnet-group-name oncolife-db-subnet \
  --db-subnet-group-description "OncoLife Database Subnets" \
  --subnet-ids subnet-private-1 subnet-private-2

# Create RDS Instance
aws rds create-db-instance \
  --db-instance-identifier oncolife-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username oncolife_admin \
  --master-user-password "YOUR_SECURE_PASSWORD" \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --kms-key-id alias/aws/rds \
  --vpc-security-group-ids sg-database \
  --db-subnet-group-name oncolife-db-subnet \
  --multi-az \
  --backup-retention-period 7 \
  --no-publicly-accessible
```

**Wait for RDS to be available (10-15 minutes):**
```bash
aws rds wait db-instance-available --db-instance-identifier oncolife-db
```

### Step 1.3: Create Databases

Connect to RDS and create databases:

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier oncolife-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Connect via bastion or SSM Session Manager
psql -h $RDS_ENDPOINT -U oncolife_admin -d postgres

# In psql:
CREATE DATABASE oncolife_patient;
CREATE DATABASE oncolife_doctor;
GRANT ALL PRIVILEGES ON DATABASE oncolife_patient TO oncolife_admin;
GRANT ALL PRIVILEGES ON DATABASE oncolife_doctor TO oncolife_admin;
\q
```

### Step 1.4: Create Cognito User Pool

```bash
# Create User Pool
POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name oncolife-patients \
  --auto-verified-attributes email \
  --username-attributes email \
  --mfa-configuration OFF \
  --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=true}" \
  --schema Name=email,Required=true Name=given_name,Required=true Name=family_name,Required=true \
  --admin-create-user-config AllowAdminCreateUserOnly=false \
  --query 'UserPool.Id' --output text)

echo "User Pool ID: $POOL_ID"

# Create App Client
CLIENT_RESULT=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-name patient-api-client \
  --generate-secret \
  --explicit-auth-flows ADMIN_NO_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_SRP_AUTH \
  --read-attributes email given_name family_name \
  --write-attributes email given_name family_name \
  --query 'UserPoolClient.[ClientId,ClientSecret]' --output text)

echo "Client ID and Secret: $CLIENT_RESULT"
```

### Step 1.5: Create S3 Buckets

```bash
AWS_REGION=us-west-2
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create Referrals Bucket
aws s3api create-bucket \
  --bucket oncolife-referrals-${ACCOUNT_ID} \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket oncolife-referrals-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket oncolife-referrals-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket oncolife-referrals-${ACCOUNT_ID} \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create Education Bucket (same settings)
aws s3api create-bucket \
  --bucket oncolife-education-${ACCOUNT_ID} \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION

aws s3api put-bucket-versioning \
  --bucket oncolife-education-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket oncolife-education-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}]
  }'

aws s3api put-public-access-block \
  --bucket oncolife-education-${ACCOUNT_ID} \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "Buckets created:"
echo "  - oncolife-referrals-${ACCOUNT_ID}"
echo "  - oncolife-education-${ACCOUNT_ID}"
```

### Step 1.6: Configure SES

```bash
# Verify sender email
aws ses verify-email-identity --email-address noreply@yourdomain.com

# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@yourdomain.com

# (Optional) Create email template
aws ses create-template --template '{
  "TemplateName": "oncolife-welcome",
  "SubjectPart": "Welcome to OncoLife - Your Health Companion",
  "HtmlPart": "<h1>Welcome to OncoLife!</h1><p>Your account has been created.</p>",
  "TextPart": "Welcome to OncoLife! Your account has been created."
}'
```

### Step 1.7: Create Secrets in Secrets Manager

```bash
# Database credentials
aws secretsmanager create-secret \
  --name oncolife/db \
  --secret-string '{
    "host": "YOUR_RDS_ENDPOINT",
    "port": "5432",
    "username": "oncolife_admin",
    "password": "YOUR_SECURE_PASSWORD",
    "patient_db": "oncolife_patient",
    "doctor_db": "oncolife_doctor"
  }'

# Cognito credentials
aws secretsmanager create-secret \
  --name oncolife/cognito \
  --secret-string '{
    "user_pool_id": "YOUR_USER_POOL_ID",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }'

# Fax webhook secret
aws secretsmanager create-secret \
  --name oncolife/fax \
  --secret-string '{
    "webhook_secret": "GENERATE_WITH_openssl_rand_-hex_32"
  }'
```

---

## Phase 2: ECS/Fargate Setup

### Step 2.1: Create ECR Repositories

```bash
# Patient API repository
aws ecr create-repository \
  --repository-name oncolife-patient-api \
  --image-scanning-configuration scanOnPush=true

# Doctor API repository
aws ecr create-repository \
  --repository-name oncolife-doctor-api \
  --image-scanning-configuration scanOnPush=true
```

### Step 2.2: Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name oncolife-production \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1
```

### Step 2.3: Create IAM Role for ECS Tasks

```bash
# Create task execution role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create task role with permissions
aws iam create-role \
  --role-name oncolifeTaskRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Add permissions for S3, Cognito, SES, SNS, Textract
aws iam put-role-policy \
  --role-name oncolifeTaskRole \
  --policy-name OncolifePermissions \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        "Resource": [
          "arn:aws:s3:::oncolife-referrals-*",
          "arn:aws:s3:::oncolife-referrals-*/*",
          "arn:aws:s3:::oncolife-education-*",
          "arn:aws:s3:::oncolife-education-*/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminDeleteUser",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:AdminRespondToAuthChallenge"
        ],
        "Resource": "arn:aws:cognito-idp:*:*:userpool/*"
      },
      {
        "Effect": "Allow",
        "Action": ["ses:SendEmail", "ses:SendRawEmail"],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": ["sns:Publish"],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": ["textract:AnalyzeDocument", "textract:StartDocumentAnalysis", "textract:GetDocumentAnalysis"],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": ["secretsmanager:GetSecretValue"],
        "Resource": "arn:aws:secretsmanager:*:*:secret:oncolife/*"
      }
    ]
  }'
```

### Step 2.4: Create Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "oncolife-patient-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/oncolifeTaskRole",
  "containerDefinitions": [
    {
      "name": "patient-api",
      "image": "ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/oncolife-patient-api:latest",
      "portMappings": [
        {"containerPort": 8000, "protocol": "tcp"}
      ],
      "essential": true,
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DEBUG", "value": "false"},
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "LOG_FORMAT", "value": "json"},
        {"name": "AWS_REGION", "value": "us-west-2"},
        {"name": "S3_REFERRAL_BUCKET", "value": "oncolife-referrals-ACCOUNT_ID"},
        {"name": "S3_EDUCATION_BUCKET", "value": "oncolife-education-ACCOUNT_ID"},
        {"name": "SES_SENDER_EMAIL", "value": "noreply@yourdomain.com"},
        {"name": "CORS_ORIGINS", "value": "https://app.yourdomain.com"}
      ],
      "secrets": [
        {"name": "PATIENT_DB_HOST", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db:host::"},
        {"name": "PATIENT_DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db:password::"},
        {"name": "PATIENT_DB_USER", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db:username::"},
        {"name": "PATIENT_DB_NAME", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db:patient_db::"},
        {"name": "COGNITO_USER_POOL_ID", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito:user_pool_id::"},
        {"name": "COGNITO_CLIENT_ID", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito:client_id::"},
        {"name": "COGNITO_CLIENT_SECRET", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito:client_secret::"},
        {"name": "FAX_WEBHOOK_SECRET", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/fax:webhook_secret::"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/oncolife-patient-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register task definition:

```bash
# Replace ACCOUNT_ID in the file first
sed -i "s/ACCOUNT_ID/${ACCOUNT_ID}/g" ecs-task-definition.json

aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

### Step 2.5: Create ALB and Target Group

```bash
# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name oncolife-api-alb \
  --subnets subnet-public-1 subnet-public-2 \
  --security-groups sg-alb \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Create Target Group
TG_ARN=$(aws elbv2 create-target-group \
  --name patient-api-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create HTTPS Listener (requires ACM certificate)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-west-2:xxx:certificate/xxx \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### Step 2.6: Create ECS Service

```bash
aws ecs create-service \
  --cluster oncolife-production \
  --service-name patient-api-service \
  --task-definition oncolife-patient-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-private-1,subnet-private-2],
    securityGroups=[sg-ecs],
    assignPublicIp=DISABLED
  }" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=patient-api,containerPort=8000" \
  --health-check-grace-period-seconds 120
```

---

## Phase 3: Application Deployment

### Step 3.1: Build and Push Docker Image

```bash
cd OncoLife_Monolith

# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com

# Build image
docker build \
  -t oncolife-patient-api:latest \
  -f apps/patient-platform/patient-api/Dockerfile \
  apps/patient-platform/patient-api/

# Tag and push
docker tag oncolife-patient-api:latest \
  ${ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/oncolife-patient-api:latest

docker push ${ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/oncolife-patient-api:latest
```

### Step 3.2: Run Database Migrations

```bash
# Connect to bastion or use SSM Session Manager
# Clone repo and run migrations

cd /tmp
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith/apps/patient-platform/patient-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export PATIENT_DB_HOST=your-rds-endpoint
export PATIENT_DB_PORT=5432
export PATIENT_DB_NAME=oncolife_patient
export PATIENT_DB_USER=oncolife_admin
export PATIENT_DB_PASSWORD=your_password

# Run migrations (if using Alembic)
cd src
alembic upgrade head

# Or create tables directly (for initial setup)
python -c "
from db.base import Base
from db.session import engine
from db.models import *  # Import all models
Base.metadata.create_all(bind=engine)
print('Tables created successfully!')
"
```

### Step 3.3: Seed Education Data

```bash
# Still in the virtual environment on bastion

cd /tmp/Oncolife_Monolith/apps/patient-platform/patient-api

# Run education seed script
python scripts/seed_education.py

# Verify data
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os

engine = create_engine(f'postgresql://{os.environ[\"PATIENT_DB_USER\"]}:{os.environ[\"PATIENT_DB_PASSWORD\"]}@{os.environ[\"PATIENT_DB_HOST\"]}:{os.environ[\"PATIENT_DB_PORT\"]}/{os.environ[\"PATIENT_DB_NAME\"]}')
with Session(engine) as session:
    from db.models.education import Symptom, Disclaimer, EducationDocument
    print(f'Symptoms: {session.query(Symptom).count()}')
    print(f'Disclaimers: {session.query(Disclaimer).count()}')
    print(f'Education Docs: {session.query(EducationDocument).count()}')
"
```

### Step 3.4: Upload Education PDFs to S3

```bash
# Create folder structure
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/fever/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/nausea/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/bleeding/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/fatigue/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/pain/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/diarrhea/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/constipation/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "symptoms/mouth/"
aws s3api put-object --bucket oncolife-education-${ACCOUNT_ID} --key "care-team/"

# Upload PDFs (from your local machine with PDFs)
for symptom in fever nausea bleeding fatigue pain diarrhea constipation mouth; do
  aws s3 cp ./education-docs/${symptom}_v1.pdf \
    s3://oncolife-education-${ACCOUNT_ID}/symptoms/${symptom}/${symptom}_v1.pdf \
    --sse aws:kms
done

# Upload care team handout
aws s3 cp ./education-docs/care_team_handout_v1.pdf \
  s3://oncolife-education-${ACCOUNT_ID}/care-team/care_team_handout_v1.pdf \
  --sse aws:kms
```

### Step 3.5: Deploy to ECS

```bash
# Force new deployment
aws ecs update-service \
  --cluster oncolife-production \
  --service patient-api-service \
  --force-new-deployment

# Wait for deployment
aws ecs wait services-stable \
  --cluster oncolife-production \
  --services patient-api-service

echo "Deployment complete!"
```

---

## Phase 4: Configure Fax Webhook

### Step 4.1: Get ALB DNS Name

```bash
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names oncolife-api-alb \
  --query 'LoadBalancers[0].DNSName' --output text)

echo "API URL: https://${ALB_DNS}"
```

### Step 4.2: Configure Fax Provider (Sinch)

1. Log into Sinch Dashboard
2. Navigate to **Fax → Numbers**
3. Select your dedicated fax number
4. Configure webhook:
   - **URL**: `https://api.yourdomain.com/api/v1/onboarding/webhook/fax/sinch`
   - **Events**: `fax.received`
   - **Secret**: (same as FAX_WEBHOOK_SECRET in Secrets Manager)

### Step 4.3: Test Fax Webhook

```bash
# Test health endpoint
curl https://api.yourdomain.com/health

# Test fax webhook (with signature)
curl -X POST https://api.yourdomain.com/api/v1/onboarding/webhook/fax/sinch \
  -H "Content-Type: application/json" \
  -H "X-Sinch-Signature: test_signature" \
  -d '{"event": "fax.received", "test": true}'
```

---

## Phase 5: Verification & Testing

### Step 5.1: Verify All Services

```bash
# Health check
curl https://api.yourdomain.com/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### Step 5.2: Test Authentication

```bash
# Create test user
curl -X POST https://api.yourdomain.com/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Step 5.3: Test Education Tab

```bash
# Get education content (requires auth token)
curl https://api.yourdomain.com/api/v1/education/tab \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 5.4: Test Symptom Checker

```bash
# Create chat session
curl -X POST https://api.yourdomain.com/api/v1/chat/session/new \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Phase 6: Monitoring Setup

### Step 6.1: Create CloudWatch Dashboard

```bash
aws cloudwatch put-dashboard \
  --dashboard-name OncoLife-Production \
  --dashboard-body file://cloudwatch-dashboard.json
```

### Step 6.2: Create Alarms

```bash
# CPU Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "OncoLife-HighCPU" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ClusterName,Value=oncolife-production Name=ServiceName,Value=patient-api-service \
  --alarm-actions arn:aws:sns:us-west-2:xxx:oncolife-alerts

# 5xx Errors Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "OncoLife-5xxErrors" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-west-2:xxx:oncolife-alerts
```

---

## 🔧 Troubleshooting

### Container Won't Start

```bash
# Check task logs
aws logs get-log-events \
  --log-group-name /ecs/oncolife-patient-api \
  --log-stream-name ecs/patient-api/xxx

# Check task status
aws ecs describe-tasks \
  --cluster oncolife-production \
  --tasks $(aws ecs list-tasks --cluster oncolife-production --query 'taskArns[0]' --output text)
```

### Database Connection Issues

```bash
# Verify security group allows traffic from ECS
aws ec2 describe-security-groups --group-ids sg-database

# Test connection from bastion
psql -h YOUR_RDS_ENDPOINT -U oncolife_admin -d oncolife_patient
```

### Education Not Loading

```bash
# Check S3 bucket has files
aws s3 ls s3://oncolife-education-${ACCOUNT_ID}/symptoms/ --recursive

# Check database has documents
psql -c "SELECT COUNT(*) FROM education_documents WHERE status = 'active';"
```

---

## 📋 Post-Deployment Checklist

### Security
- [ ] RDS encrypted at rest
- [ ] S3 buckets block public access
- [ ] ALB using HTTPS only
- [ ] WAF enabled on ALB
- [ ] Security groups follow least privilege
- [ ] Secrets Manager used for credentials
- [ ] CloudTrail enabled

### Monitoring
- [ ] CloudWatch log groups created
- [ ] Alarms configured
- [ ] Dashboard created
- [ ] SNS topic for alerts

### Application
- [ ] Health endpoint returns 200
- [ ] Authentication works
- [ ] Symptom checker completes
- [ ] Education delivered
- [ ] Summaries generated
- [ ] Fax webhook receives data

---

## 📞 Support

For deployment issues, check:
1. CloudWatch Logs: `/ecs/oncolife-patient-api`
2. ECS Service Events
3. ALB Target Group Health
4. RDS Connection Logs

---

*Last Updated: January 2026*

