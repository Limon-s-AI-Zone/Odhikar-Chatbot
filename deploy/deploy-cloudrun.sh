#!/usr/bin/env bash
# Build frontend+backend image with Cloud Build, push to Artifact Registry, deploy Cloud Run.
# Usage (from repo root or anywhere):
#   ./deploy/deploy-cloudrun.sh
#
# Optional env overrides:
#   GCP_PROJECT_ID  GCP_REGION  ARTIFACT_REPO  CLOUD_RUN_SERVICE  IMAGE_TAG
#   USE_LLAMA=1|0   LLAMA_CLOUD_RUN_SERVICE
# When USE_LLAMA is unset, auto-detects if odhikar-llama Cloud Run service exists.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="${ARTIFACT_REPO:-odhikar}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-odhikar}"
LLAMA_SERVICE="${LLAMA_CLOUD_RUN_SERVICE:-odhikar-llama}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
USE_LLAMA="${USE_LLAMA:-}"

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

DB_FILE="$ROOT/backend/odhikar.db"
if [[ ! -f "$DB_FILE" ]]; then
  echo "ERROR: backend/odhikar.db not found."
  echo "       Create/run the app locally once so the DB exists, then redeploy."
  exit 1
fi
DB_SIZE="$(wc -c < "$DB_FILE" | tr -d ' ')"
echo "==> Bundling local SQLite into image: backend/odhikar.db (${DB_SIZE} bytes)"
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

# Auto-detect Llama Cloud Run service unless USE_LLAMA is explicitly set.
if [[ -z "$USE_LLAMA" ]]; then
  if gcloud run services describe "$LLAMA_SERVICE" \
    --project="$PROJECT_ID" --region="$REGION" &>/dev/null; then
    USE_LLAMA=1
  else
    USE_LLAMA=0
  fi
fi

LLAMA_BASE_URL=""
if [[ "$USE_LLAMA" == "1" ]]; then
  LLAMA_URL="$(gcloud run services describe "$LLAMA_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)')"
  if [[ -z "$LLAMA_URL" ]]; then
    echo "ERROR: USE_LLAMA=1 but service '$LLAMA_SERVICE' has no URL."
    exit 1
  fi
  LLAMA_BASE_URL="${LLAMA_URL%/}/v1"
  LLM_PROVIDER="local"
  MODEL_NAME="${MODEL_NAME:-llama-3.2-1b-instruct}"
  # If .env still points at vertex/gemini defaults, force the GGUF alias.
  if [[ "$MODEL_NAME" == "gemini-2.5-flash-lite" || "$MODEL_NAME" == "gemini-2.5-flash" ]]; then
    MODEL_NAME="llama-3.2-1b-instruct"
  fi
  echo "==> Wiring Odhikar -> Llama service '$LLAMA_SERVICE'"
  echo "    LLM_PROVIDER=$LLM_PROVIDER"
  echo "    LLM_BASE_URL=$LLAMA_BASE_URL"
  echo "    MODEL_NAME=$MODEL_NAME"
else
  LLM_PROVIDER="${LLM_PROVIDER:-vertex}"
  MODEL_NAME="${MODEL_NAME:-gemini-2.5-flash-lite}"
  echo "==> Llama service not in use (USE_LLAMA=$USE_LLAMA); provider=$LLM_PROVIDER model=$MODEL_NAME"
fi

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
  "OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest"
do
  secret_name="${secret_pair%%=*}"
  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
    SECRET_ARGS+=("$secret_pair")
  fi
done

# When using Llama, Odhikar's LLM_API_KEY must match llama-server --api-key.
if [[ "$USE_LLAMA" == "1" ]]; then
  if gcloud secrets describe LLAMA_API_KEY --project="$PROJECT_ID" &>/dev/null; then
    SECRET_ARGS+=("LLM_API_KEY=LLAMA_API_KEY:latest")
  else
    echo "ERROR: LLAMA_API_KEY secret missing. Run ./deploy/setup-gcp.sh"
    exit 1
  fi
elif gcloud secrets describe LLM_API_KEY --project="$PROJECT_ID" &>/dev/null; then
  SECRET_ARGS+=("LLM_API_KEY=LLM_API_KEY:latest")
fi

SET_SECRETS=""
if ((${#SECRET_ARGS[@]} > 0)); then
  SET_SECRETS=$(IFS=,; echo "${SECRET_ARGS[*]}")
fi

ENV_VARS="LLM_PROVIDER=${LLM_PROVIDER},MODEL_NAME=${MODEL_NAME},GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_REGION},MAX_TOKENS=${MAX_TOKENS},TEMPERATURE=${TEMPERATURE},REASONING_MAX_TOKENS=${REASONING_MAX_TOKENS},TOKEN_BUDGET_LIMIT=${TOKEN_BUDGET_LIMIT},STATIC_DIR=/app/static"
if [[ -n "$LLAMA_BASE_URL" ]]; then
  ENV_VARS="${ENV_VARS},LLM_BASE_URL=${LLAMA_BASE_URL}"
fi

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
if [[ "$USE_LLAMA" == "1" ]]; then
  echo " LLM:      Llama via $LLAMA_BASE_URL"
fi
echo "============================================================"
echo "Note: Image includes your local backend/odhikar.db snapshot from this deploy."
echo "      New instances (redeploy / cold start) restore that snapshot;"
echo "      cases created only in the cloud are lost when the instance is replaced."
echo "Cold start after idle may take a while (Whisper model download / Llama load)."
