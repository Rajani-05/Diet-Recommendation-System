# backend/Dockerfile  –  slim multi-stage build to stay under Render 512MB limit

# ── Stage 1: install Python packages ─────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# gcc needed to compile any C-extensions (e.g. numpy/scikit-learn wheels)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY FastAPI_Backend/requirements.txt requirements.txt
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.10-slim

# Copy only installed packages from builder stage (no build tools)
COPY --from=builder /install /usr/local

# Copy app source
RUN mkdir -p /app/backend
COPY FastAPI_Backend/ /app/backend/

# Copy only the 50k-row sampled dataset (12 MB vs 90 MB full file)
RUN mkdir -p /app/Data
COPY Data/dataset_small.csv.gz /app/Data/dataset_small.csv.gz

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]