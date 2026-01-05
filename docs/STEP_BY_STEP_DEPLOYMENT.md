# OncoLife - Complete AWS Deployment Guide

**Version 2.0 | Updated January 2026**

> ⚠️ **IMPORTANT**: This guide includes fixes for common deployment errors. Read each section carefully, especially the "Common Errors" boxes.

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Windows vs Linux/Mac Notes](#2-windows-vs-linuxmac-notes)
3. [Phase 1: AWS Foundation](#3-phase-1-aws-foundation)
4. [Phase 2: Container Infrastructure](#4-phase-2-container-infrastructure)
5. [Phase 3: Build and Deploy](#5-phase-3-build-and-deploy)
6. [Phase 4: Database Setup](#6-phase-4-database-setup)
7. [Phase 5: Verification](#7-phase-5-verification)
8. [Troubleshooting Guide](#8-troubleshooting-guide)
9. [Common Errors and Fixes](#9-common-errors-and-fixes)

---

## 1. Pre-Deployment Checklist

### Required Tools

| Tool | Version | Verify Command | Install Guide |
|------|---------|----------------|---------------|
| AWS CLI | v2.x | `aws --version` | [AWS CLI Install](https://aws.amazon.com/cli/) |
| Docker Desktop | Latest | `docker --version` | [Docker Install](https://docker.com) |
| Git | Latest | `git --version` | [Git Install](https://git-scm.com) |
| Python | 3.11+ | `python --version` | [Python Install](https://python.org) |
| Node.js | 18+ | `node --version` | [Node Install](https://nodejs.org) |

### AWS Account Setup

- [ ] AWS Account with **Administrator Access**
- [ ] AWS CLI configured: `aws configure`
- [ ] Region set to `us-west-2` (or your preferred region)

**Verify AWS Setup:**
```bash
# Test AWS credentials
aws sts get-caller-identity

# Should return:
# {
#     "UserId": "AIDAXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

### Clone Repository

```bash
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith
```

---

## 2. Windows vs Linux/Mac Notes

> ⚠️ **CRITICAL FOR WINDOWS USERS**: Git Bash can mangle paths. Use **PowerShell** or **Command Prompt** for AWS CLI commands.

### Windows (PowerShell) - Use This!

```powershell
# Set your region and get account ID
$AWS_REGION = "us-west-2"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# Verify
Write-Host "Account: $ACCOUNT_ID, Region: $AWS_REGION"
```

### Linux/Mac (Bash)

```bash
# Set your region and get account ID
export AWS_REGION="us-west-2"
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Verify
echo "Account: $ACCOUNT_ID, Region: $AWS_REGION"
```

### Common Windows Path Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid parameter: /ecs/...` | Git Bash converts `/ecs` to `C:/Program Files/Git/ecs` | Use PowerShell instead |
| `InvalidParameterException` on log group | Path mangling | Run in PowerShell, not Git Bash |

---

## 3. Phase 1: AWS Foundation

### Step 1.1: Create ECS Service-Linked Role (MUST DO FIRST!)

> ⚠️ **CRITICAL**: This role MUST exist before creating ECS clusters. Do this FIRST!

**PowerShell:**
```powershell
# Create ECS service-linked role (ignore error if already exists)
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com

# If you get "InvalidInput... Role already exists" - that's OK, continue
```

**Bash:**
```bash
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com 2>/dev/null || echo "Role already exists - OK"
```

### Step 1.2: Create VPC (Using AWS Console - Recommended)

> Using the console is easier and avoids CLI complexity for VPC.

1. Go to **VPC Console** → **Create VPC**
2. Select **"VPC and more"**
3. Configure:
   - **Name tag auto-generation**: `oncolife`
   - **IPv4 CIDR**: `10.0.0.0/16`
   - **Number of AZs**: `2`
   - **Public subnets**: `2`
   - **Private subnets**: `2`
   - **NAT gateways**: `1 per AZ` (or `1` to save cost)
   - **VPC endpoints**: `S3`
4. Click **Create VPC**
5. Wait for completion (~3 minutes)

**Record these values (you'll need them later):**
```
VPC ID:              vpc-xxxxxxxxx
Public Subnet 1:     subnet-xxxxxxxxx (e.g., 10.0.0.0/24)
Public Subnet 2:     subnet-yyyyyyyyy (e.g., 10.0.16.0/24)
Private Subnet 1:    subnet-zzzzzzzzz (e.g., 10.0.128.0/24)
Private Subnet 2:    subnet-wwwwwwwww (e.g., 10.0.144.0/24)
```

### Step 1.3: Create Security Groups

**PowerShell:**
```powershell
# Get your VPC ID (replace or use your recorded value)
$VPC_ID = "vpc-xxxxxxxxx"

# ALB Security Group (public access)
$SG_ALB = (aws ec2 create-security-group `
    --group-name "oncolife-alb-sg" `
    --description "OncoLife ALB Security Group" `
    --vpc-id $VPC_ID `
    --query 'GroupId' --output text)

Write-Host "ALB Security Group: $SG_ALB"

# Allow HTTPS from internet
aws ec2 authorize-security-group-ingress `
    --group-id $SG_ALB `
    --protocol tcp `
    --port 443 `
    --cidr "0.0.0.0/0"

# Allow HTTP (for redirect)
aws ec2 authorize-security-group-ingress `
    --group-id $SG_ALB `
    --protocol tcp `
    --port 80 `
    --cidr "0.0.0.0/0"

# ECS Security Group (internal)
$SG_ECS = (aws ec2 create-security-group `
    --group-name "oncolife-ecs-sg" `
    --description "OncoLife ECS Security Group" `
    --vpc-id $VPC_ID `
    --query 'GroupId' --output text)

Write-Host "ECS Security Group: $SG_ECS"

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress `
    --group-id $SG_ECS `
    --protocol tcp `
    --port 8000 `
    --source-group $SG_ALB

# RDS Security Group
$SG_RDS = (aws ec2 create-security-group `
    --group-name "oncolife-rds-sg" `
    --description "OncoLife RDS Security Group" `
    --vpc-id $VPC_ID `
    --query 'GroupId' --output text)

Write-Host "RDS Security Group: $SG_RDS"

# Allow PostgreSQL from ECS
aws ec2 authorize-security-group-ingress `
    --group-id $SG_RDS `
    --protocol tcp `
    --port 5432 `
    --source-group $SG_ECS
```

**Bash:**
```bash
VPC_ID="vpc-xxxxxxxxx"

# ALB Security Group
SG_ALB=$(aws ec2 create-security-group \
    --group-name "oncolife-alb-sg" \
    --description "OncoLife ALB Security Group" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)
echo "ALB SG: $SG_ALB"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ALB \
    --protocol tcp --port 443 --cidr "0.0.0.0/0"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ALB \
    --protocol tcp --port 80 --cidr "0.0.0.0/0"

# ECS Security Group
SG_ECS=$(aws ec2 create-security-group \
    --group-name "oncolife-ecs-sg" \
    --description "OncoLife ECS Security Group" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)
echo "ECS SG: $SG_ECS"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ECS \
    --protocol tcp --port 8000 \
    --source-group $SG_ALB

# RDS Security Group
SG_RDS=$(aws ec2 create-security-group \
    --group-name "oncolife-rds-sg" \
    --description "OncoLife RDS Security Group" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)
echo "RDS SG: $SG_RDS"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_RDS \
    --protocol tcp --port 5432 \
    --source-group $SG_ECS
```

### Step 1.4: Create RDS PostgreSQL

```powershell
# Variables (fill in your subnet IDs)
$PRIVATE_SUBNET_1 = "subnet-zzzzzzzzz"
$PRIVATE_SUBNET_2 = "subnet-wwwwwwwww"
$SG_RDS = "sg-xxxxxxxxx"  # from previous step
$DB_PASSWORD = "YourSecurePassword123!"  # Change this!

# Create DB Subnet Group
aws rds create-db-subnet-group `
    --db-subnet-group-name "oncolife-db-subnet" `
    --db-subnet-group-description "OncoLife Database Subnets" `
    --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2

# Create RDS Instance (takes 10-15 minutes)
aws rds create-db-instance `
    --db-instance-identifier "oncolife-db" `
    --db-instance-class "db.t3.medium" `
    --engine "postgres" `
    --engine-version "15" `
    --master-username "oncolife_admin" `
    --master-user-password $DB_PASSWORD `
    --allocated-storage 100 `
    --storage-type "gp3" `
    --storage-encrypted `
    --vpc-security-group-ids $SG_RDS `
    --db-subnet-group-name "oncolife-db-subnet" `
    --no-publicly-accessible `
    --backup-retention-period 7

Write-Host "RDS creating... This takes 10-15 minutes."
Write-Host "Run: aws rds describe-db-instances --db-instance-identifier oncolife-db --query 'DBInstances[0].DBInstanceStatus'"
```

**Wait for RDS to be available:**
```powershell
# Check status (run repeatedly until "available")
aws rds describe-db-instances `
    --db-instance-identifier "oncolife-db" `
    --query 'DBInstances[0].DBInstanceStatus' --output text

# When ready, get the endpoint
$RDS_ENDPOINT = (aws rds describe-db-instances `
    --db-instance-identifier "oncolife-db" `
    --query 'DBInstances[0].Endpoint.Address' --output text)

Write-Host "RDS Endpoint: $RDS_ENDPOINT"
```

### Step 1.5: Create Cognito User Pool

```powershell
# Create User Pool
$POOL_RESULT = (aws cognito-idp create-user-pool `
    --pool-name "oncolife-patients" `
    --auto-verified-attributes "email" `
    --username-attributes "email" `
    --mfa-configuration "OFF" `
    --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":true}}' `
    --admin-create-user-config '{"AllowAdminCreateUserOnly":true}' `
    --query 'UserPool.Id' --output text)

Write-Host "User Pool ID: $POOL_RESULT"

# Create App Client
$CLIENT_RESULT = (aws cognito-idp create-user-pool-client `
    --user-pool-id $POOL_RESULT `
    --client-name "patient-api-client" `
    --generate-secret `
    --explicit-auth-flows "ADMIN_NO_SRP_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" "ALLOW_USER_PASSWORD_AUTH" `
    --query 'UserPoolClient.[ClientId,ClientSecret]' --output text)

Write-Host "Client ID and Secret: $CLIENT_RESULT"
```

### Step 1.6: Create S3 Buckets

```powershell
# Create Referrals Bucket
aws s3api create-bucket `
    --bucket "oncolife-referrals-$ACCOUNT_ID" `
    --region $AWS_REGION `
    --create-bucket-configuration LocationConstraint=$AWS_REGION

# Enable encryption
aws s3api put-bucket-encryption `
    --bucket "oncolife-referrals-$ACCOUNT_ID" `
    --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"aws:kms\"}}]}'

# Block public access
aws s3api put-public-access-block `
    --bucket "oncolife-referrals-$ACCOUNT_ID" `
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create Education Bucket (same settings)
aws s3api create-bucket `
    --bucket "oncolife-education-$ACCOUNT_ID" `
    --region $AWS_REGION `
    --create-bucket-configuration LocationConstraint=$AWS_REGION

aws s3api put-bucket-encryption `
    --bucket "oncolife-education-$ACCOUNT_ID" `
    --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"aws:kms\"}}]}'

aws s3api put-public-access-block `
    --bucket "oncolife-education-$ACCOUNT_ID" `
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

Write-Host "Buckets created: oncolife-referrals-$ACCOUNT_ID, oncolife-education-$ACCOUNT_ID"
```

### Step 1.7: Create Secrets in Secrets Manager

```powershell
# Database credentials (replace with your values!)
$DB_SECRET = @{
    host = $RDS_ENDPOINT
    port = "5432"
    username = "oncolife_admin"
    password = $DB_PASSWORD
    patient_db = "oncolife_patient"
    doctor_db = "oncolife_doctor"
} | ConvertTo-Json -Compress

aws secretsmanager create-secret `
    --name "oncolife/db" `
    --secret-string $DB_SECRET

# Cognito credentials
$COGNITO_SECRET = @{
    user_pool_id = $POOL_RESULT
    client_id = "YOUR_CLIENT_ID"      # From Step 1.5
    client_secret = "YOUR_SECRET"     # From Step 1.5
} | ConvertTo-Json -Compress

aws secretsmanager create-secret `
    --name "oncolife/cognito" `
    --secret-string $COGNITO_SECRET

# Fax webhook secret (generate a random one)
$WEBHOOK_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

aws secretsmanager create-secret `
    --name "oncolife/fax" `
    --secret-string "{`"webhook_secret`":`"$WEBHOOK_SECRET`"}"

Write-Host "Webhook Secret (save this): $WEBHOOK_SECRET"
```

---

## 4. Phase 2: Container Infrastructure

### Step 2.1: Create ECR Repositories

```powershell
# Patient API repository
aws ecr create-repository `
    --repository-name "oncolife-patient-api" `
    --image-scanning-configuration scanOnPush=true

# Doctor API repository
aws ecr create-repository `
    --repository-name "oncolife-doctor-api" `
    --image-scanning-configuration scanOnPush=true
```

### Step 2.2: Create CloudWatch Log Group

> ⚠️ **WINDOWS USERS**: Run this in PowerShell, NOT Git Bash!

```powershell
# Create log groups BEFORE creating ECS resources
aws logs create-log-group --log-group-name "/ecs/oncolife-patient-api"
aws logs create-log-group --log-group-name "/ecs/oncolife-doctor-api"

# Set retention
aws logs put-retention-policy `
    --log-group-name "/ecs/oncolife-patient-api" `
    --retention-in-days 30

aws logs put-retention-policy `
    --log-group-name "/ecs/oncolife-doctor-api" `
    --retention-in-days 30
```

### Step 2.3: Create ECS Cluster

> ⚠️ **If you get "InvalidParameterException" here, you skipped Step 1.1!**

```powershell
aws ecs create-cluster `
    --cluster-name "oncolife-production" `
    --capacity-providers "FARGATE" "FARGATE_SPOT" `
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
```

### Step 2.4: Create IAM Roles

**Task Execution Role:**
```powershell
# Create trust policy file
@'
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}
'@ | Out-File -FilePath "trust-policy.json" -Encoding utf8

# Create role
aws iam create-role `
    --role-name "ecsTaskExecutionRole" `
    --assume-role-policy-document "file://trust-policy.json"

# Attach managed policy
aws iam attach-role-policy `
    --role-name "ecsTaskExecutionRole" `
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"

# Allow Secrets Manager access
aws iam attach-role-policy `
    --role-name "ecsTaskExecutionRole" `
    --policy-arn "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
```

**Task Role (for application permissions):**
```powershell
# Create task role
aws iam create-role `
    --role-name "oncolifeTaskRole" `
    --assume-role-policy-document "file://trust-policy.json"

# Create inline policy
@'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            "Resource": ["arn:aws:s3:::oncolife-*", "arn:aws:s3:::oncolife-*/*"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminRespondToAuthChallenge",
                "cognito-idp:AdminGetUser"
            ],
            "Resource": "*"
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
        }
    ]
}
'@ | Out-File -FilePath "task-policy.json" -Encoding utf8

aws iam put-role-policy `
    --role-name "oncolifeTaskRole" `
    --policy-name "OncolifePermissions" `
    --policy-document "file://task-policy.json"

# Cleanup
Remove-Item "trust-policy.json", "task-policy.json"
```

### Step 2.5: Create ALB and Target Group

```powershell
# Get your public subnet IDs
$PUBLIC_SUBNET_1 = "subnet-xxxxxxxxx"  # From Step 1.2
$PUBLIC_SUBNET_2 = "subnet-yyyyyyyyy"
$SG_ALB = "sg-xxxxxxxxx"  # From Step 1.3

# Create ALB
$ALB_ARN = (aws elbv2 create-load-balancer `
    --name "oncolife-api-alb" `
    --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 `
    --security-groups $SG_ALB `
    --scheme "internet-facing" `
    --type "application" `
    --query 'LoadBalancers[0].LoadBalancerArn' --output text)

Write-Host "ALB ARN: $ALB_ARN"

# Create Target Group
$VPC_ID = "vpc-xxxxxxxxx"  # Your VPC ID

$TG_ARN = (aws elbv2 create-target-group `
    --name "patient-api-tg" `
    --protocol "HTTP" `
    --port 8000 `
    --vpc-id $VPC_ID `
    --target-type "ip" `
    --health-check-path "/health" `
    --health-check-interval-seconds 30 `
    --healthy-threshold-count 2 `
    --unhealthy-threshold-count 3 `
    --query 'TargetGroups[0].TargetGroupArn' --output text)

Write-Host "Target Group ARN: $TG_ARN"

# Create HTTP Listener (redirect to HTTPS)
aws elbv2 create-listener `
    --load-balancer-arn $ALB_ARN `
    --protocol "HTTP" `
    --port 80 `
    --default-actions 'Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'

# For HTTPS, you need an ACM certificate first
# aws elbv2 create-listener --load-balancer-arn $ALB_ARN --protocol HTTPS --port 443 ...
```

### Step 2.6: Register Task Definition

Create `task-definition.json`:

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
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "essential": true,
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DEBUG", "value": "false"},
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "AWS_REGION", "value": "us-west-2"}
      ],
      "secrets": [
        {"name": "PATIENT_DB_HOST", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db-XXXXXX:host::"},
        {"name": "PATIENT_DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db-XXXXXX:password::"},
        {"name": "PATIENT_DB_USER", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db-XXXXXX:username::"},
        {"name": "PATIENT_DB_NAME", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/db-XXXXXX:patient_db::"},
        {"name": "COGNITO_USER_POOL_ID", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito-XXXXXX:user_pool_id::"},
        {"name": "COGNITO_CLIENT_ID", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito-XXXXXX:client_id::"},
        {"name": "COGNITO_CLIENT_SECRET", "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:oncolife/cognito-XXXXXX:client_secret::"}
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

> ⚠️ **IMPORTANT**: Replace `ACCOUNT_ID` and the `-XXXXXX` suffix with your actual secret ARNs!

**Get your secret ARNs:**
```powershell
aws secretsmanager describe-secret --secret-id "oncolife/db" --query 'ARN' --output text
aws secretsmanager describe-secret --secret-id "oncolife/cognito" --query 'ARN' --output text
```

**Register the task definition:**
```powershell
# First, update the JSON file with your ACCOUNT_ID
(Get-Content task-definition.json) -replace 'ACCOUNT_ID', $ACCOUNT_ID | Set-Content task-definition.json

aws ecs register-task-definition --cli-input-json "file://task-definition.json"
```

### Step 2.7: Create ECS Service

> ⚠️ **IMPORTANT**: Create the service ONLY after the task definition exists!

```powershell
$PRIVATE_SUBNET_1 = "subnet-zzzzzzzzz"  # Private subnets!
$PRIVATE_SUBNET_2 = "subnet-wwwwwwwww"
$SG_ECS = "sg-xxxxxxxxx"

aws ecs create-service `
    --cluster "oncolife-production" `
    --service-name "patient-api-service" `
    --task-definition "oncolife-patient-api" `
    --desired-count 1 `
    --launch-type "FARGATE" `
    --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$SG_ECS],assignPublicIp=DISABLED}" `
    --load-balancers "targetGroupArn=$TG_ARN,containerName=patient-api,containerPort=8000" `
    --health-check-grace-period-seconds 120
```

---

## 5. Phase 3: Build and Deploy

### Step 3.1: Build Docker Image

```powershell
cd Oncolife_Monolith

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com"

# Build image
docker build `
    -t "oncolife-patient-api:latest" `
    -f "apps/patient-platform/patient-api/Dockerfile" `
    "apps/patient-platform/patient-api/"

# Tag and push
docker tag "oncolife-patient-api:latest" "$ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/oncolife-patient-api:latest"
docker push "$ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/oncolife-patient-api:latest"
```

### Step 3.2: Force New Deployment

```powershell
aws ecs update-service `
    --cluster "oncolife-production" `
    --service "patient-api-service" `
    --force-new-deployment

# Monitor deployment
aws ecs describe-services `
    --cluster "oncolife-production" `
    --services "patient-api-service" `
    --query 'services[0].{desiredCount:desiredCount,runningCount:runningCount,status:status}'
```

---

## 6. Phase 4: Database Setup

### Step 4.1: Connect to RDS

You'll need a bastion host or SSM Session Manager to connect to RDS in private subnets.

**Option A: Using a Bastion Host**
```bash
# SSH to bastion, then connect
psql -h YOUR_RDS_ENDPOINT -U oncolife_admin -d postgres
```

**Option B: Using RDS Query Editor (AWS Console)**
1. Go to RDS Console → Query Editor
2. Connect to your database

### Step 4.2: Create Databases

```sql
CREATE DATABASE oncolife_patient;
CREATE DATABASE oncolife_doctor;
GRANT ALL PRIVILEGES ON DATABASE oncolife_patient TO oncolife_admin;
GRANT ALL PRIVILEGES ON DATABASE oncolife_doctor TO oncolife_admin;
```

### Step 4.3: Run Migrations

From a machine that can reach RDS (bastion or local with VPN):

```bash
cd apps/patient-platform/patient-api
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

export PATIENT_DB_HOST=your-rds-endpoint
export PATIENT_DB_PORT=5432
export PATIENT_DB_NAME=oncolife_patient
export PATIENT_DB_USER=oncolife_admin
export PATIENT_DB_PASSWORD=your_password

cd src
python -c "
from db.base import Base
from db.session import engine
from db.models import *
Base.metadata.create_all(bind=engine)
print('Tables created!')
"
```

### Step 4.4: Seed Education Data

```bash
python scripts/seed_education.py
```

---

## 7. Phase 5: Verification

### Step 5.1: Get ALB DNS

```powershell
$ALB_DNS = (aws elbv2 describe-load-balancers `
    --names "oncolife-api-alb" `
    --query 'LoadBalancers[0].DNSName' --output text)

Write-Host "API URL: http://$ALB_DNS"
```

### Step 5.2: Test Health Endpoint

```bash
curl http://YOUR_ALB_DNS/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### Step 5.3: Check CloudWatch Logs

```powershell
aws logs tail "/ecs/oncolife-patient-api" --follow
```

---

## 8. Troubleshooting Guide

### Container Won't Start

```powershell
# Get task ARN
$TASK_ARN = (aws ecs list-tasks `
    --cluster "oncolife-production" `
    --query 'taskArns[0]' --output text)

# Describe task for error
aws ecs describe-tasks `
    --cluster "oncolife-production" `
    --tasks $TASK_ARN `
    --query 'tasks[0].{status:lastStatus,reason:stoppedReason}'

# Check logs
aws logs tail "/ecs/oncolife-patient-api" --since 30m
```

### Database Connection Issues

```powershell
# Verify security group allows traffic
aws ec2 describe-security-groups `
    --group-ids $SG_RDS `
    --query 'SecurityGroups[0].IpPermissions'

# Check RDS status
aws rds describe-db-instances `
    --db-instance-identifier "oncolife-db" `
    --query 'DBInstances[0].{status:DBInstanceStatus,endpoint:Endpoint.Address}'
```

### Secrets Not Found

```powershell
# List secrets
aws secretsmanager list-secrets --query 'SecretList[?starts_with(Name, `oncolife`)].Name'

# Get secret ARN (needed for task definition)
aws secretsmanager describe-secret --secret-id "oncolife/db" --query 'ARN'
```

---

## 9. Common Errors and Fixes

### Error: `InvalidParameterException` on Log Groups

**Cause:** Windows Git Bash converts `/ecs/...` to `C:/Program Files/Git/ecs/...`

**Fix:** Use **PowerShell** instead of Git Bash for all AWS CLI commands.

```powershell
# Correct (PowerShell):
aws logs create-log-group --log-group-name "/ecs/oncolife-patient-api"
```

---

### Error: `InvalidParameterException` on CreateCluster

**Cause:** ECS Service-Linked Role doesn't exist.

**Fix:** Create the role FIRST:

```powershell
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com
```

---

### Error: `ServiceNotFoundException` on UpdateService

**Cause:** Trying to update a service that doesn't exist yet.

**Fix:** Use `create-service` first, not `update-service`:

```powershell
# Wrong (service doesn't exist):
aws ecs update-service --cluster ... --service patient-api-service ...

# Correct:
aws ecs create-service --cluster ... --service-name patient-api-service ...
```

---

### Error: `InvalidInput` on CreateServiceLinkedRole

**Message:** "Service role name AWSServiceRoleForECS has been taken"

**Cause:** Role already exists - this is OK!

**Fix:** Ignore this error and continue.

---

### Error: Task Stuck in PENDING

**Cause:** Usually networking or IAM issues.

**Fix:**
1. Check security groups allow traffic
2. Check subnets have route to NAT Gateway
3. Check task execution role has permissions
4. Check secrets ARNs are correct in task definition

---

### Error: Container Exits Immediately

**Cause:** Application crash on startup.

**Fix:**
```powershell
# Check logs
aws logs tail "/ecs/oncolife-patient-api" --since 10m

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Import errors
```

---

## Quick Reference: All Required IDs

Keep this filled in as you deploy:

```
AWS Account ID:        ____________________
AWS Region:            ____________________

VPC:
  VPC ID:              ____________________
  Public Subnet 1:     ____________________
  Public Subnet 2:     ____________________
  Private Subnet 1:    ____________________
  Private Subnet 2:    ____________________

Security Groups:
  ALB SG:              ____________________
  ECS SG:              ____________________
  RDS SG:              ____________________

RDS:
  Endpoint:            ____________________
  Password:            ____________________

Cognito:
  User Pool ID:        ____________________
  Client ID:           ____________________
  Client Secret:       ____________________

ALB:
  ALB ARN:             ____________________
  Target Group ARN:    ____________________
  DNS Name:            ____________________

Secrets Manager ARNs:
  oncolife/db:         ____________________
  oncolife/cognito:    ____________________
  oncolife/fax:        ____________________
```

---

*Document Version: 2.0*
*Last Updated: January 2026*
*© 2026 OncoLife Health Technologies*
