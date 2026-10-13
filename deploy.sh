#!/bin/bash
# ==============================================================================
# PromoMind AI - Google Cloud Run Deployment Script
# AI Builder Cup 2026 Submission Deliverable
# ==============================================================================

set -e

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="promomind-ai"
REGION="asia-south1" # Bengaluru / Mumbai region, or choose us-central1

echo "========================================================"
echo "Deploying PromoMind AI to Google Cloud Run"
echo "Project ID : $PROJECT_ID"
echo "Service    : $SERVICE_NAME"
echo "Region     : $REGION"
echo "========================================================"

# Enable required Google Cloud services
echo "1. Enabling required GCP APIs..."
gcloud services enable run.googleapis.com \
                       artifactregistry.googleapis.com \
                       aiplatform.googleapis.com \
                       cloudbuild.googleapis.com

# Deploy directly from source to Cloud Run
echo "2. Building and deploying container to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --min-instances=0 \
  --max-instances=2 \
  --memory=512Mi \
  --cpu=1

echo "========================================================"
echo "Deployment Complete! Fetching public Cloud Run URL..."
URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Live Service URL: $URL"
echo "========================================================"
