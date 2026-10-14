FROM node:18-alpine AS front-builder
WORKDIR /front
COPY app-vulnerable/frontend/package.json app-vulnerable/frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=cache,target=/front/node_modules \
    npm install --no-audit --no-fund
COPY app-vulnerable/frontend/ ./
RUN --mount=type=cache,target=/front/node_modules \
    --mount=type=cache,target=/front/.angular/cache \
    npm run build


FROM python:3.9-slim-bookworm AS builder

WORKDIR /src

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends build-essential python3-dev

COPY app-vulnerable/backend/requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.txt


FROM python:3.9-slim-bookworm

RUN useradd --create-home --home-dir /app --shell /usr/sbin/nologin opc

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY app-vulnerable/backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels


COPY --chown=opc:opc app-vulnerable/backend /app

COPY --chown=opc:opc infraestructura/docker/backend/serve_with_spa.py /app/serve_with_spa.py

COPY --from=front-builder /front/dist/opc-tickets-frontend/ /app/spa/

RUN mkdir -p /app/data && chown opc:opc /app/data

USER opc

EXPOSE 5000

CMD ["python", "serve_with_spa.py"]
