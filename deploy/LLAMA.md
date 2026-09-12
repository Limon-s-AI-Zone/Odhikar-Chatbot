# Deploy Llama 3.2 1B GGUF on GCP (Cloud Run)

Serves [`llama-3.2-1b-instruct.Q4_K_M.gguf`](./llama-3.2-1b-instruct.Q4_K_M.gguf) with **llama.cpp** as a separate Cloud Run service (`odhikar-llama`). Odhikar keeps the same public URL and calls the model over the OpenAI-compatible `/v1` API.

## Architecture

```text
Browser → Cloud Run (odhikar) → Cloud Run (odhikar-llama) /v1
                                      ↑
                         GGUF baked into image (from GCS at build time)
```

## One-time setup

```bash
# 1) APIs, Artifact Registry, LLAMA_API_KEY secret, model bucket
./deploy/setup-gcp.sh

# 2) Upload ~770MB GGUF to gs://${PROJECT_ID}-odhikar-models/
./deploy/upload-llama-model.sh

# 3) Build + deploy llama-server on Cloud Run (CPU, 8Gi, 4 vCPU)
./deploy/deploy-llama.sh

# 4) Redeploy app (auto-detects odhikar-llama and sets LLM_* env)
./deploy/deploy-cloudrun.sh
```

Override auto-wiring:

```bash
USE_LLAMA=0 ./deploy/deploy-cloudrun.sh   # force Vertex / .env provider
USE_LLAMA=1 ./deploy/deploy-cloudrun.sh   # require llama service
```

## Verify llama service

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="${GCP_REGION:-us-central1}"
LLAMA_URL="$(gcloud run services describe odhikar-llama \
  --project="$PROJECT_ID" --region="$REGION" \
  --format='value(status.url)')"
SECRET="$(gcloud secrets versions access latest \
  --secret=LLAMA_API_KEY --project="$PROJECT_ID")"

# List models (cold start may take 30–90s the first time)
curl -sS "$LLAMA_URL/v1/models" \
  -H "Authorization: Bearer $SECRET" | head

# Short chat completion
curl -sS "$LLAMA_URL/v1/chat/completions" \
  -H "Authorization: Bearer $SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-1b-instruct",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}],
    "max_tokens": 64,
    "temperature": 0
  }'
```

## Verify Odhikar end-to-end

1. Open the app URL from `./deploy/deploy-cloudrun.sh` output (same as before if service name is still `odhikar`).
2. Hit `/docs` or the client intake UI and send a short Bangla/English message.
3. Confirm the response arrives (not a Vertex/OpenRouter error).
4. Optional: in Cloud Run logs for `odhikar`, look for requests toward the `odhikar-llama` host; in `odhikar-llama` logs, look for `/v1/chat/completions`.

```bash
ODHIKAR_URL="$(gcloud run services describe odhikar \
  --project="$PROJECT_ID" --region="$REGION" \
  --format='value(status.url)')"
curl -sS "$ODHIKAR_URL/docs" | head
```

## Env vars Odhikar gets when llama is wired

| Variable | Value |
|----------|--------|
| `LLM_PROVIDER` | `local` |
| `LLM_BASE_URL` | `https://odhikar-llama-….run.app/v1` |
| `MODEL_NAME` | `llama-3.2-1b-instruct` |
| `LLM_API_KEY` | from Secret Manager `LLAMA_API_KEY` |

## Ops notes

- **Cold start:** first request after idle loads the GGUF into RAM (tens of seconds). For demos: `LLAMA_MIN_INSTANCES=1 ./deploy/deploy-llama.sh`
- **Auth:** service allows unauthenticated HTTP but requires `Authorization: Bearer <LLAMA_API_KEY>`.
- **Cost:** two Cloud Run services; both can scale to zero (`min-instances=0`).
- **GPU:** not required for this 1B Q4 model; can be added later on the same service shape if latency is too high.
