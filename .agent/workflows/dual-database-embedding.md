---
description: Dual Neo4j Database Architecture for Dual Embeddings
---

# Dual Neo4j Database Architecture Implementation Plan

## Overview
Implement a dual Neo4j database architecture where fast and quality embeddings are stored in separate databases. This enables true isolation and optimized search performance for each embedding type.

## Architecture

### Current Implementation (Single Database)
- One Neo4j database stores both embeddings
- `node.name_embedding`: quality embeddings
- `node.attributes['name_embedding_fast']`: fast embeddings
- Both embeddings share the same graph structure

### New Implementation (Dual Database)
- **Fast Database**: Stores graph with fast embeddings
- **Quality Database**: Stores graph with quality embeddings
- Each database has identical graph structure (nodes, edges, episodes)
- Each database uses its respective embedding in `name_embedding` field

## Workflow

### 1. Ingestion (Dual Mode)
```
User Request → LLM Extraction (once) → Dual Save
                                        ├─→ Fast DB (with fast embeddings)
                                        └─→ Quality DB (with quality embeddings)
```

**Steps:**
1. Use fast embedder for LLM extraction (speed priority)
2. Save extraction result to Fast Database
3. Generate quality embeddings for the same nodes
4. Save extraction result to Quality Database

### 2. Search/Retrieval
```
Search Request → Check embedding_mode
                 ├─→ "fast": Search Fast DB with fast embedder
                 ├─→ "default": Search Quality DB with quality embedder
                 └─→ "dual": Search both DBs and merge results
```

## Implementation Changes

### 1. Configuration (`config.py`)
Add new settings:
- `neo4j_fast_uri`: URI for fast database
- `neo4j_quality_uri`: URI for quality database (or reuse `neo4j_uri`)

### 2. Client Initialization (`graphiti_client.py`)
Create two separate Graphiti clients:
- `fast_client`: Connected to fast database with fast embedder
- `quality_client`: Connected to quality database with quality embedder

### 3. Dual Embedding Implementation (`dual_embedding_graphiti.py`)
Refactor to implement dual database strategy:
- `add_episode_dual()`: Save to both databases
- `search_dual()`: Search appropriate database based on mode

### 4. Router Updates
- **Ingest Router**: Use dual database save for "dual" mode
- **Search Router**: Route searches to appropriate database

## Benefits
1. **True Isolation**: Each embedding type has its own optimized database
2. **Performance**: No need to swap embeddings or filter attributes
3. **Scalability**: Databases can be scaled independently
4. **Simplicity**: Each database has clean schema with single embedding type

## Migration Path
1. Implement dual database support
2. Keep backward compatibility with single database mode
3. Allow configuration-based selection of architecture
