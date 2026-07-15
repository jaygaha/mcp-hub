FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application
COPY . .

# Set default fallback values
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Shell form so ${API_HOST}/${API_PORT} are actually expanded - the exec
# ("[...]") form does not invoke a shell and passes them through literally.
CMD uvicorn src.main:app --host ${API_HOST} --port ${API_PORT}
