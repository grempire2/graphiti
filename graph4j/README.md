# Graph4j - Advanced Graphiti FastAPI Server

Graph4j is an advanced FastAPI server implementing the [graphiti](https://github.com/getzep/graphiti) package with **hybrid search capabilities** and **reranking**.

## Key Features

- **Hybrid Search**: Combines BM25 (keyword) + Cosine Similarity (semantic) search
- **Advanced Reranking**: RRF (Reciprocal Rank Fusion) for better result quality
- **Node Search**: Search for entity nodes with filtering by entity types
- **Fact Search**: Search for relationships/edges with optional center node reranking
- **No MCP Overhead**: Direct FastAPI endpoints without MCP protocol complexity

## What Makes This Advanced?

Unlike the basic `server` implementation, Graph4j uses:

1. **`NODE_HYBRID_SEARCH_RRF`** - Hybrid search configuration with RRF reranking
2. **Entity Type Filtering** - Filter search results by entity types (Preference, Location, etc.)
3. **Center Node Search** - Rerank results based on graph distance from a specific node
4. **SearchFilters** - Advanced filtering capabilities
5. **Dual Search Methods** - BM25 for exact matches + Cosine Similarity for semantic understanding

## Running Instructions

1. Ensure you have Docker and Docker Compose installed on your system.

2. Create a `.env` file in the `graph4j` directory:

   ```env
   # Ollama Configuration (OpenAI-compatible)
   OPENAI_API_KEY=ollama
   OPENAI_BASE_URL=http://localhost:11435/v1
   
   # Model Configuration for Ollama
   MODEL_NAME=llama3.2:latest
   EMBEDDING_MODEL_NAME=nomic-embed-text:latest
   
   # Neo4j Configuration
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   NEO4J_PORT=7687
   ```

3. Start the service:

   **Option A: Using Docker (Recommended)**
   
   ```bash
   cd graph4j
   docker compose up -d
   ```
   
   This will start both graph4j and Neo4j containers on the same network.

   **Option B: Local Development**
   
   Make sure Neo4j is running first, then:
   
   ```bash
   cd graph4j
   uvicorn main:app --reload --port 8001
   ```

4. The service will be available at `http://localhost:8001`

5. Access the API documentation:
   - Swagger UI: `http://localhost:8001/docs`
   - ReDoc: `http://localhost:8001/redoc`

## API Endpoints

### Search Endpoints

#### POST `/search/nodes` - Advanced Node Search
Search for entity nodes using hybrid search with RRF reranking.

**Request Body:**
```json
{
  "query": "user preferences for coffee",
  "group_ids": ["user123"],
  "max_nodes": 10,
  "entity_types": ["Preference", "Requirement"]
}
```

**Response:**
```json
{
  "nodes": [
    {
      "uuid": "node-uuid",
      "name": "Coffee Preference",
      "labels": ["Preference"],
      "summary": "User prefers dark roast coffee",
      "group_id": "user123",
      "created_at": "2024-01-01T00:00:00Z",
      "attributes": {}
    }
  ]
}
```

#### POST `/search/facts` - Advanced Fact Search
Search for facts/edges with optional center node reranking.

**Request Body:**
```json
{
  "query": "coffee preferences",
  "group_ids": ["user123"],
  "max_facts": 10,
  "center_node_uuid": "optional-center-node-uuid"
}
```

**Response:**
```json
{
  "facts": [
    {
      "uuid": "edge-uuid",
      "name": "preference",
      "fact": "User prefers dark roast coffee in the morning",
      "valid_at": "2024-01-01T00:00:00Z",
      "invalid_at": null,
      "created_at": "2024-01-01T00:00:00Z",
      "expired_at": null
    }
  ]
}
```

### Ingest Endpoints

#### POST `/messages` - Add Messages
Add conversation messages to the knowledge graph.

#### POST `/entity-node` - Add Entity Node
Manually add an entity node to the graph.

### Management Endpoints

#### DELETE `/entity-edge/{uuid}` - Delete Edge
#### DELETE `/episode/{uuid}` - Delete Episode
#### DELETE `/group/{group_id}` - Delete Group
#### POST `/clear` - Clear Graph

## Comparison with Basic Server

| Feature | Basic Server | Graph4j |
|---------|-------------|---------|
| Search Type | Simple | **Hybrid (BM25 + Cosine)** |
| Reranking | None | **RRF** |
| Node Search | ❌ | ✅ |
| Entity Filtering | ❌ | ✅ |
| Center Node Search | ❌ | ✅ |
| Search Quality | Basic | **Advanced** |

## License

This project is licensed under the same license as the parent Graphiti project.
