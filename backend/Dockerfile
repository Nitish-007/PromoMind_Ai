# ==============================================================================
# PromoMind AI Backend — Google Cloud Run Multi-Stage Dockerfile
# Context: ./backend
# ==============================================================================

# Stage 1: Build and install Python dependencies
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Create an isolated environment for dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Minimal production runtime
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PROMOMIND_DATA_DIR=/app/data \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy only the installed Python environment from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy backend application code and local data store
COPY . .

# Cloud Run injects PORT; 8080 is the default
EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]