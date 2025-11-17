import logging
from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from graphiti_core.nodes import EpisodeType

from app.config import SettingsDep
from app.dto import AddEpisodeRequest, AddEpisodeResponse
from app.graphiti_client import create_graphiti_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/episodes", status_code=status.HTTP_201_CREATED)
async def add_episode(request: AddEpisodeRequest, settings: SettingsDep):
    """
    Add an episode to the graph using graphiti.add_episode().

    Episodes are the primary units of information in Graphiti. They can be
    text or structured JSON and are automatically processed to extract entities
    and relationships.
    """
    graphiti = None
    try:
        graphiti = create_graphiti_client(
            settings, request.llm_client, request.embedder_client
        )
        # Convert source string to EpisodeType enum
        source_type = EpisodeType.text
        if request.source == "json":
            source_type = EpisodeType.json
        elif request.source == "message":
            source_type = EpisodeType.message

        # Use provided reference_time or default to now
        ref_time = request.reference_time or datetime.now(timezone.utc)

        result = await graphiti.add_episode(
            name=request.name,
            episode_body=request.episode_body,
            source=source_type,
            source_description=request.source_description,
            group_id=request.group_id,
            uuid=request.uuid,
            reference_time=ref_time,
        )

        # Log diagnostic information about what was created
        logger.info(
            f"Episode '{request.name}' added: "
            f"nodes={len(result.nodes)}, "
            f"edges={len(result.edges)}, "
            f"episodic_edges={len(result.episodic_edges)}"
        )

        if len(result.edges) == 0 and len(result.nodes) > 0:
            logger.warning(
                f"No edges were created for episode '{request.name}' "
                f"despite {len(result.nodes)} nodes being extracted. "
                f"This may indicate an issue with edge extraction."
            )

        return AddEpisodeResponse(
            message=f"Episode '{request.name}' added successfully",
            success=True,
            episode_uuid=result.episode.uuid if result.episode.uuid else request.uuid,
        )
    except Exception as e:
        logger.exception("Error adding episode")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": f"Error adding episode: {str(e)}",
                "success": False,
                "episode_uuid": None,
            },
        )
    finally:
        if graphiti:
            await graphiti.close()
