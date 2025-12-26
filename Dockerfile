# ---------- 1) Build frontend ----------
FROM node:20-slim AS frontend-build
WORKDIR /frontend

# Copy and install
COPY frontend/package*.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build


# ---------- 2) Backend runtime ----------
FROM python:3.10-slim

WORKDIR /app

# System deps (optional but safe for many python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install python deps
# NOTE: Place the requirements file at: backend/requirements.txt in your repo
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend
COPY backend/ /app/backend/

# Copy built frontend into expected location
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Hugging Face Spaces expects port 7860
ENV PORT=7860
EXPOSE 7860

# Start FastAPI
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
