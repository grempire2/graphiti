FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install local graphiti-core first (monorepo structure)
COPY pyproject.toml README.md /tmp/graphiti/
COPY graphiti_core /tmp/graphiti/graphiti_core
RUN pip install --no-cache-dir -e /tmp/graphiti

# Copy project files
COPY graph4j/pyproject.toml ./
COPY graph4j/README.md ./
COPY graph4j/*.py ./
COPY graph4j/routers ./routers/

# Install Python dependencies (graphiti-core will be skipped since it's already installed)
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
