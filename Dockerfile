# ---- build frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ---- backend runtime ----
FROM python:3.10-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install backend deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source
COPY backend/ /app/backend/

# Copy built frontend into /app/frontend/dist
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Download PDFs into the container (so Space has them even if they are not pushed to HF)
RUN python - <<'PY'
import os, urllib.request

base = "https://raw.githubusercontent.com/Pradeep0208/ISO20022--AI-CHATBOT-ASSISTAND/main/backend/data/"
files = ["camt_messages.pdf", "pacs_messages.pdf", "pain_messages.pdf"]

os.makedirs("/app/backend/data", exist_ok=True)

for f in files:
    dst = f"/app/backend/data/{f}"
    if not os.path.exists(dst):
        print("Downloading", f)
        urllib.request.urlretrieve(base + f, dst)

print("PDFs ready.")
PY

# Hugging Face Spaces expects port 7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--app-dir", "backend"]
