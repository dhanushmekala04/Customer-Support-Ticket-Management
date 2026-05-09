#!/bin/bash
set -e

# ── Edit these ────────────────────────────────────
AWS_REGION="us-east-1"
ECR_REPO="ticket-mgmt"
SAM_STACK="ticket-mgmt-stack"
ENVIRONMENT="prod"
# ─────────────────────────────────────────────────

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo ""
echo "==========================================="
echo " Deploying to AWS Lambda"
echo " Account : $AWS_ACCOUNT_ID"
echo " Region  : $AWS_REGION"
echo " ECR     : $ECR_URI"
echo "==========================================="
echo ""

# ── STEP 1: Create ECR repo if it doesn't exist ──
echo ">>> Step 1: Ensure ECR repository exists"
aws ecr describe-repositories \
  --repository-names $ECR_REPO \
  --region $AWS_REGION > /dev/null 2>&1 || \
aws ecr create-repository \
  --repository-name $ECR_REPO \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true
echo "    ECR repo ready: $ECR_URI"

# ── STEP 2: Login to ECR ─────────────────────────
echo ""
echo ">>> Step 2: Docker login to ECR"
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# ── STEP 3: SAM build (builds Docker image) ──────
echo ""
echo ">>> Step 3: SAM build — building Docker image"
sam build \
  --use-container \
  --region $AWS_REGION

# ── STEP 4: SAM deploy (pushes to ECR + deploys Lambda) ──
echo ""
echo ">>> Step 4: SAM deploy — push to ECR + deploy Lambda"
sam deploy \
  --stack-name $SAM_STACK \
  --image-repository $ECR_URI \
  --region $AWS_REGION \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GroqApiKey="${GROQ_API_KEY}" \
    MongoUri="${MONGO_URI}" \
    Environment="${ENVIRONMENT}" \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

# ── DONE: Print outputs ──────────────────────────
echo ""
echo "==========================================="
echo " Deployment complete!"
echo "==========================================="
aws cloudformation describe-stacks \
  --stack-name $SAM_STACK \
  --region $AWS_REGION \
  --query "Stacks[0].Outputs" \
  --output table