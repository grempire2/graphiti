# How to Run Graph4j with Ollama

## Quick Start (Docker - Recommended)

### Prerequisites
1. **Docker Desktop** installed and running
2. **Ollama** installed and running on your host machine
3. Required Ollama models installed:
   ```bash
   ollama pull llama3.2:latest
   ollama pull nomic-embed-text:latest
   ```

### Steps

1. **Ensure Ollama is running** (on port 11435)
   ```bash
   ollama serve
   ```

2. **Navigate to graph4j directory**
   ```bash
   cd d:\Github\graphiti\graph4j
   ```

3. **Start the services**
   ```bash
   docker compose up -d
   ```

4. **Verify services are running**
   ```bash
   docker compose ps
   docker compose logs -f
   ```

5. **Access the API**
   - API: http://localhost:8001
   - Swagger UI: http://localhost:8001/docs
   - Neo4j Browser: http://localhost:7474 (user: neo4j, password: password)

### Stop the services
```bash
docker compose down
```

### Stop and remove all data
```bash
docker compose down -v
```

---

## Alternative: Local Development

If you prefer to run graph4j locally (not in Docker):

### Prerequisites
1. Python 3.10+
2. Ollama running on port 11435
3. Neo4j running (can use Docker)

### Steps

1. **Start Neo4j**
   ```bash
   docker run -d \
     --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:5.26.2
   ```

2. **Install dependencies**
   ```bash
   cd d:\Github\graphiti\graph4j
   pip install -e .
   ```

3. **Run the server**
   ```bash
   uvicorn main:app --reload --port 8001
   ```

---

## Configuration

The `.env` file is already configured with these defaults:

```env
# Ollama Configuration
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11435/v1

# Ollama Models
MODEL_NAME=llama3.2:latest
EMBEDDING_MODEL_NAME=nomic-embed-text:latest

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_PORT=7687
```

### Important Notes

- **Ollama Port**: Default is **11435** (not 11434)
- **Neo4j Password**: Default is **password**
- **Docker Network**: When using docker-compose, graph4j and Neo4j are on the same network
- **Ollama Access from Docker**: Uses `host.docker.internal:11435` to access Ollama on host

---

## Testing the API

### 1. Add test data
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

### 2. Search for nodes (Hybrid Search with RRF)
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

---

## Troubleshooting

### Ollama Connection Issues
1. Verify Ollama is running: `ollama list`
2. Check Ollama is on port 11435
3. Ensure models are installed:
   - `ollama pull llama3.2:latest`
   - `ollama pull nomic-embed-text:latest`

### Neo4j Connection Issues
1. Check Neo4j is running: `docker ps | grep neo4j`
2. Verify credentials: neo4j/password
3. Check logs: `docker compose logs neo4j`

### Docker Issues
1. Ensure Docker Desktop is running
2. Check container status: `docker compose ps`
3. View logs: `docker compose logs -f`
4. Rebuild if needed: `docker compose up --build`

---

## Key Features

✅ **Hybrid Search** - BM25 + Cosine Similarity  
✅ **RRF Reranking** - Reciprocal Rank Fusion  
✅ **Entity Type Filtering** - Filter by Preference, Location, etc.  
✅ **Center Node Search** - Graph distance-based reranking  
✅ **Ollama Integration** - No OpenAI API key required  
✅ **Docker Ready** - Complete containerized setup
