# Multi-stage build: compile the React app, then serve it from FastAPI.
# One image, one process, one URL — ideal for a single-service deploy.

# --- Stage 1: build the frontend -------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: python runtime -----------------------------------------------
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
# Built SPA lands where FRONTEND_DIST expects it (repo/frontend/dist).
COPY --from=frontend /app/frontend/dist ./frontend/dist

ENV COOKIE_SECURE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
