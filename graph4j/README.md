# Graph4j

Advanced Graphiti FastAPI Server with Hybrid Search and Reranking

## Overview

Graph4j is a FastAPI-based server that provides advanced search capabilities for Graphiti knowledge graphs. It supports dual embedding modes (fast and quality) and offers multiple search endpoints with hybrid search and reranking features.

## Features

- **Dual Database Architecture**: Support for both fast and quality embedding databases
- **Hybrid Search**: Combines multiple search strategies for optimal results
- **Center Node Search**: Graph-traversal-based reranking around a center node
- **Flexible Search Endpoints**: Multiple endpoints for different search use cases
- **Episode Ingestion**: Add and manage episodes with dual embedding support

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Neo4j database

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run with Docker Compose:

```bash
docker compose up -d
```

### Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

## API Endpoints

- `/search` - Main search endpoint with hybrid search capabilities
- `/search/facts` - Fact-based hybrid search
- `/ingest/episodes` - Add episodes to the knowledge graph
- `/health` - Health check endpoint

## Configuration

See `.env.example` for available configuration options.
