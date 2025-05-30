# OpenAI Responses API Adapter Reference

The OpenAI Responses API Adapter provides OpenAI-compatible response management endpoints for creating, retrieving, and managing model responses with conversation history support.

!!! tip "Quick Start"
    New to the OpenAI Responses API? Start with the [OpenAI Responses Quickstart Guide](../../how-to/api/openai-responses-quickstart.md) to get up and running in 2 minutes.

**Source**: [`src/xaibo/server/adapters/openai_responses.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py)

**Class Path**: `xaibo.server.adapters.openai_responses.OpenAiResponsesApiAdapter`

## Constructor

```python
OpenAiResponsesApiAdapter(xaibo: Xaibo, streaming_timeout=10, responses_dir="./responses")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `xaibo` | [`Xaibo`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/xaibo.py#L23) | Required | Xaibo instance containing registered agents |
| `streaming_timeout` | `int` | `10` | Timeout in seconds for streaming response chunks |
| `responses_dir` | `str` | `"./responses"` | Directory path for storing response database and files |

## Database Schema

The adapter uses SQLite for persistent storage with three main tables:

### responses Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | `TEXT PRIMARY KEY` | Unique response identifier (format: `resp_{uuid}`) |
| `object` | `TEXT` | Object type, always `"response"` |
| `created_at` | `INTEGER` | Unix timestamp of creation |
| `status` | `TEXT` | Response status: `"in_progress"`, `"completed"`, `"failed"`, `"cancelled"` |
| `error` | `TEXT` | JSON-encoded error details if status is `"failed"` |
| `incomplete_details` | `TEXT` | JSON-encoded incomplete response details |
| `instructions` | `TEXT` | System instructions for the response |
| `max_output_tokens` | `INTEGER` | Maximum tokens to generate |
| `model` | `TEXT` | Agent ID used for the response |
| `output` | `TEXT` | JSON-encoded array of output items |
| `parallel_tool_calls` | `BOOLEAN` | Whether parallel tool calls are enabled |
| `previous_response_id` | `TEXT` | ID of previous response in conversation chain |
| `reasoning` | `TEXT` | JSON-encoded reasoning data |
| `store` | `BOOLEAN` | Whether to persist the response |
| `temperature` | `REAL` | Sampling temperature parameter |
| `text` | `TEXT` | JSON-encoded text content |
| `tool_choice` | `TEXT` | JSON-encoded tool choice configuration |
| `tools` | `TEXT` | JSON-encoded array of available tools |
| `top_p` | `REAL` | Nucleus sampling parameter |
| `truncation` | `TEXT` | Truncation strategy |
| `usage` | `TEXT` | JSON-encoded token usage statistics |
| `user_id` | `TEXT` | User identifier |
| `metadata` | `TEXT` | JSON-encoded metadata object |
| `background` | `BOOLEAN` | Whether response runs in background |

### input_items Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | `TEXT PRIMARY KEY` | Unique input item identifier (format: `msg_{uuid}`) |
| `response_id` | `TEXT` | Foreign key to responses table |
| `type` | `TEXT` | Input item type (e.g., `"message"`) |
| `role` | `TEXT` | Message role: `"user"`, `"assistant"`, `"system"` |
| `content` | `TEXT` | JSON-encoded content array |
| `created_at` | `INTEGER` | Unix timestamp of creation |

### conversation_history Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | `TEXT PRIMARY KEY` | Unique history record identifier |
| `response_id` | `TEXT` | Foreign key to responses table |
| `previous_response_id` | `TEXT` | Previous response in conversation chain |
| `conversation_data` | `TEXT` | JSON-encoded conversation messages |
| `created_at` | `INTEGER` | Unix timestamp of creation |

## API Endpoints

All endpoints are mounted under the `/openai` prefix.

### POST `/openai/responses`

Creates a new model response with optional conversation history.

#### Request Format

```json
{
  "input": "Hello, how are you?",
  "model": "my-agent",
  "stream": false,
  "instructions": "You are a helpful assistant",
  "max_output_tokens": 2048,
  "parallel_tool_calls": true,
  "previous_response_id": "resp_abc123",
  "reasoning": null,
  "store": true,
  "temperature": 1.0,
  "text": null,
  "tool_choice": "auto",
  "tools": [],
  "top_p": 1.0,
  "truncation": "disabled",
  "user": "user-123",
  "metadata": {},
  "background": false
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | `str` or `array` | Yes | Input text or array of input items |
| `model` | `str` | Yes | Xaibo agent ID to execute |
| `stream` | `bool` | No | Enable Server-Sent Events streaming (default: `false`) |
| `instructions` | `str` | No | System instructions for the agent |
| `max_output_tokens` | `int` | No | Maximum tokens to generate |
| `parallel_tool_calls` | `bool` | No | Enable parallel tool execution (default: `true`) |
| `previous_response_id` | `str` | No | Previous response ID for conversation continuity |
| `reasoning` | `object` | No | Reasoning configuration |
| `store` | `bool` | No | Whether to persist response (default: `true`) |
| `temperature` | `float` | No | Sampling temperature (default: `1.0`) |
| `text` | `object` | No | Text generation configuration |
| `tool_choice` | `str` or `object` | No | Tool selection strategy (default: `"auto"`) |
| `tools` | `array` | No | Available tools array (default: `[]`) |
| `top_p` | `float` | No | Nucleus sampling parameter (default: `1.0`) |
| `truncation` | `str` | No | Truncation strategy (default: `"disabled"`) |
| `user` | `str` | No | User identifier |
| `metadata` | `object` | No | Custom metadata (default: `{}`) |
| `background` | `bool` | No | Run response in background (default: `false`) |

#### Input Formats

**Text Input:**
```json
{
  "input": "What is the weather like today?"
}
```

**Array Input:**
```json
{
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "What is the weather like today?"
        }
      ]
    }
  ]
}
```

#### Response Format (Non-Streaming)

```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1677652288,
  "status": "completed",
  "error": null,
  "incomplete_details": null,
  "instructions": "You are a helpful assistant",
  "max_output_tokens": 2048,
  "model": "my-agent",
  "output": [
    {
      "type": "message",
      "id": "msg_def456",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "The weather is sunny and warm today!",
          "annotations": []
        }
      ]
    }
  ],
  "parallel_tool_calls": true,
  "previous_response_id": null,
  "reasoning": null,
  "store": true,
  "temperature": 1.0,
  "text": null,
  "tool_choice": "auto",
  "tools": [],
  "top_p": 1.0,
  "truncation": "disabled",
  "usage": {
    "input_tokens": 0,
    "input_tokens_details": {"cached_tokens": 0},
    "output_tokens": 0,
    "output_tokens_details": {"reasoning_tokens": 0},
    "total_tokens": 0
  },
  "user": "user-123",
  "metadata": {},
  "background": false
}
```

#### Streaming Response Format

When `stream: true`, the response uses Server-Sent Events with the following event types:

**response.created:**
```json
{
  "type": "response.created",
  "response": {
    "id": "resp_abc123",
    "object": "response",
    "created_at": 1677652288,
    "status": "in_progress",
    "model": "my-agent"
  },
  "sequence_number": 1
}
```

**response.in_progress:**
```json
{
  "type": "response.in_progress",
  "response": {
    "id": "resp_abc123",
    "status": "in_progress"
  },
  "sequence_number": 2
}
```

**response.output_item.added:**
```json
{
  "type": "response.output_item.added",
  "output_index": 0,
  "item": {
    "id": "msg_def456",
    "status": "in_progress",
    "type": "message",
    "role": "assistant",
    "content": []
  },
  "sequence_number": 3
}
```

**response.content_part.added:**
```json
{
  "type": "response.content_part.added",
  "item_id": "msg_def456",
  "output_index": 0,
  "content_index": 0,
  "part": {
    "type": "output_text",
    "text": "",
    "annotations": []
  },
  "sequence_number": 4
}
```

**response.output_text.delta:**
```json
{
  "type": "response.output_text.delta",
  "item_id": "msg_def456",
  "output_index": 0,
  "content_index": 0,
  "delta": "Hello",
  "sequence_number": 5
}
```

**response.content_part.done:**
```json
{
  "type": "response.content_part.done",
  "item_id": "msg_def456",
  "output_index": 0,
  "content_index": 0,
  "part": {
    "type": "output_text",
    "text": "Hello! The weather is sunny today.",
    "annotations": []
  },
  "sequence_number": 6
}
```

**response.output_text.done:**
```json
{
  "type": "response.output_text.done",
  "item_id": "msg_def456",
  "output_index": 0,
  "content_index": 0,
  "text": "Hello! The weather is sunny today.",
  "sequence_number": 7
}
```

**response.output_item.done:**
```json
{
  "type": "response.output_item.done",
  "output_index": 0,
  "item": {
    "id": "msg_def456",
    "status": "completed",
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "output_text",
        "text": "Hello! The weather is sunny today.",
        "annotations": []
      }
    ]
  },
  "sequence_number": 8
}
```

**response.completed:**
```json
{
  "type": "response.completed",
  "response": {
    "id": "resp_abc123",
    "status": "completed",
    "output": [...],
    "usage": {...}
  },
  "sequence_number": 9
}
```

**Stream termination:**
```
data: [DONE]
```

### GET `/openai/responses/{response_id}`

Retrieves a stored response by ID.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Unique response identifier |
| `include` | `List[str]` | Optional fields to include (query parameter) |

#### Response Format

Returns the same format as [`POST /openai/responses`](#post-openairesponses) non-streaming response.

#### Error Responses

**Response Not Found (404):**
```json
{
  "detail": "Response not found"
}
```

### DELETE `/openai/responses/{response_id}`

Deletes a stored response and all associated data.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Unique response identifier |

#### Response Format

```json
{
  "id": "resp_abc123",
  "object": "response",
  "deleted": true
}
```

#### Error Responses

**Response Not Found (404):**
```json
{
  "detail": "Response not found"
}
```

### POST `/openai/responses/{response_id}/cancel`

Cancels a background response that is in progress.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Unique response identifier |

#### Response Format

Returns the updated response object with `status: "cancelled"`.

#### Error Responses

**Response Not Found (404):**
```json
{
  "detail": "Response not found"
}
```

**Not Background Response (400):**
```json
{
  "detail": "Only background responses can be cancelled"
}
```

### GET `/openai/responses/{response_id}/input_items`

Lists input items for a specific response with pagination support.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_id` | `str` | Required | Unique response identifier |
| `after` | `str` | `None` | Cursor for pagination (item ID) |
| `before` | `str` | `None` | Cursor for pagination (item ID) |
| `include` | `List[str]` | `[]` | Optional fields to include |
| `limit` | `int` | `20` | Number of items to return (1-100) |
| `order` | `str` | `"desc"` | Sort order: `"asc"` or `"desc"` |

#### Response Format

```json
{
  "object": "list",
  "data": [
    {
      "id": "msg_abc123",
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Hello, how are you?"
        }
      ]
    }
  ],
  "first_id": "msg_abc123",
  "last_id": "msg_abc123",
  "has_more": false
}
```

#### Error Responses

**Response Not Found (404):**
```json
{
  "detail": "Response not found"
}
```

## Methods

### [`adapt(app: FastAPI)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L42)

Registers the adapter's routes with a FastAPI application.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | `FastAPI` | FastAPI application instance |

### [`_init_database()`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L45)

Initializes the SQLite database and creates required tables.

### [`_get_db_connection()`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L109)

Returns a new SQLite database connection.

#### Returns

| Type | Description |
|------|-------------|
| `sqlite3.Connection` | Database connection object |

### [`_store_response(response_data: Dict[str, Any])`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L114)

Stores a response object in the database.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_data` | `Dict[str, Any]` | Response data dictionary |

### [`_store_input_items(response_id: str, input_data: Any)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L159)

Stores input items associated with a response.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Response identifier |
| `input_data` | `Any` | Input data (string or array) |

### [`_get_stored_response(response_id: str) -> Optional[Dict[str, Any]]`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L198)

Retrieves a stored response from the database.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Response identifier |

#### Returns

| Type | Description |
|------|-------------|
| `Optional[Dict[str, Any]]` | Response data dictionary or `None` if not found |

### [`_get_conversation_history(previous_response_id: str) -> Optional[SimpleConversation]`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L225)

Retrieves conversation history from a previous response.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `previous_response_id` | `str` | Previous response identifier |

#### Returns

| Type | Description |
|------|-------------|
| `Optional[SimpleConversation]` | Conversation object or `None` if not found |

### [`_store_conversation_history(response_id: str, previous_response_id: str, conversation: SimpleConversation)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L252)

Stores conversation history for a response.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Current response identifier |
| `previous_response_id` | `str` | Previous response identifier |
| `conversation` | [`SimpleConversation`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/conversation/conversation.py#L14) | Conversation object |

### [`create_response(request: Request)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L283)

Main endpoint handler for creating responses.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `Request` | FastAPI request object |

#### Returns

| Type | Description |
|------|-------------|
| `Union[Dict[str, Any], StreamingResponse]` | Response data or streaming response |

### [`_handle_streaming_response(response_data: Dict[str, Any], last_user_message: str, conversation: SimpleConversation)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L368)

Handles streaming response generation with Server-Sent Events.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_data` | `Dict[str, Any]` | Response metadata |
| `last_user_message` | `str` | User's message text |
| `conversation` | [`SimpleConversation`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/conversation/conversation.py#L14) | Conversation context |

#### Returns

| Type | Description |
|------|-------------|
| `StreamingResponse` | FastAPI streaming response with SSE |

### [`_handle_non_streaming_response(response_data: Dict[str, Any], last_user_message: str, conversation: SimpleConversation)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L610)

Handles non-streaming response generation.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_data` | `Dict[str, Any]` | Response metadata |
| `last_user_message` | `str` | User's message text |
| `conversation` | [`SimpleConversation`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/conversation/conversation.py#L14) | Conversation context |

#### Returns

| Type | Description |
|------|-------------|
| `Dict[str, Any]` | Complete response data |

### [`get_response(response_id: str, include: List[str])`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L676)

Endpoint handler for retrieving stored responses.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Response identifier |
| `include` | `List[str]` | Optional fields to include |

#### Returns

| Type | Description |
|------|-------------|
| `Dict[str, Any]` | Response data |

### [`delete_response(response_id: str)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L686)

Endpoint handler for deleting responses.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Response identifier |

#### Returns

| Type | Description |
|------|-------------|
| `Dict[str, Any]` | Deletion confirmation |

### [`cancel_response(response_id: str)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L711)

Endpoint handler for cancelling background responses.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Response identifier |

#### Returns

| Type | Description |
|------|-------------|
| `Dict[str, Any]` | Updated response data |

### [`get_input_items(response_id: str, after: Optional[str], before: Optional[str], include: List[str], limit: int, order: str)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py#L732)

Endpoint handler for listing input items with pagination.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_id` | `str` | Response identifier |
| `after` | `Optional[str]` | Pagination cursor |
| `before` | `Optional[str]` | Pagination cursor |
| `include` | `List[str]` | Optional fields to include |
| `limit` | `int` | Number of items to return |
| `order` | `str` | Sort order |

#### Returns

| Type | Description |
|------|-------------|
| `Dict[str, Any]` | Paginated list of input items |

## Conversation Management

The adapter supports stateful conversations through the `previous_response_id` parameter. When provided, the adapter:

1. Retrieves conversation history from the previous response
2. Reconstructs the [`SimpleConversation`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/conversation/conversation.py#L14) object
3. Adds the new user message to the conversation
4. Passes the full conversation context to the agent
5. Stores the updated conversation history after the response

### Conversation Data Format

Conversation history is stored as JSON in the `conversation_data` field:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    },
    {
      "role": "assistant", 
      "content": "I'm doing well, thank you!"
    }
  ]
}
```

## Agent Integration

The adapter integrates with Xaibo agents using [`ConfigOverrides`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L45) to inject conversation history:

```python
agent = self.xaibo.get_agent_with(agent_id, ConfigOverrides(
    instances={
        '__conversation_history__': conversation,
        '__response__': streaming_handler  # For streaming only
    },
    exchange=[ExchangeConfig(
        protocol='ConversationHistoryProtocol',
        provider='__conversation_history__'
    )]
))
```

### Agent Entry Points

Agents can specify entry points using the format `agent_id/entry_point`:

```json
{
  "model": "my-agent/text"
}
```

If no entry point is specified, `__entry__` is used as the default.

## Error Handling

The adapter implements comprehensive error handling for various failure scenarios:

### Agent Not Found

```json
{
  "detail": "model not found"
}
```

### Missing Required Fields

```json
{
  "detail": "input and model are required"
}
```

### Agent Execution Failure

For streaming responses, failures are communicated via `response.failed` events:

```json
{
  "type": "response.failed",
  "response": {
    "id": "resp_abc123",
    "status": "failed",
    "error": {
      "code": "server_error",
      "message": "Agent execution failed"
    }
  },
  "sequence_number": 10
}
```

## Usage Examples

### Basic Response Creation

```bash
curl -X POST http://localhost:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "What is the capital of France?",
    "model": "my-agent"
  }'
```

### Streaming Response

```bash
curl -X POST http://localhost:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Tell me a story",
    "model": "my-agent",
    "stream": true
  }'
```

### Conversation Continuation

```bash
curl -X POST http://localhost:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "What did I just ask you?",
    "model": "my-agent",
    "previous_response_id": "resp_abc123"
  }'
```

### Retrieve Response

```bash
curl http://localhost:8000/openai/responses/resp_abc123
```

### List Input Items

```bash
curl "http://localhost:8000/openai/responses/resp_abc123/input_items?limit=10&order=asc"
```

### Delete Response

```bash
curl -X DELETE http://localhost:8000/openai/responses/resp_abc123
```

## Configuration

The adapter requires minimal configuration beyond the Xaibo instance:

```python
from xaibo import Xaibo
from xaibo.server.adapters.openai_responses import OpenAiResponsesApiAdapter

xaibo = Xaibo()
adapter = OpenAiResponsesApiAdapter(
    xaibo=xaibo,
    streaming_timeout=30,  # Increase timeout for slow agents
    responses_dir="./data/responses"  # Custom storage directory
)
```

## Performance Considerations

- Database operations are synchronous and may block for large datasets
- Streaming responses maintain active connections and consume memory
- Conversation history grows over time and may require periodic cleanup
- SQLite performance may degrade with very large response volumes

## Limitations

- Token counting is not implemented (usage statistics return zeros)
- Tool calling support is not yet implemented
- Image and multimodal input support is not implemented
- Background response cancellation is basic (no active task termination)
- No built-in rate limiting or authentication