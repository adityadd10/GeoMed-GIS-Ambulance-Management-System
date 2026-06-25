FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for PostGIS/psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5001

# Run via Waitress (production WSGI)
RUN pip install waitress
CMD ["waitress-serve", "--port=5001", "--call", "app:create_app"]
