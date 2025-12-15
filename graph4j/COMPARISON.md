# Comparison: graph4j vs server vs mcp_server

This document compares the three Graphiti server implementations in the repository.

## Overview

| Feature | `server` | `graph4j` | `mcp_server` |
|---------|----------|-----------|--------------|
| **Purpose** | Basic REST API | Advanced REST API | MCP Protocol Server |
| **Search Type** | Simple | **Hybrid + RRF** | **Hybrid + RRF** |
| **Protocol** | REST | REST | MCP + REST |
| **Complexity** | Low | Medium | High |
| **Use Case** | Simple integration | Advanced search | AI assistant integration |

## Detailed Feature Comparison

### Search Capabilities

| Feature | `server` | `graph4j` | `mcp_server` |
|---------|----------|-----------|--------------|
| **Basic Search** | ✅ | ✅ | ✅ |
| **Hybrid Search** | ❌ | ✅ **BM25 + Cosine** | ✅ **BM25 + Cosine** |
| **Reranking** | ❌ | ✅ **RRF** | ✅ **RRF** |
| **Node Search** | ❌ | ✅ **Advanced** | ✅ **Advanced** |
| **Fact Search** | ✅ Basic | ✅ **Advanced** | ✅ **Advanced** |
| **Entity Type Filter** | ❌ | ✅ | ✅ |
| **Center Node Search** | ❌ | ✅ | ✅ |
| **Search Filters** | ❌ | ✅ | ✅ |

### Architecture

| Aspect | `server` | `graph4j` | `mcp_server` |
|--------|----------|-----------|--------------|
| **Lines of Code** | ~200 | ~500 | ~1000+ |
| **Dependencies** | Minimal | Minimal | MCP + Many |
| **Configuration** | Simple .env | Simple .env | Advanced YAML |
| **Transport** | HTTP only | HTTP only | HTTP + stdio |
| **Database Support** | Neo4j only | Neo4j only | Neo4j + FalkorDB |
| **LLM Providers** | OpenAI default | OpenAI default | 5+ providers |

### API Endpoints

#### `server` (Basic)
```
POST   /search              - Basic search
POST   /messages            - Add messages
POST   /entity-node         - Add entity node
GET    /entity-edge/{uuid}  - Get edge
GET    /episodes/{group_id} - Get episodes
DELETE /entity-edge/{uuid}  - Delete edge
DELETE /episode/{uuid}      - Delete episode
DELETE /group/{group_id}    - Delete group
POST   /clear               - Clear graph
```

#### `graph4j` (Advanced)
```
POST   /search/nodes        - 🌟 Advanced node search (Hybrid + RRF)
POST   /search/facts        - 🌟 Advanced fact search (with center node)
POST   /search              - Legacy basic search
POST   /messages            - Add messages
POST   /entity-node         - Add entity node
GET    /entity-edge/{uuid}  - Get edge
GET    /episodes/{group_id} - Get episodes
DELETE /entity-edge/{uuid}  - Delete edge
DELETE /episode/{uuid}      - Delete episode
DELETE /group/{group_id}    - Delete group
POST   /clear               - Clear graph
GET    /healthcheck         - Health check
```

#### `mcp_server` (MCP Protocol)
```
MCP Tools (via MCP protocol):
- add_memory              - Add episodes
- search_nodes            - 🌟 Advanced node search
- search_memory_facts     - 🌟 Advanced fact search
- get_entity_edge         - Get edge by UUID
- get_episodes            - Get episodes
- delete_entity_edge      - Delete edge
- delete_episode          - Delete episode
- clear_graph             - Clear graph
- get_status              - Server status

HTTP Endpoints:
GET    /health             - Health check
POST   /mcp/               - MCP protocol endpoint
```

## Search Quality Comparison

### Example: Searching for "coffee preferences"

#### `server` (Basic Search)
```python
POST /search
{
  "query": "coffee preferences",
  "group_ids": ["user123"],
  "max_facts": 10
}
```
**How it works:**
- Single search method (likely cosine similarity)
- No reranking
- Returns facts only
- Basic relevance scoring

**Result Quality:** ⭐⭐⭐ (Good)

---

#### `graph4j` (Advanced Search)
```python
POST /search/nodes
{
  "query": "coffee preferences",
  "group_ids": ["user123"],
  "max_nodes": 10,
  "entity_types": ["Preference"]
}
```
**How it works:**
1. **BM25 search** - Finds exact keyword matches
2. **Cosine Similarity search** - Finds semantic matches
3. **RRF Reranking** - Combines both results optimally
4. **Entity Type Filtering** - Only returns Preference nodes
5. Returns rich node information

**Result Quality:** ⭐⭐⭐⭐⭐ (Excellent)

---

#### `mcp_server` (MCP + Advanced Search)
```python
# Via MCP protocol
search_nodes(
  query="coffee preferences",
  group_ids=["user123"],
  max_nodes=10,
  entity_types=["Preference"]
)
```
**How it works:**
- Same advanced search as graph4j
- Plus MCP protocol overhead
- Designed for AI assistant integration
- Additional features: queue processing, multiple LLM providers, etc.

**Result Quality:** ⭐⭐⭐⭐⭐ (Excellent)

## When to Use Each

### Use `server` when:
- ✅ You need a simple REST API
- ✅ Basic search is sufficient
- ✅ You want minimal dependencies
- ✅ You're building a simple integration
- ❌ You don't need advanced search features

### Use `graph4j` when:
- ✅ You need **advanced search** (hybrid + reranking)
- ✅ You want **entity type filtering**
- ✅ You need **center node search**
- ✅ You want REST API without MCP overhead
- ✅ You know which methods you need (no need for MCP discovery)
- ✅ **You want the best search quality without complexity**

### Use `mcp_server` when:
- ✅ You're building AI assistant integrations (Claude, Cursor, etc.)
- ✅ You need MCP protocol support
- ✅ You want multiple LLM provider support
- ✅ You need multiple database backends (Neo4j + FalkorDB)
- ✅ You want advanced configuration (YAML)
- ✅ You need queue-based processing
- ❌ You don't mind the additional complexity

## Code Example Comparison

### Basic Search (`server`)
```python
# Simple search - no advanced features
relevant_edges = await graphiti.search(
    group_ids=query.group_ids,
    query=query.query,
    num_results=query.max_facts,
)
```

### Advanced Search (`graph4j`)
```python
# Hybrid search with RRF reranking
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core.search.search_filters import SearchFilters

search_filters = SearchFilters(
    node_labels=entity_types,  # Filter by entity types
)

results = await graphiti.search_(
    query=query,
    config=NODE_HYBRID_SEARCH_RRF,  # BM25 + Cosine + RRF
    group_ids=group_ids,
    search_filter=search_filters,
)
```

## Performance Characteristics

| Metric | `server` | `graph4j` | `mcp_server` |
|--------|----------|-----------|--------------|
| **Startup Time** | Fast | Fast | Medium |
| **Memory Usage** | Low | Low | Medium |
| **Search Latency** | Low | Medium | Medium |
| **Search Quality** | Good | **Excellent** | **Excellent** |
| **Complexity** | Low | Medium | High |

## Migration Path

### From `server` to `graph4j`
1. Copy your `.env` file
2. Update import paths
3. Start using `/search/nodes` and `/search/facts` endpoints
4. Enjoy better search quality! 🎉

### From `graph4j` to `mcp_server`
1. Only if you need MCP protocol support
2. Configure YAML instead of .env
3. Use MCP tools instead of REST endpoints
4. Integrate with AI assistants

## Recommendation

**For most use cases requiring advanced search: Use `graph4j`** ✅

It provides the same advanced search capabilities as `mcp_server` without the MCP protocol overhead, making it perfect for:
- Direct API integrations
- Custom applications
- When you know which methods you need
- When you want maximum search quality with minimal complexity
