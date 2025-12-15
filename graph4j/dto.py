from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Message(BaseModel):
    uuid: str | None = Field(None, description="The uuid of the message")
    role: str | None = Field(None, description="The role of the message")
    role_type: str | None = Field(None, description="The role type of the message")
    content: str = Field(..., description="The content of the message")
    name: str | None = Field(None, description="The name of the message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp of the message",
    )
    source_description: str | None = Field(
        None, description="The source description of the message"
    )


class Result(BaseModel):
    message: str
    success: bool


class Episode(BaseModel):
    uuid: str | None = Field(None, description="Optional UUID for the episode")
    name: str | None = Field(None, description="Name of the episode")
    content: str = Field(..., description="The content of the episode")
    episode_type: str = Field(
        default="message",
        description='Type of episode: "text", "json", or "message" (default)',
    )
    reference_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this episode occurred",
    )
    source_description: str | None = Field(
        None, description="Description of the source"
    )
    # Message-specific fields (used when episode_type='message')
    role: str | None = Field(None, description="Role of the speaker (for messages)")
    role_type: str | None = Field(None, description="Type of role (for messages)")


class AddEpisodesRequest(BaseModel):
    group_id: str = Field(..., description="The group id for the episodes")
    episodes: list[Episode] = Field(..., description="The episodes to add")


class SearchQuery(BaseModel):
    group_ids: list[str] | None = Field(
        None, description="The group ids for the memories to search"
    )
    query: str
    max_facts: int = Field(
        default=10, description="The maximum number of facts to retrieve"
    )


class FactResult(BaseModel):
    uuid: str
    name: str
    fact: str
    valid_at: datetime | None
    invalid_at: datetime | None
    created_at: datetime
    expired_at: datetime | None

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class SearchResults(BaseModel):
    facts: list[FactResult]


class GetMemoryRequest(BaseModel):
    group_id: str = Field(..., description="The group id of the memory to get")
    max_facts: int = Field(
        default=10, description="The maximum number of facts to retrieve"
    )
    center_node_uuid: str | None = Field(
        None, description="The uuid of the node to center the retrieval on"
    )
    messages: list[Message] = Field(
        ..., description="The messages to build the retrieval query from "
    )


class GetMemoryResponse(BaseModel):
    facts: list[FactResult] = Field(
        ..., description="The facts that were retrieved from the graph"
    )


# Advanced search DTOs
class NodeSearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    group_ids: list[str] | None = Field(
        None, description="Optional list of group IDs to filter results"
    )
    max_nodes: int = Field(default=10, description="Maximum number of nodes to return")
    entity_types: list[str] | None = Field(
        None,
        description="Optional list of entity type names to filter by (e.g., Preference, Location)",
    )


class NodeResult(BaseModel):
    uuid: str
    name: str
    labels: list[str]
    summary: str | None
    group_id: str
    created_at: str | None
    attributes: dict


class NodeSearchResponse(BaseModel):
    nodes: list[NodeResult]


class FactSearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    group_ids: list[str] | None = Field(
        None, description="Optional list of group IDs to filter results"
    )
    max_facts: int = Field(default=10, description="Maximum number of facts to return")
    center_node_uuid: str | None = Field(
        None,
        description="Optional UUID of a node to center the search around for reranking",
    )


class FactSearchResponse(BaseModel):
    facts: list[FactResult]
