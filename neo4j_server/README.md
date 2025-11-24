# Neo4j Graphiti Server

A FastAPI server providing endpoints for Graphiti operations with Neo4j backend, supporting multiple LLM and embedding clients.

## Features

- **Basic Search**: Hybrid search combining semantic similarity and BM25 text retrieval
- **Center Node Search**: Rerank search results based on graph distance to a center node
- **Advanced Search**: Full graph search using `graphiti.search_()` returning nodes, edges, episodes, and communities
- **Add Episode**: Add episodes (text or JSON) to the graph for processing
- **Delete Embeddings**: Delete nodes and edges with embeddings by created date
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

### Delete Embeddings
```
DELETE /api/v1/embeddings
```
Deletes embeddings (nodes and edges) created before a specified date in a specified Neo4j database.

**Request body:**
```json
{
  "created_before": "2024-01-01T00:00:00Z",
  "database": "neo4j",
  "delete_nodes": true,
  "delete_edges": true
}
```

**Response:**
```json
{
  "message": "Successfully deleted embeddings created before 2024-01-01T00:00:00Z",
  "success": true,
  "nodes_deleted": 10,
  "edges_deleted": 25
}
```

**Parameters:**
- `created_before` (required): ISO 8601 datetime string. Deletes all nodes and edges with embeddings created before this date.
- `database` (optional): Neo4j database name. Defaults to `"neo4j"`.
- `delete_nodes` (optional): Whether to delete Entity nodes with `name_embedding`. Defaults to `true`.
- `delete_edges` (optional): Whether to delete RELATES_TO edges with `fact_embedding`. Defaults to `true`.

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

You can set these environment variables in your `.env` file or as shell environment variables:

**Optional API Keys:**
- `GROQ_API_KEY`: Groq API key (optional, required only if using Groq LLM client)
- `GEMINI_API_KEY`: Gemini API key (optional, required only if using Gemini LLM or embedding client)

**Neo4j Credentials (optional, defaults provided):**
- `NEO4J_USER`: Neo4j username (defaults to `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (defaults to `password`)

**Ollama URLs (optional, defaults provided):**
- `OLLAMA_BASE_URL`: Base URL for Ollama LLM client (defaults to `http://host.docker.internal:11434/v1`)
- `OLLAMA_EMBEDDING_BASE_URL`: Base URL for Ollama embedding client (defaults to `OLLAMA_BASE_URL` if not set)

**Note:** When Neo4j starts for the first time, you may see a message like "Changed password for user 'neo4j'". This is normal - Neo4j is setting the initial password based on the `NEO4J_AUTH` environment variable, not changing an existing password.

**Other hardcoded settings:**
- Neo4j connection: `bolt://neo4j:7687` (default user: `neo4j`, default password: `password`)
- Model names are hardcoded (see `neo4j_server/app/client_factory.py` for details)

## Hardcoded Models

### Ollama (Default)
- LLM Model: `qwen3:30b-a3b-instruct-2507-q4_K_M`
- Small Model: `qwen3:30b-a3b-instruct-2507-q4_K_M`
- Embedding Model: `embeddinggemma:latest`
- Embedding Dimension: `768`

### Groq
- LLM Model: `openai/gpt-oss-120b`
- Small Model: `openai/gpt-oss-20b`

### Gemini
- LLM Model: `gemini-flash-latest`
- Small Model: `gemini-flash-lite-latest`
- Embedding Model: `gemini-embedding-001`

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
