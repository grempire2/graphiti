# n8n Example Messages for Neo4j Graphiti Server

This document provides example JSON payloads for sending conversations to the Neo4j Graphiti server using n8n.

## Endpoint

**POST** `http://localhost:18888/api/v1/episodes`

## Basic Conversation Example

### Single Message

**Without timestamp (uses current time):**
```json
{
  "name": "User Conversation - 2024-01-15",
  "episode_body": "user: Hello, I'm interested in learning about Python programming.",
  "source_description": "n8n conversation",
  "llm_client": "groq",
  "embedder_client": "gemini"
}
```

**With historical timestamp:**
```json
{
  "name": "User Conversation - 2024-01-15",
  "episode_body": "user: Hello, I'm interested in learning about Python programming.",
  "source_description": "n8n conversation",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "reference_time": "2024-01-15T10:30:00Z"
}
```

### Multi-Turn Conversation (Single Episode)

**Without timestamp (uses current time):**
```json
{
  "name": "Support Chat - Session 12345",
  "episode_body": "user: I'm having trouble with my account\nassistant: I'd be happy to help! What specific issue are you experiencing?\nuser: I can't log in with my password\nassistant: Let me help you reset your password. Can you provide your email address?",
  "source_description": "n8n support conversation",
  "llm_client": "groq",
  "embedder_client": "gemini"
}
```

**With historical timestamp:**
```json
{
  "name": "Support Chat - Session 12345",
  "episode_body": "user: I'm having trouble with my account\nassistant: I'd be happy to help! What specific issue are you experiencing?\nuser: I can't log in with my password\nassistant: Let me help you reset your password. Can you provide your email address?",
  "source_description": "n8n support conversation",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "reference_time": "2024-01-15T14:30:00Z"
}
```

### Conversation with Named Roles
    
```json
{
  "name": "Team Discussion - Project Planning",
  "episode_body": "Alice (project_manager): We need to finalize the sprint goals by Friday.\nBob (developer): I can have the authentication module ready by then.\nAlice (project_manager): Great! What about the database migration?\nCharlie (developer): That's scheduled for Thursday afternoon.",
  "source_description": "n8n team chat",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "project-alpha-2024"
}
```

## Multi-Party Conversations

Graphiti supports conversations with **any number of participants**, not just user/assistant pairs. You can use:
- Simple names: `"Alice: ..."`, `"Bob: ..."`
- Names with roles: `"Alice (manager): ..."`, `"Bob (developer): ..."`
- Role-only identifiers: `"customer: ..."`, `"agent: ..."`, `"moderator: ..."`

### Three-Party Conversation

```json
{
  "name": "Product Meeting - Q1 Planning",
  "episode_body": "Sarah (Product Manager): Let's discuss the roadmap for Q1.\nMike (Engineer): We can deliver the API improvements by February.\nLisa (Designer): I'll have the UI mockups ready next week.\nSarah (Product Manager): Perfect! Mike, can you review Lisa's designs?\nMike (Engineer): Absolutely, I'll sync with Lisa tomorrow.\nLisa (Designer): Great, I'll send them over this afternoon.",
  "source_description": "n8n meeting transcript",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "q1-planning-2024"
}
```

### Four-Party Conversation (Podcast/Interview Style)

```json
{
  "name": "Tech Podcast - Episode 42",
  "episode_body": "Host: Welcome to today's show! We have three amazing guests.\nGuest1: Thanks for having us!\nGuest2: Excited to be here.\nGuest3: Looking forward to the discussion.\nHost: Let's start with AI trends. Guest1, what's your take?\nGuest1: I think we're seeing a shift toward more specialized models.\nGuest2: I agree, but I also see consolidation happening.\nGuest3: From my perspective, the real innovation is in the infrastructure layer.\nHost: Interesting points from all of you. Let's dive deeper...",
  "source_description": "n8n podcast transcript",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "podcast-ep42"
}
```

### Group Chat with Multiple Participants

```json
{
  "name": "Slack Channel - Engineering Team",
  "episode_body": "Alex: Has anyone tested the new deployment?\nJordan: I ran it through staging, looks good.\nSam: I'm seeing some latency issues in the logs.\nAlex: Can you share the log snippet?\nSam: Sure, here's the error...\nJordan: That looks like a database connection pool issue.\nTaylor: I can help debug that, I've seen this before.\nAlex: Thanks Taylor! Let's schedule a quick sync.\nTaylor: How about 2pm today?\nSam: Works for me.\nJordan: I'll join too.",
  "source_description": "n8n slack export",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "engineering-team-2024"
}
```

### Customer Support with Multiple Agents

```json
{
  "name": "Support Escalation - Ticket #4567",
  "episode_body": "customer: I need help with my billing issue.\nagent1: I can help with that. What's your account number?\ncustomer: It's 12345.\nagent1: I see the issue. Let me transfer you to billing specialist.\nagent2: Hi, I'm the billing specialist. I can see your account.\ncustomer: Great, I was charged twice this month.\nagent2: I see the duplicate charge. Let me process a refund.\ncustomer: Thank you!\nagent2: The refund should appear in 3-5 business days.\nagent1: Is there anything else I can help with?\ncustomer: No, that's all. Thanks!",
  "source_description": "n8n support ticket",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "ticket-4567"
}
```

## Advanced Examples

### Conversation with Historical Timestamp

**Important**: The `reference_time` field is optional. If omitted, it defaults to the current time when the episode is added. If you're importing historical conversations or not adding episodes in real-time, always include `reference_time` to preserve the original conversation timestamp.

```json
{
  "name": "Customer Inquiry - Order #789",
  "episode_body": "customer: When will my order ship?\nagent: Your order is scheduled to ship tomorrow.\ncustomer: Can I change the delivery address?\nagent: Yes, I can update that for you. What's the new address?",
  "source_description": "n8n customer service",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "order-789",
  "reference_time": "2024-01-15T14:30:00Z"
}
```

**Using n8n expressions to extract timestamp from message data:**
```json
{
  "name": "{{ $json.conversation_title }}",
  "episode_body": "{{ $json.messages.map(m => m.role + ': ' + m.content).join('\\n') }}",
  "source_description": "{{ $json.source }}",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "{{ $json.conversation_id }}",
  "reference_time": "{{ $json.timestamp || $json.created_at || $json.date }}"
}
```

### Conversation with Custom UUID

```json
{
  "name": "Sales Call - Acme Corp",
  "episode_body": "sales_rep: Thank you for taking the time to meet today.\nprospect: No problem, I'm interested in your product.\nsales_rep: Great! Let me show you our key features.\nprospect: How does pricing work?",
  "source_description": "n8n sales conversation",
  "llm_client": "gemini",
  "embedder_client": "gemini",
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Using Ollama Clients

```json
{
  "name": "Technical Discussion",
  "episode_body": "engineer: We should use async/await for better performance.\narchitect: Agreed, but we need to handle error cases properly.\nengineer: I'll add comprehensive error handling.\narchitect: Perfect, let's review the implementation tomorrow.",
  "source_description": "n8n technical chat",
  "llm_client": "ollama",
  "embedder_client": "ollama"
}
```

## n8n HTTP Request Node Configuration

### Basic Setup

1. **Method**: `POST`
2. **URL**: `http://localhost:18888/api/v1/episodes`
3. **Authentication**: None (or add if your server requires it)
4. **Body Content Type**: `JSON`

### Dynamic Body Example (n8n Expression)

If you're processing conversations from n8n workflows, you can use expressions like:

**For conversations with role field:**
```json
{
  "name": "{{ $json.conversation_title }}",
  "episode_body": "{{ $json.messages.map(m => m.role + ': ' + m.content).join('\\n') }}",
  "source_description": "{{ $json.source }}",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "{{ $json.conversation_id }}",
  "reference_time": "{{ $json.timestamp || $json.created_at || $json.date }}"
}
```

**For multi-party conversations with speaker names:**
```json
{
  "name": "{{ $json.conversation_title }}",
  "episode_body": "{{ $json.messages.map(m => (m.speaker || m.name || m.user) + (m.role ? ' (' + m.role + ')' : '') + ': ' + m.content).join('\\n') }}",
  "source_description": "{{ $json.source }}",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "{{ $json.conversation_id }}",
  "reference_time": "{{ $json.timestamp || $json.created_at || $json.date }}"
}
```

**For Slack/Discord-style exports with user names:**
```json
{
  "name": "{{ $json.channel_name }}",
  "episode_body": "{{ $json.messages.map(m => m.user_name + ': ' + m.text).join('\\n') }}",
  "source_description": "n8n slack export",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "{{ $json.channel_id }}",
  "reference_time": "{{ $json.timestamp || $json.created_at || $json.date }}"
}
```

### Processing Multiple Conversations

If you have an array of conversations, use n8n's Split In Batches or Loop nodes:

**For each conversation:**
```json
{
  "name": "{{ $json.title }}",
  "episode_body": "{{ $json.messages.map(m => m.speaker + ': ' + m.text).join('\\n') }}",
  "source_description": "n8n batch import",
  "llm_client": "groq",
  "embedder_client": "gemini",
  "group_id": "{{ $json.group_id }}",
  "reference_time": "{{ $json.timestamp || $json.created_at || $json.date }}"
}
```

## Message Format Guidelines

1. **Format**: `"actor: content"` or `"speaker_name (role): content"`
   - Actor can be any identifier: names, roles, or combinations
   - Examples: `"user: ..."`, `"Alice: ..."`, `"Bob (developer): ..."`, `"customer: ..."`
2. **Multi-line**: Use `\n` to separate multiple messages in a single episode
3. **Multi-party**: Supports any number of participants (2, 3, 4, or more)
   - Each participant is identified by the text before the colon `:`
   - Graphiti will extract each speaker as a separate entity
4. **Roles**: Common roles include `user`, `assistant`, `system`, or any custom names/roles
5. **Source**: Optional field that defaults to `"message"` for conversations (no need to specify unless using `"text"` or `"json"`)
6. **Timestamps**: 
   - Include `reference_time` when importing historical conversations or batch processing
   - Format: ISO 8601 datetime string (e.g., `"2024-01-15T14:30:00Z"`)
   - If omitted, defaults to the current time when the episode is added
   - This timestamp is used for temporal queries and fact validity tracking

## Response Format

Successful response:
```json
{
  "message": "Episode 'Your Episode Name' added successfully",
  "success": true,
  "episode_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

Error response:
```json
{
  "message": "Error adding episode: <error details>",
  "success": false,
  "episode_uuid": null
}
```

## Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name/identifier for the episode |
| `episode_body` | string | Yes | - | Conversation content in "actor: content" format |
| `source` | string | No | `"message"` | Type: `"text"`, `"json"`, or `"message"` |
| `source_description` | string | No | `""` | Description of the source |
| `llm_client` | string | No | `"groq"` | Options: `"groq"`, `"gemini"`, `"ollama"` |
| `embedder_client` | string | No | `"gemini"` | Options: `"gemini"`, `"ollama"` |
| `group_id` | string | No | `null` | Optional group ID for organizing episodes |
| `uuid` | string | No | `null` | Optional UUID (auto-generated if not provided) |
| `reference_time` | string | No | Current time | ISO 8601 datetime string (e.g., `"2024-01-15T14:30:00Z"`). **Important**: If you're importing historical conversations or not adding episodes in real-time, always include this field to preserve the original conversation timestamp. If omitted, defaults to the current time when the episode is added. |

