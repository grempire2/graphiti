from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from graphiti_core.driver.neo4j_driver import Neo4jDriver

from app.config import get_settings
from app.routers import episodes, search


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize Neo4j database indices and constraints on startup."""
    settings = get_settings()
    # Initialize the Neo4j database schema (indices and constraints)
    # This only requires the database driver, not a full Graphiti client
    driver = Neo4jDriver(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await driver.build_indices_and_constraints()
    await driver.close()
    yield


app = FastAPI(
    title="Neo4j Graphiti Server",
    description="FastAPI server for Graphiti with Neo4j backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(episodes.router, prefix="/api/v1", tags=["episodes"])


@app.get("/healthcheck")
async def healthcheck():
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy"}, status_code=200)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Neo4j Graphiti Server",
        "version": "0.1.0",
        "endpoints": {
            "add_episode": "/api/v1/episodes",
            "basic_search": "/api/v1/search/basic",
            "center_node_search": "/api/v1/search/center",
            "advanced_search": "/api/v1/search/advanced",
        },
    }
