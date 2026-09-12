# llama.cpp OpenAI-compatible server with baked-in Llama 3.2 1B GGUF.
# Build context: deploy/llama/ (model.gguf provided by Cloud Build from GCS).
FROM ghcr.io/ggerganov/llama.cpp:server

USER root
RUN mkdir -p /models
COPY model.gguf /models/model.gguf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
  && chmod 644 /models/model.gguf

ENV MODEL_PATH=/models/model.gguf \
    MODEL_ALIAS=llama-3.2-1b-instruct \
    HOST=0.0.0.0 \
    PORT=8080 \
    LLAMA_THREADS=4 \
    LLAMA_CTX_SIZE=2048

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
