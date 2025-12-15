# Graph4j Quick Start Guide

## Prerequisites

1. Python 3.10 or higher
2. Neo4j database (running locally or remotely)
3. Ollama with models installed (default) or OpenAI API key

## Installation

### 1. Navigate to the graph4j directory

```bash
cd d:\Github\graphiti\graph4j
```

### 2. Create and activate a virtual environment (optional but recommended)

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
# Or for development:
pip install -e ".[dev]"
```

### 4. Configure environment variables

```bash
# Copy the example env file
copy .env.example .env

# Edit .env if needed (default is already configured for Ollama):
# - OPENAI_API_KEY=ollama (default)
# - OPENAI_BASE_URL=http://localhost:11435/v1 (default)
# - MODEL_NAME=llama3.2:latest (default)
# - EMBEDDING_MODEL_NAME=nomic-embed-text:latest (default)
# - NEO4J_URI, NEO4J_USER=neo4j, NEO4J_PASSWORD=password (defaults)
```

### 5. Start the services

**Option A: Using Docker (Recommended)**

This starts both graph4j and Neo4j in containers on the same network:

```bash
cd d:\Github\graphiti\graph4j
docker compose up -d
```

Check the logs:
```bash
docker compose logs -f
```

**Option B: Local Development**

If running locally, start Neo4j first:

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.26.2
```

Then run graph4j:

```bash
cd d:\Github\graphiti\graph4j
uvicorn main:app --reload --port 8001
```

The server will be available at:
- API: http://localhost:8001
- Swagger Docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Testing the Advanced Search

### 1. Add some test data

```bash
curl -X POST "http://localhost:8001/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "test_user",
    "messages": [
      {
        "content": "I prefer dark roast coffee in the morning",
        "role": "user",
        "role_type": "human"
      }
    ]
  }'
```

### 2. Search for nodes (Advanced Hybrid Search)

```bash
curl -X POST "http://localhost:8001/search/nodes" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee preferences",
    "group_ids": ["test_user"],
    "max_nodes": 5,
    "entity_types": ["Preference"]
  }'
```

### 3. Search for facts

```bash
curl -X POST "http://localhost:8001/search/facts" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "morning coffee",
    "group_ids": ["test_user"],
    "max_facts": 10
  }'
```

## Key Differences from Basic Server

### Advanced Search Features

1. **Hybrid Search**: Combines BM25 (keyword) + Cosine Similarity (semantic)
2. **RRF Reranking**: Better result quality through Reciprocal Rank Fusion
3. **Entity Type Filtering**: Filter by Preference, Location, Requirement, etc.
4. **Center Node Search**: Rerank by graph distance for contextual relevance

### Example: Entity Type Filtering

```python
# Search only for user preferences
{
  "query": "what does the user like",
  "entity_types": ["Preference"]
}

# Search for locations and events
{
  "query": "where did the user go",
  "entity_types": ["Location", "Event"]
}
```

### Example: Center Node Search

```python
# First, get a node UUID
nodes = search_nodes({"query": "user", "max_nodes": 1})
center_uuid = nodes["nodes"][0]["uuid"]

# Then search facts centered around that node
{
  "query": "preferences",
  "center_node_uuid": center_uuid
}
# Results will be reranked based on graph distance from the user node
```

## Troubleshooting

### Connection Errors

If you get Neo4j connection errors:
1. Verify Neo4j is running: `docker ps` or check Neo4j Desktop
2. Check credentials in `.env` file
3. Verify URI format: `bolt://localhost:7687`

### Import Errors

If you get import errors:
1. Make sure you're in the graph4j directory
2. Install dependencies: `pip install -e .`
3. Check Python version: `python --version` (should be 3.10+)

### Ollama/LLM Errors

If you get LLM-related errors:
1. Make sure Ollama is running: `ollama serve`
2. Verify models are installed: `ollama list`
3. Pull required models if needed:
   - `ollama pull llama3.2:latest`
   - `ollama pull nomic-embed-text:latest`
4. Check OPENAI_BASE_URL in `.env` points to Ollama: `http://localhost:11435/v1`
5. For OpenAI instead, set `OPENAI_API_KEY` to your actual API key and remove `OPENAI_BASE_URL`

## Next Steps

- Explore the Swagger docs at http://localhost:8001/docs
- Try different entity types: Preference, Requirement, Location, Event, Organization, Document, Topic, Object
- Experiment with center node search for contextual results
- Compare results with and without entity type filtering
