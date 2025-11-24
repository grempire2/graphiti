# syntax=docker/dockerfile:1.9
FROM python:3.12-slim

# Install uv using the installer script
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:$PATH"

# Configure uv for runtime
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Create non-root user
RUN groupadd -r app && useradd -r -d /app -g app app

# Set up the application
WORKDIR /app

# Copy graphiti-core local package into a subdirectory
# (pyproject.toml must be in parent of graphiti_core for hatchling)
COPY ./pyproject.toml ./graphiti-core-src/pyproject.toml
COPY ./README.md ./graphiti-core-src/README.md
COPY ./graphiti_core ./graphiti-core-src/graphiti_core

# Copy neo4j_server files
COPY ./neo4j_server/pyproject.toml ./
COPY ./neo4j_server/uv.lock ./
COPY ./neo4j_server/app ./app

# Install dependencies
# First install neo4j_server dependencies (excluding graphiti-core from lock file)
# Then install local graphiti-core in editable mode with extras
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev && \
    uv pip uninstall --system graphiti-core || true && \
    uv pip install --system -e ./graphiti-core-src[groq,google-genai]

# Change ownership to app user
RUN chown -R app:app /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER app

# Set port
ENV PORT=8000
EXPOSE $PORT

# Use uv run for execution
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

