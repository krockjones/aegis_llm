FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 1000 --shell /bin/false aegis

COPY pyproject.toml README.md ./
COPY aegis_llm ./aegis_llm

RUN pip install --no-cache-dir . && chown -R aegis:aegis /app

ENV AEGISLLM_LISTEN_HOST=0.0.0.0
ENV AEGISLLM_LISTEN_PORT=8765
# Prefer AEGISLLM_UPSTREAM_BASE_URL; AEGISLLM_OLLAMA_BASE_URL remains a legacy alias.

EXPOSE 8765

USER aegis

# Uses stdlib urllib (no curl) so the image stays minimal.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('AEGISLLM_LISTEN_PORT', '8765') + '/healthz')"

CMD ["aegis-llm"]
