FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run will set PORT environment variable
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}