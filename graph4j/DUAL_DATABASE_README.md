# Dual Database Embedding Architecture

## Overview

This implementation provides a **dual Neo4j database architecture** for storing different embedding formats. Instead of storing both fast and quality embeddings in a single database, this approach uses two separate databases for true isolation and optimized performance.

## Architecture

### Database Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (FastAPI + Graphiti Client with Dual Database Support)     │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    │                    │
        ┌───────────▼──────────┐  ┌─────▼──────────────┐
        │   Fast Database      │  │  Quality Database  │
        │  (Fast Embeddings)   │  │ (Quality Embeddings)│
        │                      │  │                     │
        │  - Same graph        │  │  - Same graph       │
        │    structure         │  │    structure        │
        │  - Fast embedder     │  │  - Quality embedder │
        │  - Quick responses   │  │  - High accuracy    │
        └──────────────────────┘  └─────────────────────┘
```

### Components

1. **Fast Client** (`graphiti.fast_client`)
   - Connected to fast database (NEO4J_FAST_URI)
   - Uses fast embedder (e.g., nomic-embed-text)
   - Optimized for speed

2. **Quality Client** (`graphiti.quality_client`)
   - Connected to quality database (NEO4J_QUALITY_URI)
   - Uses quality embedder (e.g., qwen3-embedding)
   - Optimized for accuracy

## Configuration

### Single Database Mode (Default)

If you don't specify separate database URIs, the system operates in single database mode for backward compatibility:

```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

Both fast and quality clients will connect to the same database.

### Dual Database Mode

To enable true dual database architecture, set separate URIs:

```bash
# .env
NEO4J_URI=bolt://localhost:7687  # Default/fallback
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Dual database configuration
NEO4J_FAST_URI=bolt://localhost:7688    # Fast database
NEO4J_QUALITY_URI=bolt://localhost:7687  # Quality database
```

## Workflow

### 1. Ingestion

#### Fast Mode
```
POST /episodes
{
  "embedding_mode": "fast",
  "episodes": [...]
}
```
- Saves **only** to fast database
- Uses fast embedder for extraction and embeddings

#### Default Mode
```
POST /episodes
{
  "embedding_mode": "default",
  "episodes": [...]
}
```
- Saves **only** to quality database
- Uses quality embedder for extraction and embeddings

#### Dual Mode
```
POST /episodes
{
  "embedding_mode": "dual",
  "episodes": [...]
}
```
- LLM extraction happens **once** using fast embedder (speed priority)
- Saves to **both** databases:
  1. Fast database with fast embeddings
  2. Quality database with quality embeddings
- Same graph structure in both databases

### 2. Search/Retrieval

#### Node Search
```
POST /search/nodes
{
  "query": "user preferences",
  "embedding_mode": "fast",  // or "default" or "dual"
  "max_nodes": 10
}
```

#### Fact Search
```
POST /search/facts
{
  "query": "coffee preferences",
  "embedding_mode": "default",  // or "fast" or "dual"
  "max_facts": 10
}
```

**Embedding Modes:**
- `"fast"`: Search only fast database (quick responses)
- `"default"`: Search only quality database (high accuracy)
- `"dual"`: Search both databases and merge results

## Benefits

### 1. True Isolation
- Each embedding type has its own dedicated database
- No schema modifications needed
- Clean separation of concerns

### 2. Performance
- Fast database optimized for speed
- Quality database optimized for accuracy
- No need to swap embeddings or filter attributes

### 3. Scalability
- Databases can be scaled independently
- Fast database can handle high-volume, low-latency queries
- Quality database can handle complex, accuracy-critical queries

### 4. Flexibility
- Per-request embedding mode selection
- Can use single database mode for development
- Can use dual database mode for production

## Implementation Details

### Key Files

1. **`config.py`**
   - Added `neo4j_fast_uri` and `neo4j_quality_uri` settings
   - Defaults to `neo4j_uri` if not specified

2. **`graphiti_client.py`**
   - Creates two separate Graphiti clients
   - `fast_client`: Connected to fast database
   - `quality_client`: Connected to quality database

3. **`dual_embedding_graphiti.py`**
   - `add_episode_dual()`: Saves to both databases
   - `search_dual()`: Searches appropriate database(s)
   - `search_nodes_dual()`: Advanced node search across databases

4. **`routers/ingest.py`**
   - Routes ingestion to appropriate database based on mode
   - Handles dual mode by calling both databases

5. **`routers/search.py`**
   - Routes searches to appropriate database based on mode
   - Supports merging results in dual mode

### Database Initialization

For dual database mode, you need to initialize both databases:

```python
# Initialize fast database
await fast_client.build_indices_and_constraints()

# Initialize quality database
await quality_client.build_indices_and_constraints()
```

## Migration from Single Database

If you're currently using the single database approach with `node.attributes['name_embedding_fast']`, you can migrate to dual database mode:

1. Set up a second Neo4j database
2. Configure `NEO4J_FAST_URI` and `NEO4J_QUALITY_URI`
3. Re-ingest your data using `embedding_mode: "dual"`
4. Update your search queries to specify `embedding_mode`

## Performance Considerations

### Single Database Mode
- **Pros**: Simple setup, single database to manage
- **Cons**: Both embeddings stored in same database, potential attribute overhead

### Dual Database Mode
- **Pros**: True isolation, optimized performance, independent scaling
- **Cons**: Two databases to manage, duplicate graph structure

## Example Usage

### Python Client
```python
import httpx

# Ingest with dual mode
response = httpx.post("http://localhost:8000/episodes", json={
    "group_id": "user123",
    "embedding_mode": "dual",
    "episodes": [{
        "content": "User prefers dark roast coffee",
        "episode_type": "text"
    }]
})

# Search with fast mode (quick response)
response = httpx.post("http://localhost:8000/search/nodes", json={
    "query": "coffee preferences",
    "embedding_mode": "fast",
    "max_nodes": 5
})

# Search with quality mode (high accuracy)
response = httpx.post("http://localhost:8000/search/facts", json={
    "query": "coffee preferences",
    "embedding_mode": "default",
    "max_facts": 10
})
```

## Troubleshooting

### Both databases show same URI in logs
- Check that `NEO4J_FAST_URI` and `NEO4J_QUALITY_URI` are set in `.env`
- Verify they're different values

### Search returns no results
- Ensure data was ingested with the correct `embedding_mode`
- Check that the search `embedding_mode` matches the ingestion mode
- Verify both databases are running and accessible

### Dual mode ingestion is slow
- This is expected - dual mode saves to both databases
- Consider using "fast" mode for initial ingestion
- Use "dual" mode only when you need both embedding types
