FROM node:18-alpine AS front-builder
WORKDIR /front
COPY app-vulnerable/frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY app-vulnerable/frontend/ ./
RUN npm run build


FROM python:3.9-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1
WORKDIR /src

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app-vulnerable/backend/requirements.txt ./
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.txt


FROM python:3.9-slim-bookworm

RUN useradd --create-home --home-dir /app --shell /usr/sbin/nologin opc

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY app-vulnerable/backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels


COPY --chown=opc:opc app-vulnerable/backend /app

# Wrapper que sirve el SPA ademas de la API (vive en infraestructura/).
COPY --chown=opc:opc infraestructura/docker/backend/serve_with_spa.py /app/serve_with_spa.py

# SPA compilado en la etapa 1. La app lo sirve desde /app/spa (SPA_DIR).
COPY --from=front-builder /front/dist/opc-tickets-frontend/ /app/spa/

# /app/data: raiz de datos persistentes (config.py -> APP_DATA_DIR=/app/data).
# Se crea con el dueno correcto: cuando Docker initializa un named volume en
# una ruta existente, copia el contenido del directorio y conserva su
# propiedades, de modo que la app (usuario no-root) puede escribir en el
# volumen sin problemas de permisos.
RUN mkdir -p /app/data && chown opc:opc /app/data

USER opc

EXPOSE 5000

# serve_with_spa.py inicializa la base, sirve la API y el SPA en 0.0.0.0:5000.
CMD ["python", "serve_with_spa.py"]