#!/bin/bash
# Deploy script for AWS SAM

ENVIRONMENT=${1:-dev}

echo "🚀 Deploying to $ENVIRONMENT environment..."

# Build
sam build

# Deploy
sam deploy \
  --stack-name order-processing-$ENVIRONMENT \
  --parameter-overrides Environment=$ENVIRONMENT \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset

echo "✅ Deployment complete!"
