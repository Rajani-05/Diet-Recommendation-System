# backend/Dockerfile  –  slim build to stay under Render 512 MB limit

# ── Stage 1: install wheels ───────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# System deps needed to compile scikit-learn wheels (if no pre-built wheel exists)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY FastAPI_Backend/requirements.txt requirements.txt
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.10-slim

# Copy only installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy app source and data
RUN mkdir -p /app/backend /app/Data
COPY FastAPI_Backend/ /app/backend/
COPY Data/dataset.csv /app/Data/dataset.csv

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]