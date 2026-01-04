# OncoLife Patient API - AWS Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the OncoLife Patient API to AWS.

---

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Docker** installed
4. **PostgreSQL** database (AWS RDS recommended)
5. **AWS Cognito** User Pool configured
6. **AWS S3** bucket for referral documents (onboarding)
7. **AWS SES** verified sender email (onboarding)
8. **AWS SNS** for SMS (onboarding)
9. **Fax Provider** (Sinch/Twilio) with webhook configured

---

## Architecture on AWS

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          AWS Infrastructure                               │
│                                                                           │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────┐       │
│  │   Route53   │ ───► │     ALB     │ ───► │   ECS / Fargate     │       │
│  │   (DNS)     │      │ (Load Bal.) │      │ (patient-api:8000)  │       │
│  └─────────────┘      └─────────────┘      └──────────┬──────────┘       │
│                                                       │                   │
│  ┌────────────────────────────────────────────────────┼─────────────────┐│
│  │                     ONBOARDING FLOW                │                  ││
│  │  ┌───────────┐    ┌───────────┐    ┌───────────────▼───────────────┐ ││
│  │  │ Fax       │───►│ Webhook   │───►│      S3 (Referrals)           │ ││
│  │  │ (Sinch)   │    │ /fax/sinch│    │ s3://oncolife-referrals/      │ ││
│  │  └───────────┘    └───────────┘    │ (KMS Encrypted)               │ ││
│  │                                    └───────────────┬───────────────┘ ││
│  │                                                    │                  ││
│  │  ┌───────────┐    ┌───────────┐    ┌───────────────▼───────────────┐ ││
│  │  │  SES      │◄───│ Cognito   │◄───│      Textract (OCR)           │ ││
│  │  │ (Email)   │    │ (Account) │    │ Extract: Name, DOB, Cancer... │ ││
│  │  └───────────┘    └───────────┘    └───────────────────────────────┘ ││
│  │  ┌───────────┐                                                        ││
│  │  │  SNS      │ (SMS notifications)                                    ││
│  │  └───────────┘                                                        ││
│  └───────────────────────────────────────────────────────────────────────┘│
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐│
│  │                        Private Subnet                                  ││
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                  ││
│  │  │    RDS      │   │   Cognito   │   │    S3       │                  ││
│  │  │ PostgreSQL  │   │ User Pool   │   │  (logs)     │                  ││
│  │  └─────────────┘   └─────────────┘   └─────────────┘                  ││
│  └───────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Options

### Option 1: AWS ECS with Fargate (Recommended)

Fully managed container orchestration.

### Option 2: AWS Elastic Beanstalk

Simplified deployment with managed infrastructure.

### Option 3: AWS EC2

Traditional server deployment.

---

## Option 1: ECS with Fargate

### Step 1: Create ECR Repository

```bash
#!/bin/bash
# scripts/create-ecr.sh

AWS_REGION=${AWS_REGION:-"us-west-2"}
ECR_REPO_NAME="oncolife-patient-api"

# Create ECR repository
aws ecr create-repository \
    --repository-name $ECR_REPO_NAME \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true

echo "ECR Repository created: $ECR_REPO_NAME"
```

### Step 2: Build and Push Docker Image

```bash
#!/bin/bash
# scripts/build-and-push.sh

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-"us-west-2"}
ECR_REPO_NAME="oncolife-patient-api"
IMAGE_TAG=${IMAGE_TAG:-"latest"}

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_URI

# Build Docker image
docker build -t $ECR_REPO_NAME:$IMAGE_TAG \
    -f apps/patient-platform/patient-api/Dockerfile \
    apps/patient-platform/patient-api/

# Tag and push
docker tag $ECR_REPO_NAME:$IMAGE_TAG $ECR_URI/$ECR_REPO_NAME:$IMAGE_TAG
docker push $ECR_URI/$ECR_REPO_NAME:$IMAGE_TAG

echo "Image pushed: $ECR_URI/$ECR_REPO_NAME:$IMAGE_TAG"
```

### Step 3: Create ECS Cluster

```bash
#!/bin/bash
# scripts/create-ecs-cluster.sh

CLUSTER_NAME="oncolife-production"
AWS_REGION=${AWS_REGION:-"us-west-2"}

aws ecs create-cluster \
    --cluster-name $CLUSTER_NAME \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy \
        capacityProvider=FARGATE,weight=1 \
        capacityProvider=FARGATE_SPOT,weight=1 \
    --region $AWS_REGION

echo "ECS Cluster created: $CLUSTER_NAME"
```

### Step 4: Create Task Definition

Create file: `ecs-task-definition.json`

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
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "AWS_REGION", "value": "us-west-2"}
      ],
      "secrets": [
        {
          "name": "POSTGRES_HOST",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db:host::"
        },
        {
          "name": "POSTGRES_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db:password::"
        },
        {
          "name": "COGNITO_CLIENT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito:client_secret::"
        }
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

Register the task definition:

```bash
#!/bin/bash
# scripts/register-task.sh

aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition.json \
    --region us-west-2
```

### Step 5: Create ECS Service

```bash
#!/bin/bash
# scripts/create-service.sh

CLUSTER_NAME="oncolife-production"
SERVICE_NAME="patient-api-service"
TASK_DEFINITION="oncolife-patient-api"
SUBNET_IDS="subnet-xxx,subnet-yyy"  # Your private subnets
SECURITY_GROUP="sg-xxx"              # Your security group
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:..."

aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_DEFINITION \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
    --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=patient-api,containerPort=8000" \
    --health-check-grace-period-seconds 120 \
    --region us-west-2
```

### Step 6: Create Application Load Balancer

```bash
#!/bin/bash
# scripts/create-alb.sh

VPC_ID="vpc-xxx"
SUBNET_IDS="subnet-xxx subnet-yyy"
SECURITY_GROUP="sg-xxx"
CERT_ARN="arn:aws:acm:us-west-2:xxx:certificate/xxx"

# Create ALB
aws elbv2 create-load-balancer \
    --name oncolife-api-alb \
    --subnets $SUBNET_IDS \
    --security-groups $SECURITY_GROUP \
    --scheme internet-facing \
    --type application

# Create Target Group
aws elbv2 create-target-group \
    --name patient-api-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /health \
    --health-check-interval-seconds 30

# Create HTTPS Listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=$CERT_ARN \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

---

## Option 2: Elastic Beanstalk

### Step 1: Create Procfile

```
# apps/patient-platform/patient-api/Procfile
web: uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 2: Create .ebextensions

Create `apps/patient-platform/patient-api/.ebextensions/01_python.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: main:app

packages:
  yum:
    postgresql-devel: []
```

### Step 3: Deploy

```bash
#!/bin/bash
# scripts/eb-deploy.sh

cd apps/patient-platform/patient-api

# Initialize EB (first time)
eb init oncolife-patient-api \
    --platform "Python 3.11" \
    --region us-west-2

# Create environment (first time)
eb create production \
    --instance-type t3.medium \
    --elb-type application \
    --vpc.id vpc-xxx \
    --vpc.elbsubnets subnet-xxx,subnet-yyy \
    --vpc.ec2subnets subnet-zzz,subnet-www

# Deploy (subsequent times)
eb deploy production
```

---

## Option 3: EC2 Deployment

### Step 1: Launch EC2 Instance

```bash
#!/bin/bash
# scripts/launch-ec2.sh

aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxx \
    --subnet-id subnet-xxx \
    --iam-instance-profile Name=OncolifeEC2Role \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=oncolife-patient-api}]' \
    --user-data file://user-data.sh
```

### Step 2: User Data Script

Create `user-data.sh`:

```bash
#!/bin/bash
# EC2 User Data Script

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /opt
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith/apps/patient-platform/patient-api

# Create .env file from Secrets Manager
aws secretsmanager get-secret-value \
    --secret-id oncolife/patient-api/env \
    --query SecretString \
    --output text > .env

# Start application
docker-compose up -d
```

---

## Database Setup (RDS PostgreSQL)

### Create RDS Instance

```bash
#!/bin/bash
# scripts/create-rds.sh

aws rds create-db-instance \
    --db-instance-identifier oncolife-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 15 \
    --master-username oncolife_admin \
    --master-user-password "SECURE_PASSWORD" \
    --allocated-storage 100 \
    --storage-type gp3 \
    --vpc-security-group-ids sg-xxx \
    --db-subnet-group-name oncolife-db-subnet \
    --multi-az \
    --backup-retention-period 7 \
    --storage-encrypted \
    --kms-key-id alias/oncolife-rds-key
```

### Run Migrations

```bash
#!/bin/bash
# scripts/run-migrations.sh

# SSH into bastion or use SSM Session Manager
aws ssm start-session --target i-xxx

# Run migrations
cd /opt/Oncolife_Monolith/apps/patient-platform/patient-api
source venv/bin/activate
alembic upgrade head
```

---

## Patient Onboarding AWS Setup (NEW)

### Step 1: Create S3 Bucket for Referrals

```bash
#!/bin/bash
# scripts/create-referral-bucket.sh

BUCKET_NAME="oncolife-referrals"
AWS_REGION=${AWS_REGION:-"us-west-2"}

# Create bucket with encryption
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $AWS_REGION \
    --create-bucket-configuration LocationConstraint=$AWS_REGION

# Enable versioning (required for HIPAA)
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

# Enable server-side encryption with KMS
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "aws:kms",
                    "KMSMasterKeyID": "alias/oncolife-referrals-key"
                }
            }
        ]
    }'

# Block public access
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "S3 bucket created: $BUCKET_NAME"
```

### Step 2: Configure SES for Welcome Emails

```bash
#!/bin/bash
# scripts/setup-ses.sh

SENDER_EMAIL="noreply@oncolife.com"
AWS_REGION=${AWS_REGION:-"us-west-2"}

# Verify email identity (or domain)
aws ses verify-email-identity \
    --email-address $SENDER_EMAIL \
    --region $AWS_REGION

# Create email template for welcome message
aws ses create-template \
    --template '{
        "TemplateName": "oncolife-welcome",
        "SubjectPart": "Welcome to OncoLife - Your Personal Health Companion",
        "HtmlPart": "<html>...</html>",
        "TextPart": "Welcome to OncoLife..."
    }' \
    --region $AWS_REGION

echo "SES configured for: $SENDER_EMAIL"
```

### Step 3: Configure SNS for SMS

```bash
#!/bin/bash
# scripts/setup-sns.sh

AWS_REGION=${AWS_REGION:-"us-west-2"}

# Set default SMS attributes
aws sns set-sms-attributes \
    --attributes '{
        "DefaultSMSType": "Transactional",
        "DefaultSenderID": "OncoLife"
    }' \
    --region $AWS_REGION

echo "SNS SMS configured"
```

### Step 4: Create IAM Role for Onboarding

```bash
#!/bin/bash
# scripts/create-onboarding-role.sh

ROLE_NAME="OncolifeOnboardingRole"

# Create role
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Attach policy for S3
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name "S3ReferralAccess" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject"],
                "Resource": "arn:aws:s3:::oncolife-referrals/*"
            }
        ]
    }'

# Attach policy for Textract
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name "TextractAccess" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "textract:AnalyzeDocument",
                    "textract:StartDocumentAnalysis",
                    "textract:GetDocumentAnalysis"
                ],
                "Resource": "*"
            }
        ]
    }'

# Attach policy for SES
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name "SESAccess" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["ses:SendEmail", "ses:SendRawEmail"],
                "Resource": "*"
            }
        ]
    }'

# Attach policy for SNS
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name "SNSAccess" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["sns:Publish"],
                "Resource": "*"
            }
        ]
    }'

# Attach policy for Cognito (admin user creation)
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name "CognitoAdminAccess" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminDeleteUser",
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminRespondToAuthChallenge"
                ],
                "Resource": "arn:aws:cognito-idp:*:*:userpool/*"
            }
        ]
    }'

echo "IAM role created: $ROLE_NAME"
```

### Step 5: Configure Fax Provider Webhook

For **Sinch**:
1. Log into Sinch Dashboard
2. Navigate to Fax → Numbers
3. Select your dedicated fax number
4. Configure webhook:
   - URL: `https://api.oncolife.com/api/v1/onboarding/webhook/fax/sinch`
   - Events: `fax.received`
   - Secret: Same as `FAX_WEBHOOK_SECRET` in your `.env`

For **Twilio**:
1. Log into Twilio Console
2. Navigate to Fax → Manage → Fax Numbers
3. Configure incoming webhook:
   - URL: `https://api.oncolife.com/api/v1/onboarding/webhook/fax/twilio`
   - Method: POST

---

## AWS Cognito Setup

### Create User Pool

```bash
#!/bin/bash
# scripts/create-cognito.sh

aws cognito-idp create-user-pool \
    --pool-name oncolife-patients \
    --auto-verified-attributes email \
    --username-attributes email \
    --mfa-configuration OFF \
    --email-configuration SourceArn=arn:aws:ses:us-west-2:xxx:identity/noreply@oncolife.com \
    --admin-create-user-config AllowAdminCreateUserOnly=false \
    --schema Name=email,Required=true Name=given_name,Required=true Name=family_name,Required=true

# Create App Client
aws cognito-idp create-user-pool-client \
    --user-pool-id us-west-2_xxx \
    --client-name patient-api-client \
    --generate-secret \
    --explicit-auth-flows ADMIN_NO_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --read-attributes email given_name family_name \
    --write-attributes email given_name family_name
```

---

## Environment Configuration

### Secrets Manager Setup

```bash
#!/bin/bash
# scripts/create-secrets.sh

# Database credentials
aws secretsmanager create-secret \
    --name oncolife/db \
    --secret-string '{
        "host": "oncolife-db.xxx.us-west-2.rds.amazonaws.com",
        "port": "5432",
        "username": "oncolife_admin",
        "password": "SECURE_PASSWORD",
        "patient_db": "oncolife_patient",
        "doctor_db": "oncolife_doctor"
    }'

# Cognito credentials
aws secretsmanager create-secret \
    --name oncolife/cognito \
    --secret-string '{
        "user_pool_id": "us-west-2_xxx",
        "client_id": "xxx",
        "client_secret": "xxx"
    }'

# Onboarding secrets (NEW)
aws secretsmanager create-secret \
    --name oncolife/onboarding \
    --secret-string '{
        "fax_webhook_secret": "your_webhook_secret",
        "ses_sender_email": "noreply@oncolife.com",
        "s3_referral_bucket": "oncolife-referrals"
    }'
```

---

## Monitoring & Logging

### CloudWatch Log Group

```bash
aws logs create-log-group \
    --log-group-name /ecs/oncolife-patient-api

aws logs put-retention-policy \
    --log-group-name /ecs/oncolife-patient-api \
    --retention-in-days 30
```

### CloudWatch Alarms

```bash
#!/bin/bash
# scripts/create-alarms.sh

# High CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PatientAPI-HighCPU" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-west-2:xxx:oncolife-alerts \
    --dimensions Name=ClusterName,Value=oncolife-production Name=ServiceName,Value=patient-api-service

# 5xx Error alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PatientAPI-5xxErrors" \
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

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Patient API

on:
  push:
    branches: [main]
    paths:
      - 'apps/patient-platform/patient-api/**'

env:
  AWS_REGION: us-west-2
  ECR_REPOSITORY: oncolife-patient-api
  ECS_CLUSTER: oncolife-production
  ECS_SERVICE: patient-api-service

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            -f apps/patient-platform/patient-api/Dockerfile \
            apps/patient-platform/patient-api/
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment
```

---

## Dockerfile

Ensure this Dockerfile exists at `apps/patient-platform/patient-api/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Quick Start Commands

```bash
# 1. Set up infrastructure
./scripts/create-ecr.sh
./scripts/create-rds.sh
./scripts/create-cognito.sh
./scripts/create-secrets.sh
./scripts/create-ecs-cluster.sh

# 2. Build and deploy
./scripts/build-and-push.sh
./scripts/register-task.sh
./scripts/create-alb.sh
./scripts/create-service.sh

# 3. Verify deployment
aws ecs describe-services \
    --cluster oncolife-production \
    --services patient-api-service

# 4. Check logs
aws logs tail /ecs/oncolife-patient-api --follow
```

---

## Rollback Procedure

```bash
#!/bin/bash
# scripts/rollback.sh

PREVIOUS_TASK_DEF="oncolife-patient-api:5"  # Previous version

aws ecs update-service \
    --cluster oncolife-production \
    --service patient-api-service \
    --task-definition $PREVIOUS_TASK_DEF \
    --force-new-deployment
```

---

## Cost Optimization Tips

1. Use **Fargate Spot** for non-critical workloads (up to 70% savings)
2. Use **Reserved Capacity** for RDS (up to 30% savings)
3. Enable **Auto Scaling** based on CPU/Memory metrics
4. Use **S3 Intelligent-Tiering** for logs
5. Consider **AWS Savings Plans** for consistent workloads

---

## Security Checklist

### General
- [ ] Enable VPC Flow Logs
- [ ] Configure Security Groups (least privilege)
- [ ] Enable RDS encryption at rest
- [ ] Use Secrets Manager for credentials
- [ ] Enable CloudTrail for audit logging
- [ ] Configure WAF on ALB
- [ ] Enable GuardDuty for threat detection
- [ ] Set up IAM roles with least privilege

### Patient Onboarding (HIPAA)
- [ ] S3 bucket has versioning enabled
- [ ] S3 bucket has KMS encryption
- [ ] S3 bucket blocks all public access
- [ ] Fax webhook uses HTTPS only
- [ ] Fax webhook signature validation enabled
- [ ] SES sender email verified
- [ ] Cognito password policy meets requirements
- [ ] Onboarding notification logs retained
- [ ] PHI data encrypted in transit and at rest

---

*Last Updated: January 2026*

