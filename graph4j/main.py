"""
Graph4j - Advanced Graphiti FastAPI Server

This is an advanced FastAPI server for Graphiti with hybrid search capabilities.
Unlike the basic server, Graph4j implements:

- Hybrid Search: BM25 (keyword) + Cosine Similarity (semantic)
- RRF Reranking: Reciprocal Rank Fusion for better result quality
- Node Search: Search for entity nodes with entity type filtering
- Fact Search: Search for edges/relationships with center node reranking
- No MCP Overhead: Direct FastAPI endpoints without MCP protocol

Key Features:
- POST /search - Main fact search with hybrid search and structural filters
- POST /episodes - Ingest conversation history or episodes
- Entity type filtering via structural filters
- Graph-distance-based reranking for contextual relevance
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import get_settings
from routers.ingest import async_worker
from graphiti_client import initialize_graphiti, close_graphiti
from routers import ingest_router, search_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize Graphiti and background worker on startup, close on shutdown."""
    settings = get_settings()
    await initialize_graphiti(settings)

    # Start the background ingestion worker
    await async_worker.start()

    yield

    # Stop the worker first to finish pending jobs
    await async_worker.stop()
    await close_graphiti()


app = FastAPI(
    title="Graph4j - Advanced Graphiti Server",
    description="""
    Advanced Graphiti FastAPI server with hybrid search and reranking capabilities.
    
    ## Features
    
    - **Hybrid Search**: Combines BM25 (keyword) and Cosine Similarity (semantic) search
    - **RRF Reranking**: Reciprocal Rank Fusion for optimal result quality
    - **Node Search**: Search entity nodes with entity type filtering
    - **Fact Search**: Search relationships with center node reranking
    - **No MCP Overhead**: Direct REST API without MCP protocol complexity
    
    ## Search Endpoints
    
    - `POST /search` - Main fact search with hybrid search and optional structural filters
    
    ## Ingestion Endpoints
    
    - `POST /episodes` - Add episodes to the knowledge graph
    
    ## Legacy Endpoints
    
    - `POST /search` - Basic search (for backward compatibility)
    - `POST /entity-node` - Add entity nodes
    - `DELETE /entity-edge/{uuid}` - Delete edges
    - `DELETE /episode/{uuid}` - Delete episodes
    - `DELETE /group/{group_id}` - Delete groups
    - `POST /clear` - Clear graph data
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# Include routers
app.include_router(search_router, tags=["Search"])
app.include_router(ingest_router, tags=["Ingest"])


@app.get("/health")
async def healthcheck():
    """Health check endpoint."""
    return JSONResponse(
        content={"status": "healthy", "service": "graph4j"}, status_code=200
    )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Graph4j - Advanced Graphiti Server",
        "version": "1.0.0",
        "features": [
            "Hybrid Search (BM25 + Cosine Similarity)",
            "RRF Reranking",
            "Node Search with Entity Type Filtering",
            "Fact Search with Center Node Reranking",
        ],
        "docs": "/docs",
        "redoc": "/redoc",
    }
