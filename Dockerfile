FROM python:3.11-slim

WORKDIR /app

# Copy requirements from backend folder
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire backend folder
COPY backend/ .

# Expose port 7860 (Hugging Face standard)
EXPOSE 7860

# Run FastAPI from backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]