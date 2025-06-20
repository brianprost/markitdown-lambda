#!/bin/bash

set -e

GIT_HASH=$(git rev-parse --short HEAD)
if [ -z "$GIT_HASH" ]; then
  echo "Failed to get git hash"
  exit 1
fi
IMAGE_NAME="markitdown-lambda"
# IMAGE_TAG="$IMAGE_NAME-$GIT_HASH"
IMAGE_TAG=$(date +%s)

# get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Build and push the Docker image
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG ../
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG

# Apply the terraform
tofu init
tofu apply -var="image_tag=$IMAGE_TAG" -auto-approve
