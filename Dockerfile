FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CREST_PROJECT_ROOT=/app \
    CREST_DATA_DIR=/app/data \
    CREST_DATABASE_PATH=/app/data/crest.db \
    CREST_FRONTEND_DIST=/app/frontend_dist \
    CREST_BOOTSTRAP_SAMPLE=false \
    CREST_OLLAMA_ENABLED=false \
    CREST_SEMANTIC_ENABLED=false
WORKDIR /app
COPY backend/requirements-runtime.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY README.md submission_metadata.yaml Dockerfile ./
COPY backend/requirements.txt ./backend/requirements.txt
COPY backend/requirements-runtime.txt ./backend/requirements-runtime.txt
COPY backend/app ./app
COPY backend/data/sandbox/ ./data/
COPY --from=frontend-build /build/frontend/dist ./frontend_dist
RUN useradd --create-home --uid 1000 crest && chown -R crest:crest /app
USER crest
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/health', timeout=3)" || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
