import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from graphiti_core.search.search_utils import DEFAULT_MIN_SCORE
from app.config import EmbedderClientType, LLMClientType


class BasicSearchRequest(BaseModel):
    query: str
    llm_client: LLMClientType | None = None  # default to settings.llm_client
    embedder_client: EmbedderClientType | None = None
    group_ids: list[str] | None = None
    num_results: int = 10


class CenterNodeSearchRequest(BaseModel):
    query: str
    center_node_uuid: str
    llm_client: LLMClientType | None = None
    embedder_client: EmbedderClientType | None = None
    group_ids: list[str] | None = None
    num_results: int = 10


class AdvancedSearchRequest(BaseModel):
    query: str
    llm_client: LLMClientType | None = None
    embedder_client: EmbedderClientType | None = None
    group_ids: list[str] | None = None
    center_node_uuid: str | None = None
    return_limit: int | None = Field(default=None, ge=1)
    reranker_min_score: float | None = Field(default=None)


class AddEpisodeRequest(BaseModel):
    name: str
    episode_body: str
    llm_client: LLMClientType | None = None
    embedder_client: EmbedderClientType | None = None
    source: Literal["text", "json", "message"] = "message"
    source_description: str = ""
    group_id: str | None = None
    uuid: str | None = None
    reference_time: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("episode_body", mode="before")
    @classmethod
    def convert_episode_body(cls, v: Any) -> str:
        """Convert episode_body to string format."""
        if isinstance(v, str):
            return v
        else:
            return json.dumps(v)


class FactResult(BaseModel):
    uuid: str
    name: str
    fact: str
    # valid_at: datetime | None
    # invalid_at: datetime | None
    # created_at: datetime
    # expired_at: datetime | None
    # source_node_uuid: str | None = None
    # target_node_uuid: str | None = None
    episodes: list[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class BasicSearchResponse(BaseModel):
    facts: list[FactResult]


class CenterNodeSearchResponse(BaseModel):
    facts: list[FactResult]


class AdvancedSearchResponse(BaseModel):
    facts: list[FactResult] = Field(default_factory=list)
    edges: list[FactResult] = Field(default_factory=list)
    nodes: list[dict] = Field(default_factory=list)
    episodes: list[dict] = Field(default_factory=list)
    communities: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AddEpisodeResponse(BaseModel):
    message: str
    success: bool
    episode_uuid: str | None = None


class DeleteEmbeddingsRequest(BaseModel):
    created_before: datetime = Field(
        description="Delete embeddings (nodes and edges) created before this date"
    )
    database: str | None = Field(
        default="neo4j", description="Neo4j database name to delete from"
    )
    delete_nodes: bool = Field(
        default=True, description="Whether to delete nodes with embeddings"
    )
    delete_edges: bool = Field(
        default=True, description="Whether to delete edges with embeddings"
    )


class DeleteEmbeddingsResponse(BaseModel):
    message: str
    success: bool
    nodes_deleted: int = 0
    edges_deleted: int = 0


def fact_result_from_edge(edge):
    """Convert an EntityEdge to a FactResult."""
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        # valid_at=edge.valid_at,
        # invalid_at=edge.invalid_at,
        # created_at=edge.created_at,
        # expired_at=edge.expired_at,
        # source_node_uuid=edge.source_node_uuid,
        # target_node_uuid=edge.target_node_uuid,
        episodes=edge.episodes if hasattr(edge, "episodes") else [],
    )


def node_to_dict(node):
    """Convert an EntityNode to a dictionary."""
    return {
        "uuid": node.uuid,
        "name": node.name,
        "summary": node.summary,
        "labels": node.labels,
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "attributes": node.attributes if hasattr(node, "attributes") else {},
    }


def episode_to_dict(episode):
    """Convert an EpisodicNode to a dictionary."""
    return {
        "uuid": episode.uuid,
        "name": episode.name,
        "content": episode.content if hasattr(episode, "content") else None,
        "created_at": episode.created_at.isoformat() if episode.created_at else None,
        "group_id": episode.group_id if hasattr(episode, "group_id") else None,
        "source": (
            episode.source.value
            if hasattr(episode, "source") and episode.source
            else None
        ),
        "source_description": (
            episode.source_description
            if hasattr(episode, "source_description")
            else None
        ),
    }


def community_to_dict(community):
    """Convert a CommunityNode to a dictionary."""
    return {
        "uuid": community.uuid,
        "name": community.name,
        "summary": community.summary if hasattr(community, "summary") else None,
        "created_at": (
            community.created_at.isoformat() if community.created_at else None
        ),
    }
