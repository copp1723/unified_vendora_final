#!/bin/bash
# VENDORA – Secret Manager Bootstrap (Staging)
# ===========================================
# This script creates/updates Google Secret Manager entries required
# by the VENDORA platform in the *staging* project.  It is safe to
# re-run; existing secrets will have new versions added.
#
# Usage example:
#   PROJECT_ID=vendora-staging \
#   GEMINI_API_KEY=xxx \
#   OPENROUTER_API_KEY=yyy \
#   Mailgun_API=zzz \
#   Mailgun_Domain=mg.example.com \
#   Mailgun_Private_API_Key=key-123456 \
#   ./scripts/bootstrap-secrets.sh
#
# Required:  gcloud CLI already authenticated and configured.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-vendora-staging}"
SECRETS=(
  GEMINI_API_KEY
  OPENROUTER_API_KEY
  Mailgun_API
  Mailgun_Domain
  Mailgun_Private_API_Key
  SUPER_MEMORY_API
)

printf "\n🔐  Bootstrapping secrets into project: %s\n" "$PROJECT_ID"

gcloud config set project "$PROJECT_ID" >/dev/null

declare -i CREATED=0
for SECRET_NAME in "${SECRETS[@]}"; do
  VALUE="${!SECRET_NAME-}"  # Indirect expansion
  if [[ -z "$VALUE" ]]; then
    echo "⚠️  Skipping $SECRET_NAME – environment variable not provided"
    continue
  fi

  if gcloud secrets describe "$SECRET_NAME" --project "$PROJECT_ID" &>/dev/null; then
    echo "✅ Secret $SECRET_NAME exists – adding new version"
  else
    echo "➕ Creating secret $SECRET_NAME"
    gcloud secrets create "$SECRET_NAME" --project "$PROJECT_ID" --replication-policy="automatic" --quiet
  fi

  printf "%s" "$VALUE" | gcloud secrets versions add "$SECRET_NAME" --project "$PROJECT_ID" --data-file=- --quiet
  ((CREATED++))
  echo "   ↳ Stored new version for $SECRET_NAME"
done

if (( CREATED == 0 )); then
  echo "⚠️  No secrets were updated – please provide environment variables."
else
  echo "🎉  Secret bootstrap complete – $CREATED secret(s) updated."
fi