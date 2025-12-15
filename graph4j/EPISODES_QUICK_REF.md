# Episodes Endpoint - Quick Reference

## ✅ Changes Made

### New Primary Endpoint: `/episodes`

Supports **3 episode types**:
1. **`message`** (default) - Conversation messages
2. **`text`** - Plain text content  
3. **`json`** - Structured JSON data

### Backward Compatibility

The old `/messages` endpoint still works (marked as deprecated).

---

## 🚀 Quick Examples

### 1. Message Type (Default)
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

### 2. Text Type
```bash
curl -X POST "http://localhost:8001/episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "user123",
    "episodes": [
      {
        "content": "User prefers dark roast coffee",
        "episode_type": "text"
      }
    ]
  }'
```

### 3. JSON Type
```bash
curl -X POST "http://localhost:8001/episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "user123",
    "episodes": [
      {
        "content": "{\"preference\": \"dark roast coffee\"}",
        "episode_type": "json"
      }
    ]
  }'
```

### 4. Mixed Types (All in One Request)
```bash
curl -X POST "http://localhost:8001/episodes" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "user123",
    "episodes": [
      {
        "content": "I like coffee",
        "episode_type": "message",
        "role": "user"
      },
      {
        "content": "User likes coffee",
        "episode_type": "text"
      },
      {
        "content": "{\"preference\": \"coffee\"}",
        "episode_type": "json"
      }
    ]
  }'
```

---

## 📋 Episode Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `content` | ✅ Yes | - | The episode content |
| `episode_type` | No | `"message"` | "text", "json", or "message" |
| `name` | No | `null` | Episode name |
| `uuid` | No | auto | Custom UUID |
| `reference_time` | No | now | When it occurred |
| `source_description` | No | `null` | Source info |
| `role` | No | `null` | Speaker role (messages only) |
| `role_type` | No | `null` | Role type (messages only) |

---

## 🔄 How Content is Processed

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

## 📚 Full Documentation

See **`EPISODES_API.md`** for complete documentation with:
- Detailed examples for each type
- Python code examples
- Best practices
- Field reference
- Troubleshooting

---

## 🔧 Code Changes

### New DTOs (`dto.py`)
- `Episode` - New episode model with type support
- `AddEpisodesRequest` - Request model for /episodes endpoint

### Updated Router (`routers/ingest.py`)
- `POST /episodes` - New primary endpoint (supports all 3 types)
- `POST /messages` - Legacy endpoint (deprecated, still works)

### Updated Example (`example_search.py`)
- Now uses `/episodes` with mixed types
- Demonstrates all three episode types

---

## ✨ Benefits

✅ **Flexible** - One endpoint for all episode types  
✅ **Default to messages** - Most common use case is default  
✅ **Backward compatible** - Old `/messages` still works  
✅ **Type-safe** - Proper validation for each type  
✅ **Batch support** - Mix types in one request  
✅ **Well documented** - Complete API guide included
