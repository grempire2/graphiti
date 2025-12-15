# Episodes API Guide

## Overview

The `/episodes` endpoint supports adding three types of episodes to the knowledge graph:
- **message** (default): Conversation messages
- **text**: Plain text content
- **json**: Structured JSON data

## Endpoint

```
POST /episodes
```

## Request Format

```json
{
  "group_id": "user123",
  "episodes": [
    {
      "content": "Your content here",
      "episode_type": "message",  // Optional: "text", "json", or "message" (default)
      "name": "Episode Name",     // Optional
      "uuid": "custom-uuid",      // Optional
      "reference_time": "2024-01-01T10:00:00Z",  // Optional
      "source_description": "source info",  // Optional
      "role": "user",             // Optional: for messages
      "role_type": "human"        // Optional: for messages
    }
  ]
}
```

---

## Episode Type 1: Messages (Default)

For conversation messages. Automatically formats as `"{role}({role_type}): {content}"`.

### Example Request
```json
{
  "group_id": "user123",
  "episodes": [
    {
      "content": "I prefer dark roast coffee in the morning",
      "episode_type": "message",
      "role": "user",
      "role_type": "human"
    }
  ]
}
```

### Minimal (episode_type defaults to "message")
```json
{
  "group_id": "user123",
  "episodes": [
    {
      "content": "I prefer dark roast coffee"
    }
  ]
}
```

### curl Example
```bash
curl -X POST "http://localhost:8001/episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "user123",
    "episodes": [
      {
        "content": "I prefer dark roast coffee",
        "role": "user",
        "role_type": "human"
      }
    ]
  }'
```

---

## Episode Type 2: Text

For plain text content. Content is used as-is without formatting.

### Example Request
```json
{
  "group_id": "user123",
  "episodes": [
    {
      "content": "The user prefers dark roast coffee in the morning",
      "episode_type": "text",
      "name": "Coffee Preference",
      "source_description": "user profile"
    }
  ]
}
```

### curl Example
```bash
curl -X POST "http://localhost:8001/episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "user123",
    "episodes": [
      {
        "content": "The user prefers dark roast coffee",
        "episode_type": "text",
        "name": "Coffee Preference"
      }
    ]
  }'
```

---

## Episode Type 3: JSON

For structured JSON data. Content should be a JSON string.

### Example Request
```json
{
  "group_id": "user123",
  "episodes": [
    {
      "content": "{\"preference\": \"dark roast coffee\", \"time\": \"morning\", \"strength\": \"strong\"}",
      "episode_type": "json",
      "name": "User Preferences",
      "source_description": "CRM data"
    }
  ]
}
```

### curl Example
```bash
curl -X POST "http://localhost:8001/episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "user123",
    "episodes": [
      {
        "content": "{\"preference\": \"dark roast coffee\", \"time\": \"morning\"}",
        "episode_type": "json",
        "name": "User Preferences"
      }
    ]
  }'
```

---

## Batch Processing

You can add multiple episodes of different types in one request:

```json
{
  "group_id": "user123",
  "episodes": [
    {
      "content": "I prefer dark roast coffee",
      "episode_type": "message",
      "role": "user",
      "role_type": "human"
    },
    {
      "content": "User lives in San Francisco",
      "episode_type": "text",
      "name": "Location Info"
    },
    {
      "content": "{\"city\": \"San Francisco\", \"state\": \"CA\"}",
      "episode_type": "json",
      "name": "Location Data"
    }
  ]
}
```

---

## Python Examples

### Example 1: Add Message Episode (Default)
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8001/episodes",
        json={
            "group_id": "user123",
            "episodes": [
                {
                    "content": "I prefer dark roast coffee",
                    "role": "user",
                    "role_type": "human"
                }
            ]
        }
    )
    print(response.json())
```

### Example 2: Add Text Episode
```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8001/episodes",
        json={
            "group_id": "user123",
            "episodes": [
                {
                    "content": "User prefers dark roast coffee in the morning",
                    "episode_type": "text",
                    "name": "Coffee Preference"
                }
            ]
        }
    )
    print(response.json())
```

### Example 3: Add JSON Episode
```python
import json

async with httpx.AsyncClient() as client:
    preference_data = {
        "beverage": "coffee",
        "roast": "dark",
        "time": "morning"
    }
    
    response = await client.post(
        "http://localhost:8001/episodes",
        json={
            "group_id": "user123",
            "episodes": [
                {
                    "content": json.dumps(preference_data),
                    "episode_type": "json",
                    "name": "Preference Data"
                }
            ]
        }
    )
    print(response.json())
```

### Example 4: Mixed Types in Batch
```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8001/episodes",
        json={
            "group_id": "user123",
            "episodes": [
                {
                    "content": "I prefer dark roast coffee",
                    "episode_type": "message",
                    "role": "user"
                },
                {
                    "content": "User lives in San Francisco",
                    "episode_type": "text"
                },
                {
                    "content": '{"city": "San Francisco"}',
                    "episode_type": "json"
                }
            ]
        }
    )
    print(response.json())
```

---

## Response

All requests return:
```json
{
  "message": "Episodes added to processing queue",
  "success": true
}
```

---

## Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | ✅ Yes | - | The episode content |
| `episode_type` | string | ❌ No | `"message"` | Type: "text", "json", or "message" |
| `name` | string | ❌ No | `null` | Name of the episode |
| `uuid` | string | ❌ No | auto-generated | Custom UUID |
| `reference_time` | datetime | ❌ No | current time | When episode occurred |
| `source_description` | string | ❌ No | `null` | Source information |
| `role` | string | ❌ No | `null` | Speaker role (for messages) |
| `role_type` | string | ❌ No | `null` | Type of role (for messages) |

---

## How Content is Processed

### Message Type
```
Input:  content="I like coffee", role="user", role_type="human"
Stored: "user(human): I like coffee"
```

### Text Type
```
Input:  content="User likes coffee"
Stored: "User likes coffee"
```

### JSON Type
```
Input:  content='{"preference": "coffee"}'
Stored: '{"preference": "coffee"}'
```

---

## Best Practices

### 1. Choose the Right Type

**Use `message`** for:
- Conversation data
- Chat logs
- User-assistant interactions

**Use `text`** for:
- Documents
- Notes
- Descriptions
- Summaries

**Use `json`** for:
- Structured data
- API responses
- Database records
- Configuration data

### 2. Provide Context

```python
# Good - includes context
{
  "content": "User prefers dark roast coffee in the morning",
  "episode_type": "text",
  "name": "Coffee Preference",
  "source_description": "user profile survey"
}

# Less ideal - vague
{
  "content": "likes coffee"
}
```

### 3. Use Timestamps

```python
{
  "content": "User visited San Francisco",
  "reference_time": "2024-01-15T10:00:00Z",  # When it happened
  "episode_type": "text"
}
```

### 4. Batch When Possible

```python
# Efficient - one request
{
  "episodes": [ep1, ep2, ep3]
}

# Less efficient - multiple requests
# POST ep1
# POST ep2
# POST ep3
```

---

## Complete Example

```python
import asyncio
import httpx
from datetime import datetime, timezone

async def add_user_data():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/episodes",
            json={
                "group_id": "user_12345",
                "episodes": [
                    # Message type
                    {
                        "content": "I prefer dark roast coffee in the morning",
                        "episode_type": "message",
                        "role": "user",
                        "role_type": "human",
                        "name": "Coffee Preference",
                        "reference_time": datetime.now(timezone.utc).isoformat()
                    },
                    # Text type
                    {
                        "content": "User is a software engineer based in San Francisco",
                        "episode_type": "text",
                        "name": "User Profile",
                        "source_description": "onboarding survey"
                    },
                    # JSON type
                    {
                        "content": '{"occupation": "software engineer", "location": "San Francisco", "interests": ["coffee", "coding"]}',
                        "episode_type": "json",
                        "name": "User Metadata",
                        "source_description": "CRM system"
                    }
                ]
            }
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Search for what was added
        search_response = await client.post(
            "http://localhost:8001/search/nodes",
            json={
                "query": "user preferences and profile",
                "group_ids": ["user_12345"],
                "max_nodes": 10
            }
        )
        
        print(f"\nSearch Results: {search_response.json()}")

asyncio.run(add_user_data())
```

---

## Summary

✅ **New `/episodes` endpoint** supports all three types  
✅ **Default type is `message`** for convenience  
✅ **Backward compatible** - `/messages` still works  
✅ **Flexible** - mix types in one request  
✅ **Async processing** - returns immediately  
✅ **Queue-based** - handles batches efficiently
