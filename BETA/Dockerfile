# Multi-Stage Dockerfile for Capstone Production Deployment

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine as frontend-builder
WORKDIR /app/frontend
# Copy package.json and install dependencies
COPY frontend/package*.json ./
RUN npm install
# Copy rest of frontend source and build
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Backend & Final Assembly ---
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies (e.g. for OR-Tools / C++)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python backend source
COPY api/ ./api/
COPY ai_engine/ ./ai_engine/
COPY database/ ./database/
COPY optimizer/ ./optimizer/
COPY realtime/ ./realtime/
COPY BETA/ ./BETA/
COPY main.py ./

# Copy compiled frontend from Stage 1 into the backend's static directory
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
