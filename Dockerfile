FROM node:24-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
COPY static/ /build/static/
RUN npm run check && npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt \
    && groupadd --gid 10001 mazahua \
    && useradd --uid 10001 --gid 10001 --no-create-home mazahua \
    && mkdir -p /data/uploads/audios /data/uploads/imagenes \
    && chown -R mazahua:mazahua /data
COPY *.py catalogo_manifest.json videos_youtube.json ./
COPY deploy/iniciar_render.py ./deploy/iniciar_render.py
COPY static/ ./static/
COPY catalogo/ ./catalogo/
COPY --from=frontend /build/frontend/dist/ ./frontend/dist/
USER 10001:10001
ENV UPLOADS_DIR=/data/uploads
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*", "--limit-concurrency", "256", "--timeout-keep-alive", "10", "--ws-max-size", "4096", "--no-access-log"]
