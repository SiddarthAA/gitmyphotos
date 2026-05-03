FROM python:3.12-slim

# Install system deps for Pillow (HEIC support via libheif is optional — add later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies into the system Python (no venv inside container)
RUN uv pip install --system --no-cache -r pyproject.toml 2>/dev/null || \
    uv pip install --system --no-cache \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.32.0" \
        "python-multipart>=0.0.12" \
        "httpx>=0.28.0" \
        "PyGithub>=2.5.0" \
        "Pillow>=11.0.0" \
        "exifread>=3.0.0" \
        "python-dotenv>=1.0.1" \
        "pydantic>=2.10.0" \
        "pydantic-settings>=2.6.0" \
        "aiofiles>=24.1.0" \
        "nanoid>=2.0.0"

# Copy application source
COPY app/ ./app/

# data/.env and cache/ are mounted at runtime via docker-compose volumes
# Create empty placeholders so the app can start even before first mount
RUN mkdir -p /app/cache/thumbs /app/cache/previews && \
    touch /app/.env

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
