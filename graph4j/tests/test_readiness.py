from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import config
import main
from graphiti_client import get_graphiti
from routers import ingest as ingest_router_module
from routers import search as search_router_module


def build_settings() -> config.Settings:
    return config.Settings(
        openai_api_key='ollama',
        openai_base_url='http://100.76.6.21:11434/v1',
        model_name='qwen3.5:latest',
        embedding_base_url='http://100.76.6.21:11434/v1',
        embedding_model='qwen3-embedding:8b-q8_0',
        fast_base_url='http://100.76.6.21:11434/v1',
        fast_embedding_model='qwen3-embedding:8b-q8_0',
        neo4j_uri='bolt://localhost:7687',
        neo4j_user='neo4j',
        neo4j_password='password',
        neo4j_fast_uri='bolt://localhost:7787',
    )


def patch_clean_lifespan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, 'get_settings', build_settings)
    monkeypatch.setattr(main, 'initialize_graphiti', AsyncMock())
    monkeypatch.setattr(main, 'close_graphiti', AsyncMock())
    monkeypatch.setattr(main.async_worker, 'start', AsyncMock())
    monkeypatch.setattr(main.async_worker, 'stop', AsyncMock())


async def fake_graphiti_dep():
    yield SimpleNamespace(fast_client=object())


def test_app_startup_succeeds_when_graphiti_is_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_clean_lifespan(monkeypatch)
    app = main.create_app()

    with TestClient(app) as client:
        response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'healthy', 'service': 'graph4j'}


def test_app_startup_failure_surfaces_embedder_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    timeout_error = RuntimeError(
        'Graph4j startup readiness failed: '
        'quality_embedder (http://100.76.6.21:11434/v1 [qwen3-embedding:8b-q8_0]): '
        'APITimeoutError: Request timed out.'
    )
    monkeypatch.setattr(main, 'get_settings', build_settings)
    monkeypatch.setattr(main, 'initialize_graphiti', AsyncMock(side_effect=timeout_error))
    monkeypatch.setattr(main.async_worker, 'start', AsyncMock())

    app = main.create_app()

    with pytest.raises(RuntimeError, match='startup readiness failed'):
        with TestClient(app):
            pass


def test_ready_endpoint_reports_degraded_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_clean_lifespan(monkeypatch)
    monkeypatch.setattr(
        main,
        'get_readiness_status',
        AsyncMock(
            return_value={
                'status': 'degraded',
                'ready': False,
                'checked_at': '2026-03-25T00:00:00+00:00',
                'readiness_ttl_seconds': 5.0,
                'dependencies': {
                    'quality_embedder': {
                        'ok': False,
                        'target': 'http://100.76.6.21:11434/v1 [qwen3-embedding:8b-q8_0]',
                        'detail': 'APITimeoutError: Request timed out.',
                    }
                },
                'operations': {
                    'search_quality': False,
                    'search_fast': True,
                    'ingest_quality': False,
                    'ingest_fast': True,
                    'ingest_dual': False,
                },
            }
        ),
    )

    app = main.create_app()

    with TestClient(app) as client:
        response = client.get('/ready')

    assert response.status_code == 503
    payload = response.json()
    assert payload['ready'] is False
    assert payload['status'] == 'degraded'


def test_search_returns_503_when_backend_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_clean_lifespan(monkeypatch)
    search_helper = AsyncMock()
    monkeypatch.setattr(
        search_router_module,
        'ensure_operation_ready',
        AsyncMock(
            side_effect=HTTPException(
                status_code=503,
                detail={'message': 'Graph4j search backend unavailable'},
            )
        ),
    )
    monkeypatch.setattr(search_router_module, 'search_helper', search_helper)

    app = main.create_app()
    app.dependency_overrides[config.get_settings] = build_settings
    app.dependency_overrides[get_graphiti] = fake_graphiti_dep

    with TestClient(app) as client:
        response = client.post(
            '/search',
            json={
                'query': 'test connectivity',
                'group_ids': ['companion'],
                'max_facts': 1,
                'embedding_mode': 'quality',
            },
        )

    assert response.status_code == 503
    assert response.json()['detail']['message'] == 'Graph4j search backend unavailable'
    search_helper.assert_not_awaited()


def test_add_episodes_refuses_to_enqueue_when_dependencies_are_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_clean_lifespan(monkeypatch)
    put_mock = AsyncMock()
    monkeypatch.setattr(
        ingest_router_module,
        'ensure_operation_ready',
        AsyncMock(
            side_effect=HTTPException(
                status_code=503,
                detail={'message': 'Graph4j ingest backend unavailable'},
            )
        ),
    )
    monkeypatch.setattr(
        ingest_router_module.async_worker,
        'queue',
        SimpleNamespace(
            put=put_mock,
            qsize=lambda: 0,
            empty=lambda: True,
            get_nowait=lambda: None,
        ),
    )

    app = main.create_app()
    app.dependency_overrides[config.get_settings] = build_settings
    app.dependency_overrides[get_graphiti] = fake_graphiti_dep

    with TestClient(app) as client:
        response = client.post(
            '/episodes',
            json={
                'group_id': 'companion',
                'embedding_mode': 'dual',
                'episodes': [
                    {
                        'name': 'conversation_turn_user',
                        'content': 'hello there',
                        'episode_type': 'message',
                        'role': 'user',
                        'source_description': 'test',
                    }
                ],
            },
        )

    assert response.status_code == 503
    assert response.json()['detail']['message'] == 'Graph4j ingest backend unavailable'
    put_mock.assert_not_awaited()
