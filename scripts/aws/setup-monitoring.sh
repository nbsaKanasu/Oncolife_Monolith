#!/bin/bash
# =============================================================================
# OncoLife Monitoring Setup Script
# =============================================================================
# 
# This script sets up:
# 1. SNS Topics for alert notifications
# 2. Email subscriptions for alerts
# 3. CloudWatch Log Groups
# 4. CloudWatch Dashboard
#
# Usage:
#   ./setup-monitoring.sh production email@example.com
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Appropriate IAM permissions
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
ALERT_EMAIL="${2:-}"
AWS_REGION="${AWS_REGION:-eu-west-2}"
PROJECT_NAME="oncolife"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     OncoLife Monitoring Setup - ${ENVIRONMENT}                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"

# =============================================================================
# SNS Topics Setup
# =============================================================================

echo -e "\n${YELLOW}📧 Setting up SNS Topics...${NC}"

# Create main alerts topic
ALERTS_TOPIC_ARN=$(aws sns create-topic \
    --name "${PROJECT_NAME}-${ENVIRONMENT}-alerts" \
    --region "$AWS_REGION" \
    --tags "Key=Environment,Value=${ENVIRONMENT}" "Key=Project,Value=${PROJECT_NAME}" \
    --query 'TopicArn' \
    --output text 2>/dev/null || echo "")

if [ -n "$ALERTS_TOPIC_ARN" ]; then
    echo -e "${GREEN}✓ Created SNS topic: ${ALERTS_TOPIC_ARN}${NC}"
else
    ALERTS_TOPIC_ARN=$(aws sns list-topics --region "$AWS_REGION" --query "Topics[?contains(TopicArn, '${PROJECT_NAME}-${ENVIRONMENT}-alerts')].TopicArn" --output text)
    echo -e "${YELLOW}! SNS topic already exists: ${ALERTS_TOPIC_ARN}${NC}"
fi

# Create critical alerts topic (for immediate attention)
CRITICAL_TOPIC_ARN=$(aws sns create-topic \
    --name "${PROJECT_NAME}-${ENVIRONMENT}-critical-alerts" \
    --region "$AWS_REGION" \
    --tags "Key=Environment,Value=${ENVIRONMENT}" "Key=Project,Value=${PROJECT_NAME}" "Key=Severity,Value=critical" \
    --query 'TopicArn' \
    --output text 2>/dev/null || echo "")

if [ -n "$CRITICAL_TOPIC_ARN" ]; then
    echo -e "${GREEN}✓ Created critical alerts topic: ${CRITICAL_TOPIC_ARN}${NC}"
fi

# Subscribe email if provided
if [ -n "$ALERT_EMAIL" ]; then
    echo -e "\n${YELLOW}📬 Subscribing email to alerts...${NC}"
    
    aws sns subscribe \
        --topic-arn "$ALERTS_TOPIC_ARN" \
        --protocol email \
        --notification-endpoint "$ALERT_EMAIL" \
        --region "$AWS_REGION" \
        --return-subscription-arn 2>/dev/null || true
    
    echo -e "${GREEN}✓ Subscription request sent to ${ALERT_EMAIL}${NC}"
    echo -e "${YELLOW}! Please check your email and confirm the subscription${NC}"
    
    # Also subscribe to critical alerts
    aws sns subscribe \
        --topic-arn "$CRITICAL_TOPIC_ARN" \
        --protocol email \
        --notification-endpoint "$ALERT_EMAIL" \
        --region "$AWS_REGION" \
        --return-subscription-arn 2>/dev/null || true
fi

# =============================================================================
# CloudWatch Log Groups
# =============================================================================

echo -e "\n${YELLOW}📋 Setting up CloudWatch Log Groups...${NC}"

LOG_GROUPS=(
    "/ecs/${PROJECT_NAME}-${ENVIRONMENT}/patient-api"
    "/ecs/${PROJECT_NAME}-${ENVIRONMENT}/doctor-api"
    "/ecs/${PROJECT_NAME}-${ENVIRONMENT}/patient-web"
    "/ecs/${PROJECT_NAME}-${ENVIRONMENT}/doctor-web"
    "/ecs/${PROJECT_NAME}-${ENVIRONMENT}/patient-server"
)

for LOG_GROUP in "${LOG_GROUPS[@]}"; do
    aws logs create-log-group \
        --log-group-name "$LOG_GROUP" \
        --region "$AWS_REGION" 2>/dev/null || true
    
    # Set retention to 30 days
    aws logs put-retention-policy \
        --log-group-name "$LOG_GROUP" \
        --retention-in-days 30 \
        --region "$AWS_REGION" 2>/dev/null || true
    
    echo -e "${GREEN}✓ Log group: ${LOG_GROUP}${NC}"
done

# =============================================================================
# CloudWatch Dashboard
# =============================================================================

echo -e "\n${YELLOW}📊 Creating CloudWatch Dashboard...${NC}"

DASHBOARD_NAME="${PROJECT_NAME}-${ENVIRONMENT}-dashboard"

DASHBOARD_BODY=$(cat <<EOF
{
    "widgets": [
        {
            "type": "text",
            "x": 0,
            "y": 0,
            "width": 24,
            "height": 1,
            "properties": {
                "markdown": "# OncoLife Production Dashboard\n**Environment:** ${ENVIRONMENT} | **Last Updated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 1,
            "width": 12,
            "height": 6,
            "properties": {
                "title": "API Response Times (P95)",
                "metrics": [
                    [ "AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/oncolife-alb/${ENVIRONMENT}", { "stat": "p95", "label": "All APIs" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}",
                "stat": "p95"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 1,
            "width": 12,
            "height": 6,
            "properties": {
                "title": "Request Count",
                "metrics": [
                    [ "AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/oncolife-alb/${ENVIRONMENT}", { "stat": "Sum" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}",
                "stat": "Sum"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 7,
            "width": 8,
            "height": 6,
            "properties": {
                "title": "ECS CPU Utilization",
                "metrics": [
                    [ "AWS/ECS", "CPUUtilization", "ClusterName", "oncolife-cluster", "ServiceName", "patient-api", { "label": "Patient API" } ],
                    [ "...", "doctor-api", { "label": "Doctor API" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}"
            }
        },
        {
            "type": "metric",
            "x": 8,
            "y": 7,
            "width": 8,
            "height": 6,
            "properties": {
                "title": "ECS Memory Utilization",
                "metrics": [
                    [ "AWS/ECS", "MemoryUtilization", "ClusterName", "oncolife-cluster", "ServiceName", "patient-api", { "label": "Patient API" } ],
                    [ "...", "doctor-api", { "label": "Doctor API" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}"
            }
        },
        {
            "type": "metric",
            "x": 16,
            "y": 7,
            "width": 8,
            "height": 6,
            "properties": {
                "title": "HTTP 5xx Errors",
                "metrics": [
                    [ "AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", "app/oncolife-alb/${ENVIRONMENT}", { "stat": "Sum", "color": "#d62728" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}",
                "stat": "Sum"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 13,
            "width": 12,
            "height": 6,
            "properties": {
                "title": "RDS Metrics",
                "metrics": [
                    [ "AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "oncolife-db", { "label": "CPU %" } ],
                    [ ".", "DatabaseConnections", ".", ".", { "label": "Connections", "yAxis": "right" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 13,
            "width": 12,
            "height": 6,
            "properties": {
                "title": "Application Alerts",
                "metrics": [
                    [ "OncoLife/PatientAPI", "Alert_Error", "Environment", "${ENVIRONMENT}", { "label": "Errors", "color": "#d62728" } ],
                    [ ".", "Alert_Warning", ".", ".", { "label": "Warnings", "color": "#ff7f0e" } ],
                    [ ".", "AuthenticationFailure", ".", ".", { "label": "Auth Failures", "color": "#9467bd" } ]
                ],
                "period": 60,
                "region": "${AWS_REGION}",
                "stat": "Sum"
            }
        },
        {
            "type": "alarm",
            "x": 0,
            "y": 19,
            "width": 24,
            "height": 3,
            "properties": {
                "title": "Active Alarms",
                "alarms": [
                    "arn:aws:cloudwatch:${AWS_REGION}:*:alarm:OncoLife-${ENVIRONMENT}-*"
                ]
            }
        }
    ]
}
EOF
)

aws cloudwatch put-dashboard \
    --dashboard-name "$DASHBOARD_NAME" \
    --dashboard-body "$DASHBOARD_BODY" \
    --region "$AWS_REGION" 2>/dev/null || true

echo -e "${GREEN}✓ Dashboard created: ${DASHBOARD_NAME}${NC}"

# =============================================================================
# Summary
# =============================================================================

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 Monitoring Setup Complete!                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Created Resources:${NC}"
echo -e "  • SNS Alerts Topic: ${ALERTS_TOPIC_ARN}"
echo -e "  • SNS Critical Topic: ${CRITICAL_TOPIC_ARN}"
echo -e "  • Log Groups: ${#LOG_GROUPS[@]} created"
echo -e "  • Dashboard: ${DASHBOARD_NAME}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Confirm email subscription (check inbox)"
echo -e "  2. Apply CloudWatch alarms: cd scripts/aws && terraform apply"
echo -e "  3. Configure Slack webhook (optional)"
echo -e "  4. View dashboard: https://${AWS_REGION}.console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${DASHBOARD_NAME}"

echo -e "\n${BLUE}Environment Variables to Set:${NC}"
echo -e "  export SNS_ALERT_TOPIC_ARN=\"${ALERTS_TOPIC_ARN}\""
echo -e "  export CLOUDWATCH_NAMESPACE=\"OncoLife/PatientAPI\""
