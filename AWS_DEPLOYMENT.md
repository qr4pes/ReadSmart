# AWS Deployment Guide

Complete guide for deploying the Website Content Analyzer on AWS using ECS Fargate and RDS.

## Architecture

```
Internet → ALB → ECS Fargate (Backend + Frontend) → RDS PostgreSQL
                      ↓
                  OpenAI API
```

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Docker installed locally
- OpenAI API key
- Domain name (optional, for custom domain)

## Step-by-Step Deployment

### 1. Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=website-analyzer-vpc}]'

# Note the VPC ID
export VPC_ID=<vpc-id>

# Create public subnets (for ALB)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1a}]'

aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1b}]'

# Create private subnets (for ECS and RDS)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-1a}]'

aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-1b}]'

# Create and attach Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=website-analyzer-igw}]'

export IGW_ID=<igw-id>

aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID

# Create NAT Gateway (for private subnet internet access)
aws ec2 allocate-address --domain vpc

export EIP_ALLOC_ID=<allocation-id>

aws ec2 create-nat-gateway \
  --subnet-id <public-subnet-1a-id> \
  --allocation-id $EIP_ALLOC_ID \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=website-analyzer-nat}]'

export NAT_GW_ID=<nat-gateway-id>

# Update route tables
# Public subnet route table
aws ec2 create-route-table --vpc-id $VPC_ID

export PUBLIC_RT_ID=<route-table-id>

aws ec2 create-route \
  --route-table-id $PUBLIC_RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

# Associate public subnets
aws ec2 associate-route-table \
  --route-table-id $PUBLIC_RT_ID \
  --subnet-id <public-subnet-1a-id>

aws ec2 associate-route-table \
  --route-table-id $PUBLIC_RT_ID \
  --subnet-id <public-subnet-1b-id>

# Private subnet route table
aws ec2 create-route-table --vpc-id $VPC_ID

export PRIVATE_RT_ID=<route-table-id>

aws ec2 create-route \
  --route-table-id $PRIVATE_RT_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_ID

# Associate private subnets
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_RT_ID \
  --subnet-id <private-subnet-1a-id>

aws ec2 associate-route-table \
  --route-table-id $PRIVATE_RT_ID \
  --subnet-id <private-subnet-1b-id>
```

### 2. Create Security Groups

```bash
# ALB Security Group (allow HTTP/HTTPS from internet)
aws ec2 create-security-group \
  --group-name alb-sg \
  --description "Security group for ALB" \
  --vpc-id $VPC_ID

export ALB_SG_ID=<security-group-id>

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# ECS Security Group (allow traffic from ALB)
aws ec2 create-security-group \
  --group-name ecs-sg \
  --description "Security group for ECS tasks" \
  --vpc-id $VPC_ID

export ECS_SG_ID=<security-group-id>

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8000 \
  --source-group $ALB_SG_ID

# RDS Security Group (allow traffic from ECS)
aws ec2 create-security-group \
  --group-name rds-sg \
  --description "Security group for RDS" \
  --vpc-id $VPC_ID

export RDS_SG_ID=<security-group-id>

aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $ECS_SG_ID
```

### 3. Create RDS PostgreSQL Database

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name website-analyzer-db-subnet \
  --db-subnet-group-description "Subnet group for website analyzer DB" \
  --subnet-ids <private-subnet-1a-id> <private-subnet-1b-id>

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier website-analyzer-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username analyzer_admin \
  --master-user-password <strong-password-here> \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids $RDS_SG_ID \
  --db-subnet-group-name website-analyzer-db-subnet \
  --backup-retention-period 7 \
  --multi-az \
  --no-publicly-accessible \
  --db-name website_analyzer

# Wait for DB to be available (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier website-analyzer-db

# Get DB endpoint
aws rds describe-db-instances \
  --db-instance-identifier website-analyzer-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text

export DB_ENDPOINT=<db-endpoint>
```

### 4. Create ECR Repository and Push Docker Image

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name website-analyzer \
  --image-scanning-configuration scanOnPush=true

export ECR_REPO_URI=<account-id>.dkr.ecr.<region>.amazonaws.com/website-analyzer

# Login to ECR
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin $ECR_REPO_URI

# Build and push image
cd backend
docker build -t website-analyzer .
docker tag website-analyzer:latest $ECR_REPO_URI:latest
docker push $ECR_REPO_URI:latest
```

### 5. Create Secrets Manager Secret for OpenAI API Key

```bash
aws secretsmanager create-secret \
  --name website-analyzer/openai-api-key \
  --description "OpenAI API key for website analyzer" \
  --secret-string '{"OPENAI_API_KEY":"sk-your-actual-key-here"}'

export SECRET_ARN=<secret-arn>
```

### 6. Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name website-analyzer-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
```

### 7. Create IAM Roles

```bash
# Create task execution role
cat > task-execution-role-trust-policy.json << EOF
{
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
}
EOF

aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://task-execution-role-trust-policy.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Add policy for Secrets Manager access
cat > secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "$SECRET_ARN"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets-policy.json

export EXECUTION_ROLE_ARN=<role-arn>

# Create task role (if needed for application)
aws iam create-role \
  --role-name ecsTaskRole \
  --assume-role-policy-document file://task-execution-role-trust-policy.json

export TASK_ROLE_ARN=<role-arn>
```

### 8. Create ECS Task Definition

```bash
cat > task-definition.json << EOF
{
  "family": "website-analyzer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "$EXECUTION_ROLE_ARN",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "website-analyzer",
      "image": "$ECR_REPO_URI:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://analyzer_admin:<password>@$DB_ENDPOINT:5432/website_analyzer"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "$SECRET_ARN:OPENAI_API_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/website-analyzer",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/website-analyzer

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### 9. Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name website-analyzer-alb \
  --subnets <public-subnet-1a-id> <public-subnet-1b-id> \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application

export ALB_ARN=<load-balancer-arn>

# Create target group
aws elbv2 create-target-group \
  --name website-analyzer-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /api/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

export TG_ARN=<target-group-arn>

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### 10. Create ECS Service

```bash
aws ecs create-service \
  --cluster website-analyzer-cluster \
  --service-name website-analyzer-service \
  --task-definition website-analyzer \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<private-subnet-1a-id>,<private-subnet-1b-id>],securityGroups=[$ECS_SG_ID],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=website-analyzer,containerPort=8000" \
  --health-check-grace-period-seconds 60

# Enable auto-scaling (optional)
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/website-analyzer-cluster/website-analyzer-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/website-analyzer-cluster/website-analyzer-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json

cat > scaling-policy.json << EOF
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
EOF
```

### 11. Get ALB DNS Name

```bash
aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text

# Your application will be available at:
# http://<alb-dns-name>
```

### 12. (Optional) Set Up Custom Domain with Route 53

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference $(date +%s)

# Get ALB hosted zone ID
aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].CanonicalHostedZoneId' \
  --output text

export ALB_HOSTED_ZONE_ID=<hosted-zone-id>

# Create Route 53 record
cat > route53-record.json << EOF
{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "analyzer.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "$ALB_HOSTED_ZONE_ID",
          "DNSName": "<alb-dns-name>",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
EOF

aws route53 change-resource-record-sets \
  --hosted-zone-id <your-hosted-zone-id> \
  --change-batch file://route53-record.json
```

### 13. (Optional) Add HTTPS with ACM

```bash
# Request certificate
aws acm request-certificate \
  --domain-name analyzer.example.com \
  --validation-method DNS

export CERT_ARN=<certificate-arn>

# Validate certificate through DNS (follow ACM console instructions)

# Add HTTPS listener to ALB
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN

# Redirect HTTP to HTTPS
aws elbv2 modify-listener \
  --listener-arn <http-listener-arn> \
  --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"
```

## Cost Estimation (Monthly, us-east-1)

- **ECS Fargate**: 2 tasks × 0.5 vCPU × $0.04 + 2 tasks × 1 GB × $0.004 × 730 hours = ~$60
- **RDS db.t3.micro**: $0.017/hour × 730 hours = ~$12.50
- **RDS Storage**: 20 GB × $0.115/GB = ~$2.30
- **ALB**: $0.0225/hour × 730 hours + data processing = ~$20
- **Data Transfer**: Variable based on usage
- **NAT Gateway**: $0.045/hour × 730 hours + data = ~$35
- **OpenAI API**: Variable based on usage (biggest cost)

**Estimated Total: ~$130/month** (excluding OpenAI API usage)

### Cost Optimization Tips

1. Use FARGATE_SPOT for non-critical workloads (70% savings)
2. Use Single-AZ RDS for development
3. Consider VPC endpoints instead of NAT Gateway for AWS services
4. Enable CloudWatch Logs retention limits
5. Use reserved capacity for predictable workloads

## Monitoring and Logging

### CloudWatch Dashboards

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name website-analyzer \
  --dashboard-body file://dashboard.json
```

### CloudWatch Alarms

```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name high-cpu-utilization \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# Database connections alarm
aws cloudwatch put-metric-alarm \
  --alarm-name high-db-connections \
  --alarm-description "Alert when DB connections exceed 80" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## Updating the Application

```bash
# Build new image
docker build -t website-analyzer ./backend
docker tag website-analyzer:latest $ECR_REPO_URI:v2
docker push $ECR_REPO_URI:v2

# Update task definition (change image tag to :v2)
# Register new task definition
aws ecs register-task-definition --cli-input-json file://task-definition-v2.json

# Update service
aws ecs update-service \
  --cluster website-analyzer-cluster \
  --service website-analyzer-service \
  --task-definition website-analyzer:2 \
  --force-new-deployment
```

## Cleanup

```bash
# Delete ECS service
aws ecs update-service \
  --cluster website-analyzer-cluster \
  --service website-analyzer-service \
  --desired-count 0

aws ecs delete-service \
  --cluster website-analyzer-cluster \
  --service website-analyzer-service

# Delete ECS cluster
aws ecs delete-cluster --cluster website-analyzer-cluster

# Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
aws elbv2 delete-target-group --target-group-arn $TG_ARN

# Delete RDS instance
aws rds delete-db-instance \
  --db-instance-identifier website-analyzer-db \
  --skip-final-snapshot

# Delete remaining resources (security groups, VPC, etc.)
```

## Troubleshooting

### Service Not Starting
```bash
# Check service events
aws ecs describe-services \
  --cluster website-analyzer-cluster \
  --services website-analyzer-service

# Check task logs
aws logs tail /ecs/website-analyzer --follow
```

### Database Connection Issues
- Verify security group rules allow ECS → RDS on port 5432
- Check DATABASE_URL is correct
- Verify RDS is in the same VPC

### High Costs
- Check OpenAI API usage (usually the highest cost)
- Review CloudWatch metrics for traffic patterns
- Consider FARGATE_SPOT for cost savings

## Security Best Practices

1. Use Secrets Manager for sensitive data
2. Enable encryption at rest for RDS
3. Use HTTPS only in production
4. Implement WAF rules on ALB
5. Enable VPC Flow Logs
6. Regular security group audits
7. Enable GuardDuty for threat detection
8. Use IAM roles with least privilege

## Backup and Disaster Recovery

1. Enable automated RDS backups (7-35 days retention)
2. Take manual RDS snapshots before major changes
3. Use Multi-AZ for production RDS
4. Store ECR images with multiple tags
5. Document infrastructure as code (Terraform/CloudFormation)

## Production Checklist

- [ ] Enable Multi-AZ RDS
- [ ] Configure HTTPS with ACM certificate
- [ ] Set up CloudWatch alarms
- [ ] Enable auto-scaling
- [ ] Configure backup retention
- [ ] Set up monitoring dashboard
- [ ] Implement rate limiting
- [ ] Add WAF rules
- [ ] Enable access logging on ALB
- [ ] Set up CI/CD pipeline
- [ ] Document runbooks
- [ ] Test disaster recovery procedures
