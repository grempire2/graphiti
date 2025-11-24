import logging
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from graphiti_core.driver.neo4j_driver import Neo4jDriver

from app.config import SettingsDep
from app.dto import DeleteEmbeddingsRequest, DeleteEmbeddingsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.delete("/embeddings", status_code=status.HTTP_200_OK)
async def delete_embeddings(
    request: DeleteEmbeddingsRequest, settings: SettingsDep
):
    """
    Delete embeddings (nodes and edges) created before a specified date.

    This endpoint deletes Entity nodes and RELATES_TO edges that have embeddings
    and were created before the specified date. The deletion is performed in the
    specified Neo4j database.
    """
    driver = None
    try:
        # Create Neo4j driver with specified database
        driver = Neo4jDriver(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=request.database or "neo4j",
        )

        nodes_deleted = 0
        edges_deleted = 0

        # Ensure datetime is timezone-aware (Neo4j expects datetime objects)
        from graphiti_core.utils.datetime_utils import ensure_utc

        created_before = ensure_utc(request.created_before)

        async with driver.session() as session:
            # Delete edges with embeddings created before the date
            if request.delete_edges:
                # First, count the edges to be deleted
                count_result = await session.run(
                    """
                    MATCH ()-[e:RELATES_TO]->()
                    WHERE e.created_at < $created_before
                      AND e.fact_embedding IS NOT NULL
                    RETURN count(e) AS edge_count
                    """,
                    created_before=created_before,
                )
                count_record = await count_result.single()
                edges_deleted = count_record["edge_count"] if count_record else 0

                # Then delete them
                if edges_deleted > 0:
                    delete_result = await session.run(
                        """
                        MATCH ()-[e:RELATES_TO]->()
                        WHERE e.created_at < $created_before
                          AND e.fact_embedding IS NOT NULL
                        DETACH DELETE e
                        """,
                        created_before=created_before,
                    )
                    # Consume the result to ensure the transaction completes
                    await delete_result.consume()
                logger.info(f"Deleted {edges_deleted} edges with embeddings")

            # Delete nodes with embeddings created before the date
            if request.delete_nodes:
                # First, count the nodes to be deleted
                count_result = await session.run(
                    """
                    MATCH (n:Entity)
                    WHERE n.created_at < $created_before
                      AND n.name_embedding IS NOT NULL
                    RETURN count(n) AS node_count
                    """,
                    created_before=created_before,
                )
                count_record = await count_result.single()
                nodes_deleted = count_record["node_count"] if count_record else 0

                # Then delete them
                if nodes_deleted > 0:
                    delete_result = await session.run(
                        """
                        MATCH (n:Entity)
                        WHERE n.created_at < $created_before
                          AND n.name_embedding IS NOT NULL
                        DETACH DELETE n
                        """,
                        created_before=created_before,
                    )
                    # Consume the result to ensure the transaction completes
                    await delete_result.consume()
                logger.info(f"Deleted {nodes_deleted} nodes with embeddings")

        return DeleteEmbeddingsResponse(
            message=f"Successfully deleted embeddings created before {request.created_before}",
            success=True,
            nodes_deleted=nodes_deleted,
            edges_deleted=edges_deleted,
        )

    except Exception as e:
        logger.exception("Error deleting embeddings")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": f"Error deleting embeddings: {str(e)}",
                "success": False,
                "nodes_deleted": 0,
                "edges_deleted": 0,
            },
        )
    finally:
        if driver:
            await driver.close()

