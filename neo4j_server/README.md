# Neo4j Graphiti Server

A FastAPI server providing endpoints for Graphiti operations with Neo4j backend, supporting multiple LLM and embedding clients.

## Features

- **Basic Search**: Hybrid search combining semantic similarity and BM25 text retrieval
- **Center Node Search**: Rerank search results based on graph distance to a center node
- **Advanced Search**: Full graph search using `graphiti.search_()` returning nodes, edges, episodes, and communities
- **Add Episode**: Add episodes (text or JSON) to the graph for processing
- **Multi-Client Support**: Choose from Groq, Gemini, or Ollama for LLM, and Gemini or Ollama for embeddings

## Endpoints

All endpoints require specifying which LLM client and embedding client to use.

### Basic Search
```
POST /api/v1/search/basic
```
Performs a basic search using `graphiti.search()`, returning edges (facts) from the graph.

**Request body:**
```json
{
  "query": "your search query",
  "llm_client": "groq|gemini|ollama",
  "embedder_client": "gemini|ollama",
  "group_ids": ["optional", "group", "ids"],
  "num_results": 10
}
```

### Center Node Search
```
POST /api/v1/search/center
```
Performs a search with center node reranking using `graphiti.search()` with `center_node_uuid`.

**Request body:**
```json
{
  "query": "your search query",
  "center_node_uuid": "uuid-of-center-node",
  "llm_client": "groq|gemini|ollama",
  "embedder_client": "gemini|ollama",
  "group_ids": ["optional", "group", "ids"],
  "num_results": 10
}
```

### Advanced Search
```
POST /api/v1/search/advanced
```
Performs an advanced search using `graphiti.search_()`, returning nodes, edges, episodes, and communities.

**Request body:**
```json
{
  "query": "your search query",
  "llm_client": "groq|gemini|ollama",
  "embedder_client": "gemini|ollama",
  "group_ids": ["optional", "group", "ids"],
  "center_node_uuid": "optional-center-node-uuid",
  "limit": 10
}
```

### Add Episode
```
POST /api/v1/episodes
```
Adds an episode to the graph using `graphiti.add_episode()`.

**Request body:**
```json
{
  "name": "Episode name",
  "episode_body": "Content of the episode",
  "llm_client": "groq|gemini|ollama",
  "embedder_client": "gemini|ollama",
  "source": "text|json|message",
  "source_description": "Description",
  "group_id": "optional-group-id",
  "uuid": "optional-uuid",
  "reference_time": "2024-01-01T00:00:00Z"
}
```

## Running with Docker Compose

1. Create a `.env` file in the `neo4j_server` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

2. Ensure Ollama is running on your host machine (for Ollama client support):
```bash
ollama serve
```

3. Run with docker-compose:
```bash
cd neo4j_server
docker-compose up
```

The server will be available at `http://localhost:18888` and Neo4j at `http://localhost:7474`.

## Environment Variables

Only these two environment variables are read from `.env`:
- `GROQ_API_KEY`: Groq API key (optional, required only if using Groq LLM client)
- `GEMINI_API_KEY`: Gemini API key (optional, required only if using Gemini LLM or embedding client)

All other settings are hardcoded:
- Neo4j connection: `bolt://neo4j:7687`, user: `neo4j`, password: `password`
- Ollama base URL: `http://host.docker.internal:11434/v1`
- Model names are hardcoded (see `neo4j_server/clients.py` for details)

## Hardcoded Models

### Groq
- LLM Model: `llama-3.1-70b-versatile`
- Small Model: `llama-3.1-70b-versatile`

### Gemini
- LLM Model: `gemini-2.5-flash`
- Small Model: `gemini-2.5-flash-lite-preview-06-17`
- Embedding Model: `text-embedding-001`

### Ollama
- LLM Model: `deepseek-r1:7b`
- Small Model: `deepseek-r1:7b`
- Embedding Model: `nomic-embed-text`
- Embedding Dimension: `768`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:18888/docs`
- ReDoc: `http://localhost:18888/redoc`

## Testing

A test script is provided to test all endpoints. It follows a similar structure to the quickstart example.

### Running the Test Script

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Make sure the server is running (via docker-compose or directly)

3. Set environment variables (optional):
```bash
export SERVER_URL=http://localhost:18888  # Default
export LLM_CLIENT=ollama  # Default: ollama
export EMBEDDER_CLIENT=ollama  # Default: ollama
```

4. Run the test script:
```bash
python test_server.py
```

The test script will:
- Add episodes (text and JSON) to the graph
- Perform basic search
- Perform center node search
- Perform advanced search
- Test different client combinations (if API keys are available)

The script uses the same example data as `examples/quickstart/quickstart_neo4j.py` for consistency.
