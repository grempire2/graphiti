import asyncio
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI, status
from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

from dto import AddEpisodesRequest, Episode, Result
from graphiti_client import GraphitiDep


class AsyncWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.task = None

    async def worker(self):
        while True:
            try:
                print(f"Got a job: (size of remaining queue: {self.queue.qsize()})")
                job = await self.queue.get()
                await job()
            except asyncio.CancelledError:
                break

    async def start(self):
        self.task = asyncio.create_task(self.worker())

    async def stop(self):
        if self.task:
            self.task.cancel()
            await self.task
        while not self.queue.empty():
            self.queue.get_nowait()


async_worker = AsyncWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await async_worker.start()
    yield
    await async_worker.stop()


router = APIRouter(lifespan=lifespan)


@router.post("/episodes", status_code=status.HTTP_202_ACCEPTED)
async def add_episodes(
    request: AddEpisodesRequest,
    graphiti: GraphitiDep,
):
    """
    Add episodes to the knowledge graph.

    Supports three episode types:
    - 'message': Conversation messages (default) - formatted as "{role}({role_type}): {content}"
    - 'text': Plain text content
    - 'json': Structured JSON data
    """

    async def add_episode_task(ep: Episode):
        # Determine the episode type
        episode_type_map = {
            "text": EpisodeType.text,
            "json": EpisodeType.json,
            "message": EpisodeType.message,
        }

        # Get the episode type, default to message
        ep_type = episode_type_map.get(ep.episode_type.lower(), EpisodeType.message)

        # Format episode body based on type
        if ep_type == EpisodeType.message:
            # For messages, format with role information
            episode_body = f'{ep.role or ""}({ep.role_type or ""}): {ep.content}'
        else:
            # For text and json, use content as-is
            episode_body = ep.content

        await graphiti.add_episode(
            uuid=ep.uuid,
            group_id=request.group_id,
            name=ep.name,
            episode_body=episode_body,
            reference_time=ep.reference_time,
            source=ep_type,
            source_description=ep.source_description,
        )

    for ep in request.episodes:
        await async_worker.queue.put(partial(add_episode_task, ep))

    return Result(message="Episodes added to processing queue", success=True)


@router.delete("/entity-edge/{uuid}", status_code=status.HTTP_200_OK)
async def delete_entity_edge(uuid: str, graphiti: GraphitiDep):
    await graphiti.delete_entity_edge(uuid)
    return Result(message="Entity Edge deleted", success=True)


@router.delete("/group/{group_id}", status_code=status.HTTP_200_OK)
async def delete_group(group_id: str, graphiti: GraphitiDep):
    await graphiti.delete_group(group_id)
    return Result(message="Group deleted", success=True)


@router.delete("/episode/{uuid}", status_code=status.HTTP_200_OK)
async def delete_episode(uuid: str, graphiti: GraphitiDep):
    await graphiti.delete_episodic_node(uuid)
    return Result(message="Episode deleted", success=True)


@router.post("/clear", status_code=status.HTTP_200_OK)
async def clear(
    graphiti: GraphitiDep,
):
    await clear_data(graphiti.driver)
    await graphiti.build_indices_and_constraints()
    return Result(message="Graph cleared", success=True)
