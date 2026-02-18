FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn (single worker for APScheduler)
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120"]
