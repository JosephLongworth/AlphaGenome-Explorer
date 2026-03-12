# ─────────────────────────────────────────────────────────────────────────────
#  AlphaGenome Explorer – Dockerfile
#  Department of Immune and Inflammatory Diseases (DII)
#  Luxembourg Institute of Health (LIH)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libcurl4-openssl-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies (cached layer) ───────────────────────────────────────
COPY shiny_app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY shiny_app/ .

EXPOSE 8080

# ── Entrypoint ────────────────────────────────────────────────────────────────
CMD ["shiny", "run", "app.py", "--host", "0.0.0.0", "--port", "8080"]
