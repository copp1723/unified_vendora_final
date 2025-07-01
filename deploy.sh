#!/bin/bash

# VENDORA Deployment Script for Google Cloud Run
# This script builds and deploys the application to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID=${PROJECT_ID:-"vendora-464403"}
SERVICE_NAME=${SERVICE_NAME:-"vendora-api"}
REGION=${REGION:-"us-central1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting VENDORA deployment..."
echo "📋 Project: ${PROJECT_ID}"
echo "🏷️  Service: ${SERVICE_NAME}"
echo "🌍 Region: ${REGION}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install it first."
    exit 1
fi

# Set the project
echo "🔧 Setting gcloud project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the Docker image
echo "🏗️  Building Docker image..."
docker build -f working_vendora/docker/Dockerfile -t ${IMAGE_NAME} .

# Push the image to Google Container Registry
echo "📤 Pushing image to Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "PORT=8000,ENVIRONMENT=production" \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🔍 Health check: ${SERVICE_URL}/health"

# Test the health endpoint
echo "🏥 Testing health endpoint..."
if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed. Please check the logs:"
    echo "   gcloud logs read --service=${SERVICE_NAME} --region=${REGION}"
fi

echo "📊 View logs: gcloud logs read --service=${SERVICE_NAME} --region=${REGION}"
echo "🎯 Done!"