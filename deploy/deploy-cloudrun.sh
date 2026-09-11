#!/usr/bin/env bash
# Build frontend+backend image with Cloud Build, push to Artifact Registry, deploy Cloud Run.
# Usage (from repo root or anywhere):
#   ./deploy/deploy-cloudrun.sh
#
# Optional env overrides:
#   GCP_PROJECT_ID  GCP_REGION  ARTIFACT_REPO  CLOUD_RUN_SERVICE  IMAGE_TAG
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="${ARTIFACT_REPO:-odhikar}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-odhikar}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/odhikar"
IMAGE_SHA="${IMAGE_BASE}:${IMAGE_TAG}"
IMAGE_LATEST="${IMAGE_BASE}:latest"

echo "==> Deploying Odhikar to Cloud Run"
echo "    Project: $PROJECT_ID"
echo "    Region:  $REGION"
echo "    Service: $SERVICE_NAME"
echo "    Image:   $IMAGE_SHA"
echo

# Load non-secret defaults from backend/.env if present
LLM_PROVIDER="${LLM_PROVIDER:-}"
MODEL_NAME="${MODEL_NAME:-}"
GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT_ID}"
GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-$REGION}"
MAX_TOKENS="${MAX_TOKENS:-500}"
TEMPERATURE="${TEMPERATURE:-0}"
REASONING_MAX_TOKENS="${REASONING_MAX_TOKENS:-0}"
TOKEN_BUDGET_LIMIT="${TOKEN_BUDGET_LIMIT:-180}"

ENV_FILE="$ROOT/backend/.env"
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      case "$key" in
        LLM_PROVIDER|MODEL_NAME|GOOGLE_CLOUD_PROJECT|GOOGLE_CLOUD_REGION|MAX_TOKENS|TEMPERATURE|REASONING_MAX_TOKENS|TOKEN_BUDGET_LIMIT)
          printf -v "$key" '%s' "$val"
          ;;
      esac
    fi
  done < "$ENV_FILE"
fi

GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT_ID}"
GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-$REGION}"
LLM_PROVIDER="${LLM_PROVIDER:-vertex}"
MODEL_NAME="${MODEL_NAME:-gemini-2.5-flash-lite}"

# Ensure repo exists (idempotent)
if ! gcloud artifacts repositories describe "$REPO_NAME" \
  --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
  echo "==> Artifact Registry repo missing. Run ./deploy/setup-gcp.sh first."
  exit 1
fi

echo "==> Building & pushing image via Cloud Build (source: repo root)..."
gcloud builds submit \
  --project="$PROJECT_ID" \
  --config=deploy/cloudbuild.yaml \
  --substitutions="_IMAGE_SHA=${IMAGE_SHA},_IMAGE_LATEST=${IMAGE_LATEST}" \
  .

# Build --set-secrets only for secrets that exist
SECRET_ARGS=()
for secret_pair in \
  "GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
  "OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest" \
  "LLM_API_KEY=LLM_API_KEY:latest"
do
  secret_name="${secret_pair%%=*}"
  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
    SECRET_ARGS+=("$secret_pair")
  fi
done

SET_SECRETS=""
if ((${#SECRET_ARGS[@]} > 0)); then
  SET_SECRETS=$(IFS=,; echo "${SECRET_ARGS[*]}")
fi

ENV_VARS="LLM_PROVIDER=${LLM_PROVIDER},MODEL_NAME=${MODEL_NAME},GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_REGION},MAX_TOKENS=${MAX_TOKENS},TEMPERATURE=${TEMPERATURE},REASONING_MAX_TOKENS=${REASONING_MAX_TOKENS},TOKEN_BUDGET_LIMIT=${TOKEN_BUDGET_LIMIT},STATIC_DIR=/app/static"

echo "==> Deploying Cloud Run service '$SERVICE_NAME'..."
DEPLOY_CMD=(
  gcloud run deploy "$SERVICE_NAME"
  --project="$PROJECT_ID"
  --image="$IMAGE_SHA"
  --region="$REGION"
  --platform=managed
  --allow-unauthenticated
  --port=8080
  --memory=4Gi
  --cpu=2
  --min-instances=0
  --max-instances=1
  --concurrency=1
  --timeout=360
  --cpu-boost
  --set-env-vars="$ENV_VARS"
)

if [[ -n "$SET_SECRETS" ]]; then
  DEPLOY_CMD+=(--set-secrets="$SET_SECRETS")
else
  echo "WARNING: No Secret Manager secrets found. LLM calls may fail."
  echo "         Run ./deploy/setup-gcp.sh after filling backend/.env"
fi

"${DEPLOY_CMD[@]}"

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)')"

echo
echo "============================================================"
echo " Deployed: $SERVICE_URL"
echo " API docs: $SERVICE_URL/docs"
echo "============================================================"
echo "Note: SQLite is ephemeral on Cloud Run (resets on new revision)."
echo "Cold start after idle may take a while (Whisper model download)."
