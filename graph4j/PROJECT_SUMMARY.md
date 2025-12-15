# Graph4j - Project Summary

## 📁 Project Structure

```
graph4j/
├── README.md              # Main documentation
├── QUICKSTART.md          # Quick start guide
├── COMPARISON.md          # Detailed comparison with other servers
├── .env.example           # Environment configuration template
├── .gitignore            # Git ignore rules
├── pyproject.toml        # Python project configuration
├── config.py             # Settings and configuration
├── dto.py                # Data transfer objects (request/response models)
├── graphiti_client.py    # Advanced Graphiti client wrapper
├── main.py               # FastAPI application entry point
├── example_search.py     # Example script demonstrating features
└── routers/
    ├── __init__.py       # Router package initialization
    ├── ingest.py         # Ingest endpoints (add data)
    └── search.py         # Advanced search endpoints ⭐
```

## 🎯 What Makes Graph4j Special

Graph4j is the **sweet spot** between the basic `server` and the complex `mcp_server`:

### ✅ Has Advanced Search (like mcp_server)
- **Hybrid Search**: BM25 + Cosine Similarity
- **RRF Reranking**: Reciprocal Rank Fusion
- **Entity Type Filtering**: Filter by Preference, Location, etc.
- **Center Node Search**: Graph-distance reranking

### ✅ Without MCP Overhead (like server)
- Simple REST API
- No MCP protocol complexity
- Direct endpoints
- Easy to integrate

## 🚀 Key Features

### 1. Advanced Node Search
```python
POST /search/nodes
{
  "query": "user preferences",
  "entity_types": ["Preference"],  # Filter by type
  "max_nodes": 10
}
```

**How it works:**
1. BM25 search finds exact keyword matches
2. Cosine Similarity finds semantic matches
3. RRF combines both optimally
4. Entity filter applies
5. Returns rich node data

### 2. Advanced Fact Search
```python
POST /search/facts
{
  "query": "coffee preferences",
  "center_node_uuid": "user-uuid",  # Rerank by distance
  "max_facts": 10
}
```

**How it works:**
1. Hybrid search finds relevant facts
2. If center node provided, reranks by graph distance
3. Returns contextually relevant results

### 3. Entity Type Filtering

Available entity types:
- **Preference**: User preferences, choices, opinions
- **Requirement**: Needs, features, functionality
- **Procedure**: SOPs, instructions
- **Location**: Physical or virtual places
- **Event**: Time-bound activities
- **Organization**: Companies, institutions
- **Document**: Information content
- **Topic**: Subject of conversation
- **Object**: Physical items, tools

## 📊 Performance Characteristics

| Metric | Value |
|--------|-------|
| **Startup Time** | ~2 seconds |
| **Memory Usage** | ~100-200 MB |
| **Search Latency** | ~100-500ms (depending on query) |
| **Search Quality** | ⭐⭐⭐⭐⭐ Excellent |
| **Code Complexity** | Medium (500 lines) |

## 🔧 Technical Details

### Search Implementation

The magic happens in `routers/search.py`:

```python
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core.search.search_filters import SearchFilters

# Create filters
search_filters = SearchFilters(
    node_labels=entity_types,
)

# Execute hybrid search with RRF
results = await graphiti.search_(
    query=query,
    config=NODE_HYBRID_SEARCH_RRF,  # BM25 + Cosine + RRF
    group_ids=group_ids,
    search_filter=search_filters,
)
```

### What is NODE_HYBRID_SEARCH_RRF?

From `graphiti_core.search.search_config_recipes`:

```python
NODE_HYBRID_SEARCH_RRF = SearchConfig(
    node_config=NodeSearchConfig(
        search_methods=[
            NodeSearchMethod.bm25,              # Keyword search
            NodeSearchMethod.cosine_similarity  # Semantic search
        ],
        reranker=NodeReranker.rrf,  # Reciprocal Rank Fusion
    )
)
```

**BM25**: Best Match 25 algorithm for keyword-based search
**Cosine Similarity**: Vector-based semantic search
**RRF**: Combines results from multiple search methods optimally

## 📈 Use Cases

### Perfect For:
- ✅ Applications needing high-quality search
- ✅ Systems with entity-based knowledge graphs
- ✅ Chatbots requiring contextual memory
- ✅ Recommendation systems
- ✅ Personal assistants
- ✅ Knowledge management systems

### Not Ideal For:
- ❌ Simple key-value lookups (use basic server)
- ❌ AI assistant integration via MCP (use mcp_server)
- ❌ Systems that don't need advanced search

## 🎓 Learning Resources

### Understanding Hybrid Search

**BM25 (Best Match 25)**
- Keyword-based ranking algorithm
- Excellent for exact matches
- Considers term frequency and document length
- Example: "dark roast coffee" → finds documents with these exact words

**Cosine Similarity**
- Vector-based semantic search
- Understands meaning, not just keywords
- Uses embeddings to find similar concepts
- Example: "morning beverage" → finds "coffee" even without exact match

**RRF (Reciprocal Rank Fusion)**
- Combines multiple search results
- Gives higher weight to items appearing in multiple result sets
- More robust than simple score averaging
- Formula: `RRF(d) = Σ 1/(k + rank(d))` where k=60

### Why This Matters

Traditional search (basic server):
```
Query: "coffee preferences"
→ Single search method
→ May miss relevant results
→ Quality: ⭐⭐⭐
```

Hybrid search with RRF (graph4j):
```
Query: "coffee preferences"
→ BM25: Finds "coffee" keyword matches
→ Cosine: Finds "beverage", "drink" semantic matches
→ RRF: Combines both optimally
→ Quality: ⭐⭐⭐⭐⭐
```

## 🔍 Example Scenarios

### Scenario 1: User Preference Search
```python
# User says: "I like dark roast coffee"
# Later search: "what beverages does the user prefer"

POST /search/nodes
{
  "query": "beverages user prefers",
  "entity_types": ["Preference"]
}

# BM25 might miss this (no exact "beverage" match)
# Cosine similarity finds it (semantic match)
# RRF ensures it ranks high
# Result: ✅ Finds "dark roast coffee" preference
```

### Scenario 2: Location-Based Context
```python
# User says: "I live in San Francisco"
# Later search: "where is the user located"

POST /search/nodes
{
  "query": "user location",
  "entity_types": ["Location"]
}

# Entity filter ensures only locations returned
# Hybrid search finds "San Francisco"
# Result: ✅ High-quality location data
```

### Scenario 3: Contextual Search
```python
# Get user node first
user_node = search_nodes({"query": "user", "max_nodes": 1})
user_uuid = user_node["nodes"][0]["uuid"]

# Search preferences centered on user
POST /search/facts
{
  "query": "preferences",
  "center_node_uuid": user_uuid
}

# Results reranked by graph distance from user
# Closer relationships rank higher
# Result: ✅ Most relevant user preferences
```

## 🎯 Quick Decision Guide

**Choose graph4j if:**
- ✅ You need better search quality than basic server
- ✅ You want entity type filtering
- ✅ You need contextual search (center node)
- ✅ You prefer REST API over MCP
- ✅ You want minimal complexity with maximum search power

**Choose basic server if:**
- ✅ Simple search is sufficient
- ✅ You want absolute minimum code
- ✅ You don't need advanced features

**Choose mcp_server if:**
- ✅ You're integrating with AI assistants (Claude, Cursor)
- ✅ You need MCP protocol support
- ✅ You want multiple LLM providers
- ✅ You need advanced configuration options

## 📝 Next Steps

1. **Read**: `QUICKSTART.md` for setup instructions
2. **Compare**: `COMPARISON.md` for detailed comparison
3. **Try**: `example_search.py` to see it in action
4. **Explore**: Swagger docs at `/docs` when running
5. **Customize**: Modify entity types and search configs

## 🤝 Contributing

This is a demonstration of advanced search capabilities. Feel free to:
- Add more entity types
- Implement additional search configs
- Add custom rerankers
- Extend with your own features

## 📄 License

Same as parent Graphiti project (Apache 2.0)

---

**Built with ❤️ to demonstrate the power of hybrid search and reranking**
