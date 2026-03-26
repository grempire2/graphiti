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
- GET /health - Liveness check
- GET /ready - Operational readiness check for search/ingestion backends
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import get_settings
from graphiti_client import close_graphiti, get_readiness_status, initialize_graphiti
from routers import ingest_router, search_router
from routers.ingest import async_worker


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        """Initialize Graphiti and background worker on startup, close on shutdown."""
        settings = get_settings()
        await initialize_graphiti(settings)
        await async_worker.start()

        yield

        await async_worker.stop()
        await close_graphiti()

    app = FastAPI(
        title='Graph4j - Advanced Graphiti Server',
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

        ## Operational Endpoints

        - `GET /health` - Liveness only
        - `GET /ready` - Backend readiness for search and ingestion
        """,
        version='1.0.0',
        lifespan=lifespan,
    )

    app.include_router(search_router, tags=['Search'])
    app.include_router(ingest_router, tags=['Ingest'])

    @app.get('/health')
    async def healthcheck():
        """Liveness check endpoint."""
        return JSONResponse(
            content={'status': 'healthy', 'service': 'graph4j'},
            status_code=200,
        )

    @app.get('/ready')
    async def readycheck():
        """Operational readiness endpoint for Neo4j and inference backends."""
        report = await get_readiness_status(get_settings())
        status_code = 200 if report['ready'] else 503
        return JSONResponse(content=report, status_code=status_code)

    @app.get('/')
    async def root():
        """Root endpoint with service information."""
        return {
            'service': 'Graph4j - Advanced Graphiti Server',
            'version': '1.0.0',
            'features': [
                'Hybrid Search (BM25 + Cosine Similarity)',
                'RRF Reranking',
                'Node Search with Entity Type Filtering',
                'Fact Search with Center Node Reranking',
            ],
            'docs': '/docs',
            'redoc': '/redoc',
        }

    return app


app = create_app()
