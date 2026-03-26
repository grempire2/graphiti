from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.errors import (
    EdgeNotFoundError,
    GroupsEdgesNotFoundError,
    NodeNotFoundError,
)
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.nodes import EntityNode, EpisodicNode
from openai import AsyncOpenAI

from config import Settings, SettingsDep, get_settings
from dto import FactResult

logger = logging.getLogger(__name__)

DEPENDENCY_NEO4J = 'neo4j'
DEPENDENCY_NEO4J_FAST = 'neo4j_fast'
DEPENDENCY_LLM = 'llm'
DEPENDENCY_QUALITY_EMBEDDER = 'quality_embedder'
DEPENDENCY_FAST_EMBEDDER = 'fast_embedder'

_SEARCH_REQUIREMENTS = {
    'quality': [DEPENDENCY_NEO4J, DEPENDENCY_QUALITY_EMBEDDER],
    'fast': [DEPENDENCY_NEO4J_FAST, DEPENDENCY_FAST_EMBEDDER],
}

_INGEST_REQUIREMENTS = {
    'quality': [DEPENDENCY_NEO4J, DEPENDENCY_QUALITY_EMBEDDER, DEPENDENCY_LLM],
    'fast': [DEPENDENCY_NEO4J_FAST, DEPENDENCY_FAST_EMBEDDER, DEPENDENCY_LLM],
    'dual': [
        DEPENDENCY_NEO4J,
        DEPENDENCY_NEO4J_FAST,
        DEPENDENCY_QUALITY_EMBEDDER,
        DEPENDENCY_FAST_EMBEDDER,
        DEPENDENCY_LLM,
    ],
}


# Global long-lived Graphiti clients
_default_graphiti: Graphiti | None = None
_fast_graphiti: Graphiti | None = None

_readiness_cache: dict[str, Any] | None = None
_readiness_cache_expires_at: float = 0.0
_readiness_lock = asyncio.Lock()


def _invalidate_readiness_cache() -> None:
    global _readiness_cache, _readiness_cache_expires_at
    _readiness_cache = None
    _readiness_cache_expires_at = 0.0


def _build_openai_client(settings: Settings, base_url: str | None) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=base_url,
        timeout=settings.backend_timeout_seconds,
        max_retries=0,
    )


def _target(base_url: str | None, model: str | None = None) -> str:
    base = base_url or '<default>'
    if model:
        return f'{base} [{model}]'
    return base


def _dependency_result(ok: bool, target: str, detail: str) -> dict[str, Any]:
    return {
        'ok': ok,
        'target': target,
        'detail': detail,
    }


async def _probe_dependency(
    *,
    name: str,
    target: str,
    probe: Any,
) -> tuple[str, dict[str, Any]]:
    try:
        await probe()
        return name, _dependency_result(True, target, 'ok')
    except Exception as exc:
        detail = f'{exc.__class__.__name__}: {exc}'
        logger.warning('Graph4j readiness probe failed for %s (%s): %s', name, target, detail)
        return name, _dependency_result(False, target, detail)


def _build_uninitialized_readiness(settings: Settings) -> dict[str, Any]:
    dependencies = {
        DEPENDENCY_NEO4J: _dependency_result(
            False,
            settings.neo4j_uri,
            'Graphiti clients not initialized',
        ),
        DEPENDENCY_NEO4J_FAST: _dependency_result(
            False,
            settings.neo4j_fast_uri or 'bolt://localhost:7787',
            'Graphiti clients not initialized',
        ),
        DEPENDENCY_LLM: _dependency_result(
            False,
            _target(settings.openai_base_url, settings.model_name),
            'Graphiti clients not initialized',
        ),
        DEPENDENCY_QUALITY_EMBEDDER: _dependency_result(
            False,
            _target(settings.embedding_base_url, settings.embedding_model),
            'Graphiti clients not initialized',
        ),
        DEPENDENCY_FAST_EMBEDDER: _dependency_result(
            False,
            _target(settings.fast_base_url, settings.fast_embedding_model),
            'Graphiti clients not initialized',
        ),
    }
    return _build_readiness_report(settings, dependencies)


def _build_readiness_report(
    settings: Settings,
    dependencies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    operations = {
        'search_quality': all(
            dependencies[name]['ok'] for name in _SEARCH_REQUIREMENTS['quality']
        ),
        'search_fast': all(dependencies[name]['ok'] for name in _SEARCH_REQUIREMENTS['fast']),
        'ingest_quality': all(
            dependencies[name]['ok'] for name in _INGEST_REQUIREMENTS['quality']
        ),
        'ingest_fast': all(dependencies[name]['ok'] for name in _INGEST_REQUIREMENTS['fast']),
        'ingest_dual': all(dependencies[name]['ok'] for name in _INGEST_REQUIREMENTS['dual']),
    }
    ready = all(dep['ok'] for dep in dependencies.values())
    return {
        'status': 'ready' if ready else 'degraded',
        'ready': ready,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'readiness_ttl_seconds': settings.readiness_ttl_seconds,
        'dependencies': dependencies,
        'operations': operations,
    }


def _get_requirements(operation: str, embedding_mode: str) -> list[str]:
    if operation == 'search':
        requirements = _SEARCH_REQUIREMENTS
    elif operation == 'ingest':
        requirements = _INGEST_REQUIREMENTS
    else:
        raise ValueError(f'Unsupported readiness operation: {operation}')

    if embedding_mode not in requirements:
        raise ValueError(
            f"Unsupported embedding_mode '{embedding_mode}' for operation '{operation}'"
        )
    return requirements[embedding_mode]


def _summarize_failures(
    report: dict[str, Any],
    required_dependencies: list[str] | None = None,
) -> str:
    names = required_dependencies or list(report['dependencies'].keys())
    failing = [name for name in names if not report['dependencies'][name]['ok']]
    if not failing:
        return 'ok'

    parts = []
    for name in failing:
        dependency = report['dependencies'][name]
        parts.append(f"{name} ({dependency['target']}): {dependency['detail']}")
    return '; '.join(parts)


async def get_readiness_status(
    settings: Settings | None = None,
    *,
    use_cache: bool = True,
) -> dict[str, Any]:
    global _readiness_cache, _readiness_cache_expires_at

    settings = settings or get_settings()
    now = time.monotonic()
    if use_cache and _readiness_cache is not None and now < _readiness_cache_expires_at:
        return _readiness_cache

    async with _readiness_lock:
        now = time.monotonic()
        if use_cache and _readiness_cache is not None and now < _readiness_cache_expires_at:
            return _readiness_cache

        if _default_graphiti is None or _fast_graphiti is None:
            report = _build_uninitialized_readiness(settings)
        else:
            llm_client = _default_graphiti.llm_client
            quality_embedder = _default_graphiti.embedder
            fast_embedder = _fast_graphiti.embedder

            async def probe_neo4j() -> None:
                await _default_graphiti.driver.health_check()

            async def probe_neo4j_fast() -> None:
                await _fast_graphiti.driver.health_check()

            async def probe_llm() -> None:
                model_response = await llm_client.client.models.list()
                configured_model = settings.model_name or llm_client.model
                if not configured_model:
                    return
                available_ids = {entry.id for entry in model_response.data}
                if configured_model not in available_ids:
                    raise RuntimeError(
                        f"configured model '{configured_model}' not returned by backend"
                    )

            async def probe_quality_embedder() -> None:
                await quality_embedder.create(input_data=['graph4j readiness probe'])

            async def probe_fast_embedder() -> None:
                await fast_embedder.create(input_data=['graph4j readiness probe'])

            probe_results = await asyncio.gather(
                _probe_dependency(
                    name=DEPENDENCY_NEO4J,
                    target=settings.neo4j_uri,
                    probe=probe_neo4j,
                ),
                _probe_dependency(
                    name=DEPENDENCY_NEO4J_FAST,
                    target=settings.neo4j_fast_uri or 'bolt://localhost:7787',
                    probe=probe_neo4j_fast,
                ),
                _probe_dependency(
                    name=DEPENDENCY_LLM,
                    target=_target(settings.openai_base_url, settings.model_name),
                    probe=probe_llm,
                ),
                _probe_dependency(
                    name=DEPENDENCY_QUALITY_EMBEDDER,
                    target=_target(settings.embedding_base_url, settings.embedding_model),
                    probe=probe_quality_embedder,
                ),
                _probe_dependency(
                    name=DEPENDENCY_FAST_EMBEDDER,
                    target=_target(settings.fast_base_url, settings.fast_embedding_model),
                    probe=probe_fast_embedder,
                ),
            )
            dependencies = {name: result for name, result in probe_results}
            report = _build_readiness_report(settings, dependencies)

        _readiness_cache = report
        _readiness_cache_expires_at = time.monotonic() + settings.readiness_ttl_seconds
        return report


async def ensure_startup_readiness(settings: Settings) -> dict[str, Any]:
    report = await get_readiness_status(settings, use_cache=False)
    if report['ready']:
        return report

    raise RuntimeError(
        'Graph4j startup readiness failed: '
        + _summarize_failures(report, _INGEST_REQUIREMENTS['dual'])
    )


async def ensure_operation_ready(
    settings: Settings,
    *,
    operation: str,
    embedding_mode: str,
) -> dict[str, Any]:
    try:
        required_dependencies = _get_requirements(operation, embedding_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    report = await get_readiness_status(settings)
    if all(report['dependencies'][name]['ok'] for name in required_dependencies):
        return report

    raise HTTPException(
        status_code=503,
        detail={
            'message': (
                f"Graph4j {operation} backend unavailable for embedding_mode='{embedding_mode}'"
            ),
            'status': report['status'],
            'operation': operation,
            'embedding_mode': embedding_mode,
            'required_dependencies': required_dependencies,
            'dependencies': {
                name: report['dependencies'][name] for name in required_dependencies
            },
        },
    )


# Helper functions for operations used by routers
async def get_entity_edge(graphiti: Graphiti, uuid: str) -> EntityEdge:
    """Get an entity edge by UUID."""
    try:
        edge = await EntityEdge.get_by_uuid(graphiti.driver, uuid)
        return edge
    except EdgeNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e


async def delete_entity_edge(graphiti: Graphiti, uuid: str) -> None:
    """Delete an entity edge by UUID (supports dual databases)."""

    async def _delete(client: Graphiti) -> None:
        try:
            edge = await EntityEdge.get_by_uuid(client.driver, uuid)
            await edge.delete(client.driver)
        except EdgeNotFoundError:
            pass

    await _delete(graphiti)

    if hasattr(graphiti, 'fast_client') and graphiti.fast_client:
        await _delete(graphiti.fast_client)


async def delete_episodic_node(graphiti: Graphiti, uuid: str) -> None:
    """Delete an episodic node by UUID (supports dual databases)."""

    async def _delete(client: Graphiti) -> None:
        try:
            episode = await EpisodicNode.get_by_uuid(client.driver, uuid)
            await episode.delete(client.driver)
        except NodeNotFoundError:
            pass

    await _delete(graphiti)

    if hasattr(graphiti, 'fast_client') and graphiti.fast_client:
        await _delete(graphiti.fast_client)


async def delete_group(graphiti: Graphiti, group_id: str) -> None:
    """Delete all nodes and edges in a group (supports dual databases)."""

    async def _delete(client: Graphiti) -> None:
        try:
            edges = await EntityEdge.get_by_group_ids(client.driver, [group_id])
        except GroupsEdgesNotFoundError:
            edges = []

        nodes = await EntityNode.get_by_group_ids(client.driver, [group_id])
        episodes = await EpisodicNode.get_by_group_ids(client.driver, [group_id])

        for edge in edges:
            await edge.delete(client.driver)
        for node in nodes:
            await node.delete(client.driver)
        for episode in episodes:
            await episode.delete(client.driver)

    await _delete(graphiti)

    if hasattr(graphiti, 'fast_client') and graphiti.fast_client:
        await _delete(graphiti.fast_client)


async def get_graphiti(settings: SettingsDep):
    """Dependency to get long-lived Graphiti client instances for dual database architecture."""
    del settings

    if _default_graphiti is None or _fast_graphiti is None:
        raise RuntimeError(
            'Graphiti clients not initialized. Call initialize_graphiti() during startup.'
        )

    yield _default_graphiti


def get_clients() -> tuple[Graphiti, Graphiti]:
    """Helper for background tasks to get initialized clients."""
    if _default_graphiti is None or _fast_graphiti is None:
        raise RuntimeError('Graphiti clients not initialized')
    return _default_graphiti, _fast_graphiti


async def initialize_graphiti(settings: Settings) -> None:
    """Initialize long-lived Graphiti clients for both databases."""
    global _default_graphiti, _fast_graphiti

    await close_graphiti()
    _invalidate_readiness_cache()

    logger.info('Initializing LLM client with model: %s', settings.model_name)
    llm_openai_client = _build_openai_client(settings, settings.openai_base_url)
    llm_client = OpenAIClient(
        config=LLMConfig(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.model_name,
            small_model=settings.model_name,
        ),
        client=llm_openai_client,
    )

    fast_embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model=settings.fast_embedding_model,
            embedding_dim=settings.embedding_dim,
            api_key=settings.openai_api_key,
            base_url=settings.fast_base_url,
        ),
        client=_build_openai_client(settings, settings.fast_base_url),
    )

    embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model=settings.embedding_model,
            embedding_dim=settings.embedding_dim,
            api_key=settings.openai_api_key,
            base_url=settings.embedding_base_url,
        ),
        client=_build_openai_client(settings, settings.embedding_base_url),
    )

    try:
        _fast_graphiti = Graphiti(
            uri=settings.neo4j_fast_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm_client=llm_client,
            embedder=fast_embedder,
        )

        _default_graphiti = Graphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            llm_client=llm_client,
            embedder=embedder,
        )

        _default_graphiti.fast_client = _fast_graphiti
        _default_graphiti.fast_embedder = fast_embedder

        is_dual_db = settings.neo4j_fast_uri != settings.neo4j_uri

        logger.info(
            'Initialized Graphiti clients (%s mode): fast=%s default=%s',
            'DUAL DATABASE' if is_dual_db else 'SINGLE DATABASE',
            _target(settings.fast_base_url, settings.fast_embedding_model),
            _target(settings.embedding_base_url, settings.embedding_model),
        )

        await ensure_startup_readiness(settings)

        await _default_graphiti.build_indices_and_constraints()
        logger.info(
            'Initialized indices and constraints for default database: %s',
            settings.neo4j_uri,
        )

        if is_dual_db:
            await _fast_graphiti.build_indices_and_constraints()
            logger.info(
                'Initialized indices and constraints for fast database: %s',
                settings.neo4j_fast_uri,
            )

        _invalidate_readiness_cache()
    except Exception:
        await close_graphiti()
        raise


async def close_graphiti() -> None:
    """Close long-lived Graphiti clients."""
    global _default_graphiti, _fast_graphiti

    if _default_graphiti is not None:
        await _default_graphiti.close()
        logger.info('Closed default Graphiti client')

    if _fast_graphiti is not None and _fast_graphiti is not _default_graphiti:
        await _fast_graphiti.close()
        logger.info('Closed fast Graphiti client')

    _default_graphiti = None
    _fast_graphiti = None
    _invalidate_readiness_cache()


def get_fact_result_from_edge(edge: EntityEdge) -> FactResult:
    """Convert EntityEdge to FactResult DTO."""
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
    )


GraphitiDep = Annotated[Graphiti, Depends(get_graphiti)]
