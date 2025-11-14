import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class BasicSearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    llm_client: Literal["groq", "gemini", "ollama"] = Field(
        default="groq", description="LLM client to use"
    )
    embedder_client: Literal["gemini", "ollama"] = Field(
        default="gemini", description="Embedder client to use"
    )
    group_ids: list[str] | None = Field(
        None, description="Optional list of group IDs to filter results"
    )
    num_results: int = Field(
        default=10, description="Maximum number of results to return"
    )


class CenterNodeSearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    center_node_uuid: str = Field(
        ..., description="UUID of the center node for reranking"
    )
    llm_client: Literal["groq", "gemini", "ollama"] = Field(
        default="groq", description="LLM client to use"
    )
    embedder_client: Literal["gemini", "ollama"] = Field(
        default="gemini", description="Embedder client to use"
    )
    group_ids: list[str] | None = Field(
        None, description="Optional list of group IDs to filter results"
    )
    num_results: int = Field(
        default=10, description="Maximum number of results to return"
    )


class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    llm_client: Literal["groq", "gemini", "ollama"] = Field(
        default="groq", description="LLM client to use"
    )
    embedder_client: Literal["gemini", "ollama"] = Field(
        default="gemini", description="Embedder client to use"
    )
    group_ids: list[str] | None = Field(
        None, description="Optional list of group IDs to filter results"
    )
    center_node_uuid: str | None = Field(
        None, description="Optional UUID of the center node for reranking"
    )
    limit: int = Field(default=10, description="Maximum number of results to return")


class AddEpisodeRequest(BaseModel):
    name: str = Field(..., description="Name of the episode")
    episode_body: str = Field(
        ..., description="Content of the episode (text or JSON string)"
    )
    llm_client: Literal["groq", "gemini", "ollama"] = Field(
        default="groq", description="LLM client to use"
    )
    embedder_client: Literal["gemini", "ollama"] = Field(
        default="gemini", description="Embedder client to use"
    )
    source: Literal["text", "json", "message"] = Field(
        default="text", description="Type of episode source"
    )
    source_description: str = Field(
        default="", description="Description of the episode source"
    )
    group_id: str | None = Field(None, description="Optional group ID for the episode")
    uuid: str | None = Field(None, description="Optional UUID for the episode")
    reference_time: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Reference time for the episode",
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
    valid_at: datetime | None
    invalid_at: datetime | None
    created_at: datetime
    expired_at: datetime | None
    source_node_uuid: str | None = None
    target_node_uuid: str | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class BasicSearchResponse(BaseModel):
    facts: list[FactResult] = Field(..., description="List of facts (edges) found")


class CenterNodeSearchResponse(BaseModel):
    facts: list[FactResult] = Field(..., description="List of facts (edges) found")


class AdvancedSearchResponse(BaseModel):
    edges: list[FactResult] = Field(
        default_factory=list, description="List of edges found"
    )
    nodes: list[dict] = Field(default_factory=list, description="List of nodes found")
    episodes: list[dict] = Field(
        default_factory=list, description="List of episodes found"
    )
    communities: list[dict] = Field(
        default_factory=list, description="List of communities found"
    )


class AddEpisodeResponse(BaseModel):
    message: str
    success: bool
    episode_uuid: str | None = None


def fact_result_from_edge(edge):
    """Convert an EntityEdge to a FactResult."""
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
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
