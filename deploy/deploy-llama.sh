#!/usr/bin/env bash
# Build llama.cpp server image (GGUF from GCS) and deploy Cloud Run service odhikar-llama.
# Prerequisites:
#   ./deploy/upload-llama-model.sh
#   ./deploy/setup-gcp.sh
#
# Usage:
#   ./deploy/deploy-llama.sh
#
# Optional env overrides:
#   GCP_PROJECT_ID  GCP_REGION  ARTIFACT_REPO  LLAMA_CLOUD_RUN_SERVICE
#   MODEL_BUCKET  IMAGE_TAG  LLAMA_MIN_INSTANCES
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="${ARTIFACT_REPO:-odhikar}"
SERVICE_NAME="${LLAMA_CLOUD_RUN_SERVICE:-odhikar-llama}"
BUCKET="${MODEL_BUCKET:-${PROJECT_ID}-odhikar-models}"
GGUF_NAME="llama-3.2-1b-instruct.Q4_K_M.gguf"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
MIN_INSTANCES="${LLAMA_MIN_INSTANCES:-0}"

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/odhikar-llama"
IMAGE_SHA="${IMAGE_BASE}:${IMAGE_TAG}"
IMAGE_LATEST="${IMAGE_BASE}:latest"

echo "==> Deploying Llama GGUF server to Cloud Run"
echo "    Project: $PROJECT_ID"
echo "    Region:  $REGION"
echo "    Service: $SERVICE_NAME"
echo "    Image:   $IMAGE_SHA"
echo "    Model:   gs://${BUCKET}/${GGUF_NAME}"
echo

if ! gcloud storage objects describe "gs://${BUCKET}/${GGUF_NAME}" --project="$PROJECT_ID" &>/dev/null; then
  echo "ERROR: Model not found at gs://${BUCKET}/${GGUF_NAME}"
  echo "       Run: ./deploy/upload-llama-model.sh"
  exit 1
fi

if ! gcloud artifacts repositories describe "$REPO_NAME" \
  --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
  echo "ERROR: Artifact Registry repo missing. Run ./deploy/setup-gcp.sh first."
  exit 1
fi

if ! gcloud secrets describe LLAMA_API_KEY --project="$PROJECT_ID" &>/dev/null; then
  echo "ERROR: Secret LLAMA_API_KEY missing. Run ./deploy/setup-gcp.sh first."
  exit 1
fi

echo "==> Building & pushing llama image via Cloud Build..."
gcloud builds submit \
  --project="$PROJECT_ID" \
  --config=deploy/llama/cloudbuild.yaml \
  --substitutions="_IMAGE_SHA=${IMAGE_SHA},_IMAGE_LATEST=${IMAGE_LATEST},_MODEL_BUCKET=${BUCKET},_GGUF_NAME=${GGUF_NAME}" \
  .

echo "==> Deploying Cloud Run service '$SERVICE_NAME'..."
gcloud run deploy "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --image="$IMAGE_SHA" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=8Gi \
  --cpu=4 \
  --no-cpu-throttling \
  --min-instances="$MIN_INSTANCES" \
  --max-instances=1 \
  --concurrency=1 \
  --timeout=300 \
  --set-env-vars="MODEL_ALIAS=llama-3.2-1b-instruct,LLAMA_THREADS=4,LLAMA_CTX_SIZE=2048" \
  --set-secrets="LLAMA_API_KEY=LLAMA_API_KEY:latest"

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)')"

echo
echo "============================================================"
echo " Llama service: $SERVICE_URL"
echo " OpenAI base:   $SERVICE_URL/v1"
echo "============================================================"
echo "Verify:"
echo "  SECRET=\$(gcloud secrets versions access latest --secret=LLAMA_API_KEY --project=$PROJECT_ID)"
echo "  curl -sS \"$SERVICE_URL/v1/models\" -H \"Authorization: Bearer \$SECRET\""
echo
echo "Then redeploy the app so it points at this endpoint:"
echo "  ./deploy/deploy-cloudrun.sh"
