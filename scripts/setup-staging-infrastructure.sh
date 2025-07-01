#!/bin/bash
# VENDORA - Staging Infrastructure Provisioning Script
# ====================================================
# This script provisions all GCP resources required for the staging
# environment.  It is **idempotent**; re-running it will skip resources
# that already exist.
#
# Requirements:
#   • gcloud CLI (>= 466.0.0) authenticated with an account that has
#     Editor / specific IAM roles in the target project.
#   • PROJECT_ID env var set to your staging project (e.g. vendora-staging).
#
# Usage:
#   chmod +x scripts/setup-staging-infrastructure.sh
#   PROJECT_ID=vendora-staging ./scripts/setup-staging-infrastructure.sh

set -euo pipefail

# ----------------------------
# 1. Configuration
# ----------------------------
PROJECT_ID="${PROJECT_ID:-vendora-staging}"
REGION="${REGION:-us-central1}"
SQL_INSTANCE="vendora-staging-db"
REDIS_INSTANCE="vendora-staging-cache"
BQ_DATASET="vendora_staging"
CLOUD_RUN_SVC="vendora-api-staging"
POSTGRES_DB="vendora_staging"

# Display config
cat <<EOF
🚀  VENDORA Staging Infrastructure Provisioning
    Project:      ${PROJECT_ID}
    Region:       ${REGION}
    Cloud SQL:    ${SQL_INSTANCE} (Postgres)
    Redis:        ${REDIS_INSTANCE}
    BigQuery:     ${BQ_DATASET}
    Cloud Run:    ${CLOUD_RUN_SVC}
EOF

# ----------------------------
# 2. Project & API setup
# ----------------------------

echo "🔧 Setting gcloud project..."
gcloud config set project "${PROJECT_ID}"

echo "🔌 Enabling required APIs (may take a few minutes) ..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com

# ----------------------------
# 3. Cloud SQL (Postgres)
# ----------------------------

echo "🗄️  Creating / updating Cloud SQL instance ..."
if gcloud sql instances describe "${SQL_INSTANCE}" &>/dev/null; then
  echo "✅ Cloud SQL instance already exists – skipping create"
else
  gcloud sql instances create "${SQL_INSTANCE}" \
    --database-version=POSTGRES_14 \
    --tier=db-custom-2-4096 \
    --region="${REGION}" \
    --storage-type=SSD \
    --storage-size=20GB \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --retained-backups-count=7
fi

# Create database in the instance if not present
if gcloud sql databases describe "${POSTGRES_DB}" --instance="${SQL_INSTANCE}" &>/dev/null; then
  echo "✅ Postgres database ${POSTGRES_DB} already exists"
else
  gcloud sql databases create "${POSTGRES_DB}" --instance="${SQL_INSTANCE}"
fi

# ----------------------------
# 4. Redis
# ----------------------------

echo "🗃️  Creating / updating Redis instance ..."
if gcloud redis instances describe "${REDIS_INSTANCE}" --region="${REGION}" &>/dev/null; then
  echo "✅ Redis instance already exists – skipping create"
else
  gcloud redis instances create "${REDIS_INSTANCE}" \
    --size=1 \
    --region="${REGION}" \
    --redis-version=redis_6_x \
    --tier=basic
fi

# ----------------------------
# 5. BigQuery dataset
# ----------------------------

echo "📊 Creating BigQuery dataset (if missing) ..."
if bq --project_id="${PROJECT_ID}" show "${BQ_DATASET}" &>/dev/null; then
  echo "✅ BigQuery dataset already exists"
else
  bq --location=US mk --dataset "${PROJECT_ID}:${BQ_DATASET}"
fi

# ----------------------------
# 6. Cloud Run service placeholder
# ----------------------------
# The actual container is deployed by CI/CD.  Here we create a placeholder with
# minimal settings so connection strings can be referenced immediately.

echo "☁️  Ensuring Cloud Run service placeholder exists ..."
if gcloud run services describe "${CLOUD_RUN_SVC}" --region="${REGION}" --platform managed &>/dev/null; then
  echo "✅ Cloud Run service already exists"
else
  gcloud run deploy "${CLOUD_RUN_SVC}" \
    --image us-docker.pkg.dev/cloudrun/container/hello \
    --platform managed \
    --region "${REGION}" \
    --allow-unauthenticated \
    --quiet
fi

echo "🎉  Staging infrastructure provisioning complete."