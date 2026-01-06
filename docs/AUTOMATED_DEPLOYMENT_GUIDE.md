# OncoLife Automated Deployment Guide

<div align="center">

## 🚀 Deploy OncoLife to AWS in One Command

**Version 1.0 | January 2026**

</div>

---

## Overview

This guide walks you through deploying the complete OncoLife platform to AWS using our **automated deployment script**. The script handles everything from VPC creation to running services.

| What | Details |
|------|---------|
| **Time Required** | 20-30 minutes |
| **Skill Level** | Basic (just run the script!) |
| **What You Need** | AWS account, Docker Desktop |
| **What Gets Created** | Complete production environment |

---

## Prerequisites Checklist

Before running the script, ensure you have:

- [ ] **AWS Account** with Administrator access
- [ ] **AWS CLI** installed and configured
- [ ] **Docker Desktop** installed and running
- [ ] **PowerShell** (Windows) or Terminal (Mac/Linux)
- [ ] **Git** installed

---

## Step 1: Install Required Tools

### 1.1 Install AWS CLI

**Windows:**
```powershell
# Download and run the MSI installer from:
# https://aws.amazon.com/cli/

# Verify installation
aws --version
# Expected: aws-cli/2.x.x ...
```

**Mac:**
```bash
brew install awscli

# Verify
aws --version
```

### 1.2 Install Docker Desktop

Download from: https://www.docker.com/products/docker-desktop/

After installation:
1. Start Docker Desktop
2. Wait for it to fully start (whale icon stops animating)
3. Verify:
```powershell
docker --version
# Expected: Docker version 24.x.x ...
```

### 1.3 Configure AWS Credentials

```powershell
aws configure
```

Enter when prompted:
```
AWS Access Key ID:     [Your access key]
AWS Secret Access Key: [Your secret key]
Default region name:   us-west-2
Default output format: json
```

**Verify AWS is configured:**
```powershell
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-user"
}
```

---

## Step 2: Clone the Repository

```powershell
git clone https://github.com/nbsaKanasu/Oncolife_Monolith.git
cd Oncolife_Monolith
```

---

## Step 3: Run the Automated Deployment

> ⚠️ **IMPORTANT**: Use **PowerShell** on Windows, not Git Bash!

### 3.1 Start the Deployment

```powershell
.\scripts\aws\full-deploy.ps1
```

### 3.2 When Prompted, Enter Database Password

The script will ask for one input:

```
Enter a password for the database.
Requirements: 8+ chars, letters, numbers, no @/"/spaces
Database Password: ********
```

**Choose a strong password like:** `OncoLife2026Prod!`

### 3.3 Wait for Completion

The script will show progress:

```
=============================================
STEP 1: Checking Prerequisites
=============================================
  ✓ AWS Account: 123456789012
  ✓ Docker is running
  ✓ Project directory verified
  ✓ Region: us-west-2

=============================================
STEP 2: Creating VPC and Networking
=============================================
  → Creating VPC...
  ✓ VPC created: vpc-0abc123def456
  → Creating Internet Gateway...
  ✓ Internet Gateway attached
  ...
```

**Do not close the terminal!** The deployment takes 20-30 minutes.

---

## Step 4: Deployment Complete!

When finished, you'll see:

```
╔══════════════════════════════════════════════════════════════╗
║              DEPLOYMENT COMPLETE!                            ║
╚══════════════════════════════════════════════════════════════╝

Duration: 25 minutes 30 seconds

ACCESS URLS:
  Patient API:      http://oncolife-patient-alb-xxxxx.elb.amazonaws.com
  Patient API Docs: http://oncolife-patient-alb-xxxxx.elb.amazonaws.com/docs
  Doctor API:       http://oncolife-doctor-alb-xxxxx.elb.amazonaws.com
  Doctor API Docs:  http://oncolife-doctor-alb-xxxxx.elb.amazonaws.com/docs

Configuration saved to: deployment-config-20260106-143022.json
```

### 4.1 Test Your Deployment

Open a browser and test:

```
# Patient API Health Check
http://[PATIENT_ALB_DNS]/health

# Patient API Documentation (Swagger UI)
http://[PATIENT_ALB_DNS]/docs

# Doctor API Health Check
http://[DOCTOR_ALB_DNS]/health

# Doctor API Documentation (Swagger UI)
http://[DOCTOR_ALB_DNS]/docs
```

---

## Step 5: Create Databases (Required)

After deployment, you need to create the databases. Connect to RDS and run:

### Option A: Using a Bastion Host

```bash
# SSH to bastion host, then:
psql -h [RDS_ENDPOINT] -U oncolife_admin -d postgres

# In PostgreSQL:
CREATE DATABASE oncolife_patient;
CREATE DATABASE oncolife_doctor;
GRANT ALL PRIVILEGES ON DATABASE oncolife_patient TO oncolife_admin;
GRANT ALL PRIVILEGES ON DATABASE oncolife_doctor TO oncolife_admin;
\q
```

### Option B: Using AWS RDS Query Editor

1. Go to AWS Console → RDS → Query Editor
2. Connect to your database
3. Run the SQL commands above

---

## Step 6: Run Database Migrations

From a machine that can reach RDS:

```bash
# Patient API migrations
cd apps/patient-platform/patient-api
pip install -r requirements.txt
export DATABASE_URL=postgresql://oncolife_admin:PASSWORD@RDS_ENDPOINT:5432/oncolife_patient
alembic upgrade head

# Doctor API migrations
cd ../../doctor-platform/doctor-api
pip install -r requirements.txt
export DATABASE_URL=postgresql://oncolife_admin:PASSWORD@RDS_ENDPOINT:5432/oncolife_doctor
alembic upgrade head
```

---

## What Gets Created

The script automatically creates all these AWS resources:

### Networking
| Resource | Name | Purpose |
|----------|------|---------|
| VPC | oncolife-vpc | Isolated network |
| Public Subnet 1 | 10.0.1.0/24 | ALB, NAT Gateway |
| Public Subnet 2 | 10.0.2.0/24 | ALB (multi-AZ) |
| Private Subnet 1 | 10.0.10.0/24 | ECS Tasks, RDS |
| Private Subnet 2 | 10.0.11.0/24 | ECS Tasks, RDS (multi-AZ) |
| Internet Gateway | oncolife-igw | Public internet access |
| NAT Gateway | oncolife-nat | Private subnet internet access |

### Security
| Resource | Purpose |
|----------|---------|
| ALB Security Group | Allow HTTP/HTTPS from internet |
| ECS Security Group | Allow traffic from ALB only |
| RDS Security Group | Allow PostgreSQL from ECS only |

### Database
| Resource | Details |
|----------|---------|
| RDS PostgreSQL | db.t3.medium, 100GB, encrypted |
| Databases | oncolife_patient, oncolife_doctor |

### Compute
| Resource | Details |
|----------|---------|
| ECS Cluster | oncolife-production |
| Patient API Service | 2 Fargate tasks |
| Doctor API Service | 2 Fargate tasks |

### Load Balancing
| Resource | Port | Target |
|----------|------|--------|
| Patient ALB | 80 → 8000 | Patient API |
| Doctor ALB | 80 → 8001 | Doctor API |

### Storage & Secrets
| Resource | Purpose |
|----------|---------|
| ECR Repositories | Docker images |
| S3 Buckets | Referrals, Education content |
| Secrets Manager | Database credentials, Cognito secrets |

### Authentication
| Resource | Purpose |
|----------|---------|
| Cognito User Pool | Patient authentication |
| App Client | API authentication |

---

## Deployment Options

### Different Region

```powershell
.\scripts\aws\full-deploy.ps1 -Region us-east-1
```

### Use Existing VPC

If you already have a VPC:

```powershell
.\scripts\aws\full-deploy.ps1 -SkipVPC
```

The script will prompt you for:
- VPC ID
- Public Subnet IDs (2)
- Private Subnet IDs (2)

### Use Existing RDS

If you already have an RDS instance:

```powershell
.\scripts\aws\full-deploy.ps1 -SkipRDS
```

The script will prompt you for:
- RDS Endpoint
- Database Password

### Skip Docker Build

To use existing images in ECR:

```powershell
.\scripts\aws\full-deploy.ps1 -SkipBuild
```

### Combine Options

```powershell
.\scripts\aws\full-deploy.ps1 -Region us-east-1 -SkipVPC -SkipRDS
```

---

## Troubleshooting

### Script Fails Early

**Error:** `AWS CLI not configured`
```powershell
# Fix: Run aws configure
aws configure
```

**Error:** `Docker not running`
```powershell
# Fix: Start Docker Desktop and wait for it to fully start
```

### VPC Creation Fails

**Error:** `VPC limit exceeded`
```powershell
# Fix: Delete unused VPCs or request limit increase
# Or use -SkipVPC with existing VPC
.\scripts\aws\full-deploy.ps1 -SkipVPC
```

### RDS Takes Too Long

RDS creation takes 10-15 minutes. If it times out:
```powershell
# Check status manually
aws rds describe-db-instances --db-instance-identifier oncolife-db --query 'DBInstances[0].DBInstanceStatus'

# When it shows "available", run:
.\scripts\aws\full-deploy.ps1 -SkipVPC -SkipRDS
```

### Tasks Stay in PENDING

Check CloudWatch logs:
```powershell
aws logs tail "/ecs/oncolife-patient-api" --since 10m
```

Common causes:
- Secrets Manager permissions
- Security group rules
- NAT Gateway not ready

### Health Checks Failing

Wait 5 minutes after deployment, then check:
```powershell
# Check service status
aws ecs describe-services `
    --cluster oncolife-production `
    --services patient-api-service doctor-api-service `
    --query 'services[*].{Name:serviceName,Running:runningCount}'
```

### For More Help

See: [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md)

---

## Saving Your Configuration

After deployment, a config file is saved:

```
deployment-config-20260106-143022.json
```

This contains all resource IDs. **Keep this file safe!**

```json
{
    "AccountId": "123456789012",
    "Region": "us-west-2",
    "VpcId": "vpc-0abc123...",
    "PublicSubnet1": "subnet-...",
    "RdsEndpoint": "oncolife-db.xxxxx.rds.amazonaws.com",
    "PatientAlbDns": "oncolife-patient-alb-xxxxx.elb.amazonaws.com",
    "DoctorAlbDns": "oncolife-doctor-alb-xxxxx.elb.amazonaws.com",
    ...
}
```

---

## Next Steps After Deployment

1. **✅ Create Databases** - See Step 5 above
2. **✅ Run Migrations** - See Step 6 above
3. **⬜ Set Up Custom Domains** - See [STEP_BY_STEP_DEPLOYMENT.md](STEP_BY_STEP_DEPLOYMENT.md) Section 11
4. **⬜ Configure HTTPS** - Request ACM certificates and add HTTPS listeners
5. **⬜ Set Up CI/CD** - Configure GitHub Actions with your AWS credentials
6. **⬜ Deploy Frontend** - Use S3 + CloudFront or ECS

---

## Cleanup (Delete Everything)

To delete all created resources:

```powershell
# Delete ECS Services
aws ecs update-service --cluster oncolife-production --service patient-api-service --desired-count 0
aws ecs update-service --cluster oncolife-production --service doctor-api-service --desired-count 0
aws ecs delete-service --cluster oncolife-production --service patient-api-service
aws ecs delete-service --cluster oncolife-production --service doctor-api-service

# Delete ALBs
aws elbv2 delete-load-balancer --load-balancer-arn [PATIENT_ALB_ARN]
aws elbv2 delete-load-balancer --load-balancer-arn [DOCTOR_ALB_ARN]

# Delete RDS
aws rds delete-db-instance --db-instance-identifier oncolife-db --skip-final-snapshot

# Delete VPC (will fail if resources still exist)
# Use AWS Console for easier cleanup
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `.\scripts\aws\full-deploy.ps1` | Deploy everything |
| `.\scripts\aws\full-deploy.ps1 -SkipVPC` | Use existing VPC |
| `.\scripts\aws\full-deploy.ps1 -SkipRDS` | Use existing RDS |
| `.\scripts\aws\full-deploy.ps1 -SkipBuild` | Use existing Docker images |
| `.\scripts\aws\full-deploy.ps1 -Region us-east-1` | Deploy to different region |

---

## Support

| Resource | Link |
|----------|------|
| Troubleshooting | [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) |
| Manual Deployment | [STEP_BY_STEP_DEPLOYMENT.md](STEP_BY_STEP_DEPLOYMENT.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Developer Guide | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |

---

<div align="center">

**Happy Deploying! 🚀**

*OncoLife Platform | © 2026*

</div>
