#!/usr/bin/env bash
# One-time (or refresh) upload of the Llama GGUF to GCS for Cloud Build.
# Usage:
#   ./deploy/upload-llama-model.sh
#
# Optional env overrides:
#   GCP_PROJECT_ID  GCP_REGION  MODEL_BUCKET  GGUF_PATH
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
BUCKET="${MODEL_BUCKET:-${PROJECT_ID}-odhikar-models}"
GGUF_NAME="llama-3.2-1b-instruct.Q4_K_M.gguf"
GGUF_PATH="${GGUF_PATH:-$ROOT/deploy/$GGUF_NAME}"
GCS_URI="gs://${BUCKET}/${GGUF_NAME}"

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

if [[ ! -f "$GGUF_PATH" ]]; then
  echo "ERROR: GGUF not found at $GGUF_PATH"
  echo "       Place the model file there, or set GGUF_PATH=/path/to/model.gguf"
  exit 1
fi

echo "==> Project: $PROJECT_ID"
echo "==> Bucket:  gs://${BUCKET}"
echo "==> Source:  $GGUF_PATH"
echo

echo "==> Enabling Storage API..."
gcloud services enable storage.googleapis.com --project="$PROJECT_ID"

if ! gcloud storage buckets describe "gs://${BUCKET}" --project="$PROJECT_ID" &>/dev/null; then
  echo "==> Creating bucket gs://${BUCKET} (location=${REGION})..."
  gcloud storage buckets create "gs://${BUCKET}" \
    --project="$PROJECT_ID" \
    --location="$REGION" \
    --uniform-bucket-level-access
else
  echo "==> Bucket already exists."
fi

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "==> Granting Cloud Build SA objectViewer on bucket..."
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/storage.objectViewer" \
  --project="$PROJECT_ID" >/dev/null || true

echo "==> Uploading GGUF to ${GCS_URI} (may take a few minutes)..."
gcloud storage cp "$GGUF_PATH" "$GCS_URI" --project="$PROJECT_ID"

echo
echo "Upload complete: $GCS_URI"
echo "Next: ./deploy/setup-gcp.sh   # ensures LLAMA_API_KEY secret"
echo "Then: ./deploy/deploy-llama.sh"
