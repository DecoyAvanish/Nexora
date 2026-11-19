FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend backend
COPY artifacts artifacts
COPY data/sp500_universe.csv data/sp500_universe.csv
EXPOSE 5001
ENV NEXORA_ENV=staging NEXORA_HOST=0.0.0.0
CMD ["python", "-m", "backend.app"]
