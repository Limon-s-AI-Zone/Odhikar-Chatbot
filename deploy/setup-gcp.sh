#!/usr/bin/env bash
# One-time GCP setup for Odhikar Cloud Run (hackathon).
# Usage: ./deploy/setup-gcp.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="${ARTIFACT_REPO:-odhikar}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-odhikar}"

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

echo "==> Project: $PROJECT_ID"
echo "==> Region:  $REGION"
echo "==> Service: $SERVICE_NAME"
echo

echo "==> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  --project="$PROJECT_ID"

echo "==> Ensuring Artifact Registry Docker repo '$REPO_NAME'..."
if ! gcloud artifacts repositories describe "$REPO_NAME" \
  --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Odhikar hackathon images" \
    --project="$PROJECT_ID"
else
  echo "    Repo already exists."
fi

ensure_secret() {
  local name="$1"
  local value="$2"
  if [[ -z "$value" ]]; then
    echo "    Skip secret $name (empty in backend/.env)"
    return 0
  fi
  if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
    echo -n "$value" | gcloud secrets versions add "$name" \
      --data-file=- --project="$PROJECT_ID" >/dev/null
    echo "    Updated secret: $name"
  else
    echo -n "$value" | gcloud secrets create "$name" \
      --data-file=- --replication-policy=automatic --project="$PROJECT_ID" >/dev/null
    echo "    Created secret: $name"
  fi
}

ENV_FILE="$ROOT/backend/.env"
if [[ -f "$ENV_FILE" ]]; then
  echo "==> Syncing secrets from backend/.env (values not printed)..."
  # shellcheck disable=SC1090
  set -a
  # Only load KEY=VALUE lines; ignore comments/blank
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
    fi
  done < "$ENV_FILE"
  set +a

  ensure_secret "GOOGLE_API_KEY" "${GOOGLE_API_KEY:-}"
  ensure_secret "OPENROUTER_API_KEY" "${OPENROUTER_API_KEY:-}"
  ensure_secret "LLM_API_KEY" "${LLM_API_KEY:-}"
else
  echo "WARNING: backend/.env not found — create secrets manually before deploy."
fi

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "==> Granting runtime SA access to secrets + Vertex AI..."
echo "    SA: $RUNTIME_SA"
for secret in GOOGLE_API_KEY OPENROUTER_API_KEY LLM_API_KEY; do
  if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
    gcloud secrets add-iam-policy-binding "$secret" \
      --member="serviceAccount:${RUNTIME_SA}" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID" >/dev/null || true
  fi
done

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/aiplatform.user" \
  --condition=None >/dev/null || true

# Cloud Build needs to push images + deploy
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
echo "==> Granting Cloud Build SA Artifact Registry writer + Run admin (best effort)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/artifactregistry.writer" \
  --condition=None >/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/run.admin" \
  --condition=None >/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None >/dev/null || true

echo
echo "Setup complete."
echo "Next: ./deploy/deploy-cloudrun.sh"
