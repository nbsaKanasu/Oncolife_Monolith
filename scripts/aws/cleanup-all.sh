#!/bin/bash
# ===========================================
# DELETE ALL ONCOLIFE AWS RESOURCES
# ===========================================
# This script deletes ALL OncoLife resources to allow a fresh deployment.
#
# Usage: ./scripts/aws/cleanup-all.sh
#
# WARNING: This is DESTRUCTIVE and cannot be undone!
# ===========================================

REGION="${AWS_REGION:-us-west-2}"
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${RED}=========================================="
echo "  DELETE ALL ONCOLIFE AWS RESOURCES"
echo "  Region: $REGION"
echo -e "==========================================${NC}"
echo ""
echo -e "${YELLOW}WARNING: This will delete:${NC}"
echo "  - ECS Services and Cluster"
echo "  - Load Balancers and Target Groups"
echo "  - RDS Database"
echo "  - Cognito User Pools"
echo "  - S3 Buckets"
echo "  - Secrets Manager secrets"
echo "  - ECR Repositories"
echo "  - CloudWatch Log Groups"
echo "  - ALL VPCs named 'oncolife-vpc'"
echo ""
read -p "Type 'DELETE' to confirm: " confirm
if [ "$confirm" != "DELETE" ]; then
  echo "Cancelled."
  exit 1
fi

echo ""
echo -e "${CYAN}Starting cleanup...${NC}"
echo ""

# 1. Delete ECS Services
echo -e "${YELLOW}=== Deleting ECS Services ===${NC}"
aws ecs update-service --cluster oncolife-production --service patient-api-service --desired-count 0 --region $REGION 2>/dev/null || true
aws ecs update-service --cluster oncolife-production --service doctor-api-service --desired-count 0 --region $REGION 2>/dev/null || true
aws ecs delete-service --cluster oncolife-production --service patient-api-service --force --region $REGION 2>/dev/null && echo "  Deleted patient-api-service" || true
aws ecs delete-service --cluster oncolife-production --service doctor-api-service --force --region $REGION 2>/dev/null && echo "  Deleted doctor-api-service" || true

# 2. Delete ECS Cluster
echo -e "${YELLOW}=== Deleting ECS Cluster ===${NC}"
aws ecs delete-cluster --cluster oncolife-production --region $REGION 2>/dev/null && echo "  Deleted oncolife-production cluster" || true

# 3. Delete ALL Load Balancers with "oncolife"
echo -e "${YELLOW}=== Deleting Load Balancers ===${NC}"
for alb in $(aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName,'oncolife')].LoadBalancerArn" --output text --region $REGION 2>/dev/null); do
  name=$(aws elbv2 describe-load-balancers --load-balancer-arns $alb --query 'LoadBalancers[0].LoadBalancerName' --output text --region $REGION)
  aws elbv2 delete-load-balancer --load-balancer-arn $alb --region $REGION
  echo "  Deleted: $name"
done

echo "  Waiting 15s for ALBs to delete..."
sleep 15

# 4. Delete ALL Target Groups
echo -e "${YELLOW}=== Deleting Target Groups ===${NC}"
for tg in $(aws elbv2 describe-target-groups --query "TargetGroups[?contains(TargetGroupName,'patient') || contains(TargetGroupName,'doctor')].TargetGroupArn" --output text --region $REGION 2>/dev/null); do
  name=$(aws elbv2 describe-target-groups --target-group-arns $tg --query 'TargetGroups[0].TargetGroupName' --output text --region $REGION 2>/dev/null)
  aws elbv2 delete-target-group --target-group-arn $tg --region $REGION 2>/dev/null && echo "  Deleted: $name" || true
done

# 5. Delete RDS
echo -e "${YELLOW}=== Deleting RDS ===${NC}"
if aws rds describe-db-instances --db-instance-identifier oncolife-db --region $REGION 2>/dev/null > /dev/null; then
  aws rds delete-db-instance --db-instance-identifier oncolife-db --skip-final-snapshot --delete-automated-backups --region $REGION 2>/dev/null
  echo "  Initiated deletion of oncolife-db (takes 5-10 minutes)"
  echo "  Waiting for RDS deletion..."
  aws rds wait db-instance-deleted --db-instance-identifier oncolife-db --region $REGION 2>/dev/null || true
  echo "  RDS deleted"
else
  echo "  No RDS instance found"
fi

# 6. Delete RDS Subnet Group
aws rds delete-db-subnet-group --db-subnet-group-name oncolife-db-subnet --region $REGION 2>/dev/null && echo "  Deleted DB subnet group" || true

# 7. Delete Cognito
echo -e "${YELLOW}=== Deleting Cognito User Pools ===${NC}"
for pool in $(aws cognito-idp list-user-pools --max-results 60 --query "UserPools[?contains(Name,'oncolife')].Id" --output text --region $REGION 2>/dev/null); do
  aws cognito-idp delete-user-pool --user-pool-id $pool --region $REGION 2>/dev/null && echo "  Deleted pool: $pool" || true
done

# 8. Delete Secrets
echo -e "${YELLOW}=== Deleting Secrets ===${NC}"
aws secretsmanager delete-secret --secret-id oncolife/db --force-delete-without-recovery --region $REGION 2>/dev/null && echo "  Deleted oncolife/db" || true
aws secretsmanager delete-secret --secret-id oncolife/cognito --force-delete-without-recovery --region $REGION 2>/dev/null && echo "  Deleted oncolife/cognito" || true

# 9. Delete S3 Buckets
echo -e "${YELLOW}=== Deleting S3 Buckets ===${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
for bucket in "oncolife-referrals-$ACCOUNT_ID" "oncolife-education-$ACCOUNT_ID"; do
  if aws s3api head-bucket --bucket $bucket 2>/dev/null; then
    aws s3 rm s3://$bucket --recursive --region $REGION 2>/dev/null || true
    aws s3api delete-bucket --bucket $bucket --region $REGION 2>/dev/null && echo "  Deleted: $bucket" || true
  fi
done

# 10. Delete ECR Repositories
echo -e "${YELLOW}=== Deleting ECR Repositories ===${NC}"
for repo in oncolife-patient-api oncolife-doctor-api oncolife-patient-web oncolife-doctor-web; do
  aws ecr delete-repository --repository-name $repo --force --region $REGION 2>/dev/null && echo "  Deleted: $repo" || true
done

# 11. Delete CloudWatch Log Groups
echo -e "${YELLOW}=== Deleting Log Groups ===${NC}"
aws logs delete-log-group --log-group-name /ecs/oncolife-patient-api --region $REGION 2>/dev/null && echo "  Deleted /ecs/oncolife-patient-api" || true
aws logs delete-log-group --log-group-name /ecs/oncolife-doctor-api --region $REGION 2>/dev/null && echo "  Deleted /ecs/oncolife-doctor-api" || true

# 12. Delete ALL OncoLife VPCs
echo -e "${YELLOW}=== Deleting VPCs ===${NC}"
VPC_LIST=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=oncolife-vpc" --query 'Vpcs[*].VpcId' --output text --region $REGION 2>/dev/null)

if [ -n "$VPC_LIST" ]; then
  # First pass: Delete NAT Gateways (they take time)
  for VPC_ID in $VPC_LIST; do
    echo "  Deleting NAT Gateways in $VPC_ID..."
    for nat in $(aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available,pending" --query 'NatGateways[*].NatGatewayId' --output text --region $REGION 2>/dev/null); do
      aws ec2 delete-nat-gateway --nat-gateway-id $nat --region $REGION 2>/dev/null
      echo "    Deleted NAT: $nat"
    done
  done

  echo "  Waiting 90s for NAT Gateways to delete..."
  sleep 90

  # Second pass: Delete everything else
  for VPC_ID in $VPC_LIST; do
    echo "  Cleaning VPC: $VPC_ID"
    
    # Release EIPs
    for eip in $(aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].AllocationId' --output text --region $REGION 2>/dev/null); do
      aws ec2 release-address --allocation-id $eip --region $REGION 2>/dev/null || true
    done
    
    # Delete ENIs
    for eni in $(aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" --query 'NetworkInterfaces[*].NetworkInterfaceId' --output text --region $REGION 2>/dev/null); do
      aws ec2 delete-network-interface --network-interface-id $eni --region $REGION 2>/dev/null || true
    done
    
    # Delete Subnets
    for subnet in $(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region $REGION 2>/dev/null); do
      aws ec2 delete-subnet --subnet-id $subnet --region $REGION 2>/dev/null || true
    done
    
    # Delete IGWs
    for igw in $(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query 'InternetGateways[*].InternetGatewayId' --output text --region $REGION 2>/dev/null); do
      aws ec2 detach-internet-gateway --internet-gateway-id $igw --vpc-id $VPC_ID --region $REGION 2>/dev/null || true
      aws ec2 delete-internet-gateway --internet-gateway-id $igw --region $REGION 2>/dev/null || true
    done
    
    # Delete Route Tables
    for rt in $(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[?Associations[0].Main!=`true`].RouteTableId' --output text --region $REGION 2>/dev/null); do
      aws ec2 delete-route-table --route-table-id $rt --region $REGION 2>/dev/null || true
    done
    
    # Delete Security Groups
    for sg in $(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text --region $REGION 2>/dev/null); do
      aws ec2 delete-security-group --group-id $sg --region $REGION 2>/dev/null || true
    done
    
    # Delete VPC
    if aws ec2 delete-vpc --vpc-id $VPC_ID --region $REGION 2>/dev/null; then
      echo -e "  ${GREEN}Deleted VPC: $VPC_ID${NC}"
    else
      echo -e "  ${RED}Failed to delete VPC: $VPC_ID (may have remaining dependencies)${NC}"
    fi
  done
else
  echo "  No OncoLife VPCs found"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  CLEANUP COMPLETE!"
echo -e "==========================================${NC}"
echo ""
echo "You can now run a fresh deployment:"
echo -e "  ${CYAN}./scripts/aws/full-deploy.sh${NC}"
echo ""
