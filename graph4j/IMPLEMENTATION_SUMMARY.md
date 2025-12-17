# Dual Database Embedding Implementation - Summary

## What Changed

The implementation has been refactored from a **single database with dual embeddings** approach to a **dual database architecture** where fast and quality embeddings are stored in separate Neo4j databases.

## Previous Implementation (Single Database)

### Architecture
- One Neo4j database
- Both embeddings stored in the same nodes:
  - `node.name_embedding`: Quality embeddings
  - `node.attributes['name_embedding_fast']`: Fast embeddings
- Required swapping embedders on a single Graphiti client

### Workflow
1. Extract with fast embedder
2. Save to database with fast embeddings
3. Generate quality embeddings for same nodes
4. Update nodes with quality embeddings in `name_embedding`
5. Preserve fast embeddings in `attributes['name_embedding_fast']`

### Issues
- Both embeddings in same database (no true isolation)
- Attribute overhead for storing fast embeddings
- Complex embedding swapping logic
- Single database must handle both use cases

## New Implementation (Dual Database)

### Architecture
- Two separate Neo4j databases:
  - **Fast Database**: Stores graph with fast embeddings
  - **Quality Database**: Stores graph with quality embeddings
- Two separate Graphiti clients:
  - `graphiti.fast_client`: Connected to fast database
  - `graphiti.quality_client`: Connected to quality database
- Each database has clean schema with single embedding type

### Workflow

#### Ingestion (Dual Mode)
1. LLM extraction with fast embedder (once)
2. Save to fast database with fast embeddings
3. Generate quality embeddings for same nodes
4. Save to quality database with quality embeddings

#### Search/Retrieval
- `"fast"` mode: Search fast database only
- `"default"` mode: Search quality database only
- `"dual"` mode: Search both databases and merge results

### Benefits
✅ **True Isolation**: Each embedding type has its own database
✅ **Performance**: No embedding swapping, no attribute filtering
✅ **Scalability**: Databases can be scaled independently
✅ **Simplicity**: Clean schema, straightforward logic
✅ **Backward Compatible**: Falls back to single database if not configured

## Files Changed

### 1. `config.py`
**Added:**
- `neo4j_fast_uri`: URI for fast database
- `neo4j_quality_uri`: URI for quality database
- Defaults to `neo4j_uri` if not specified (backward compatible)

### 2. `graphiti_client.py`
**Changed:**
- `get_graphiti()` now creates two separate Graphiti clients
- `fast_client`: Connected to fast database with fast embedder
- `quality_client`: Connected to quality database with quality embedder
- Main client is `quality_client` for backward compatibility
- Both clients stored as attributes for dual operations

### 3. `dual_embedding_graphiti.py`
**Completely Rewritten:**
- Removed deprecated POC code
- Added `add_episode_dual()`: Saves to both databases
- Added `search_dual()`: Searches appropriate database(s)
- Added `search_nodes_dual()`: Advanced node search across databases
- Added `is_dual_database_mode()`: Helper to check if using dual DBs

### 4. `routers/ingest.py`
**Changed:**
- Removed embedding swapping logic
- Routes to appropriate database based on `embedding_mode`:
  - `"fast"`: Save to fast database only
  - `"default"`: Save to quality database only
  - `"dual"`: Save to both databases using `add_episode_dual()`

### 5. `routers/search.py`
**Changed:**
- `search_nodes()`: Uses `search_nodes_dual()` to route searches
- `search_facts()`: Uses `search_dual()` to route searches
- Both support `embedding_mode` parameter in request

### 6. `dto.py`
**Added:**
- `embedding_mode` field to `NodeSearchRequest`
- `embedding_mode` field to `FactSearchRequest`
- Default value: `"default"` (quality database)

### 7. `.env.example`
**Added:**
- Documentation for `NEO4J_FAST_URI`
- Documentation for `NEO4J_QUALITY_URI`
- Examples showing dual database configuration

### 8. New Files
**Created:**
- `DUAL_DATABASE_README.md`: Comprehensive documentation
- `.agent/workflows/dual-database-embedding.md`: Implementation plan

## Configuration

### Single Database Mode (Default)
```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Dual Database Mode
```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Dual database configuration
NEO4J_FAST_URI=bolt://localhost:7688
NEO4J_QUALITY_URI=bolt://localhost:7687
```

## API Usage

### Ingestion
```json
POST /episodes
{
  "group_id": "user123",
  "embedding_mode": "dual",  // "fast", "default", or "dual"
  "episodes": [
    {
      "content": "User prefers dark roast coffee",
      "episode_type": "text"
    }
  ]
}
```

### Search
```json
POST /search/nodes
{
  "query": "coffee preferences",
  "embedding_mode": "fast",  // "fast", "default", or "dual"
  "max_nodes": 10
}
```

## Migration Path

### For New Projects
1. Set up two Neo4j databases
2. Configure `NEO4J_FAST_URI` and `NEO4J_QUALITY_URI`
3. Use `embedding_mode: "dual"` for ingestion
4. Use appropriate `embedding_mode` for searches

### For Existing Projects
1. Continue using single database mode (no configuration changes needed)
2. When ready, set up second database
3. Configure dual database URIs
4. Re-ingest data with `embedding_mode: "dual"`
5. Update search queries to specify `embedding_mode`

## Deprecated Files

The following files are now deprecated but kept for reference:
- `dual_embedding_utils.py`: Old single-database dual embedding approach
  - Still functional but not used by new implementation
  - Can be removed in future cleanup

## Testing Recommendations

1. **Single Database Mode**: Verify backward compatibility
   - Don't set `NEO4J_FAST_URI` or `NEO4J_QUALITY_URI`
   - Test all three embedding modes
   - Verify both clients connect to same database

2. **Dual Database Mode**: Verify dual database functionality
   - Set separate URIs for fast and quality databases
   - Test ingestion with each mode
   - Test search with each mode
   - Verify data in both databases

3. **Performance Testing**:
   - Compare search latency: fast vs quality databases
   - Measure ingestion time: single vs dual mode
   - Test concurrent operations on both databases

## Next Steps

1. ✅ Configuration updated for dual databases
2. ✅ Client initialization refactored
3. ✅ Dual database implementation complete
4. ✅ Routers updated to use dual databases
5. ✅ DTOs updated with embedding_mode
6. ✅ Documentation created

### Recommended Follow-ups:
- [ ] Set up second Neo4j database for testing
- [ ] Test dual database mode end-to-end
- [ ] Add database health checks
- [ ] Add metrics/logging for database operations
- [ ] Consider adding database migration scripts
- [ ] Add integration tests for dual database mode
