# Google Cloud Run Optimized Dockerfile for PromoMind AI
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend code
COPY backend ./backend
COPY frontend ./frontend

EXPOSE 8080

# Launch server
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
