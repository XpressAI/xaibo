# Server API Endpoints

## OpenAI-Compatible API

When using the [`OpenAiApiAdapter`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai_responses.py), Xaibo provides OpenAI-compatible endpoints:

### Chat Completions

**Endpoint:** `POST /openai/chat/completions`

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Hello, what time is it now?"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": false
  }'
```

**Request Body:**
- `model` (required): Agent ID to use
- `messages` (required): Array of message objects
- `temperature` (optional): Sampling temperature
- `max_tokens` (optional): Maximum tokens to generate
- `stream` (optional): Enable streaming responses

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "example",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The current time is 2024-01-15 14:30:25 UTC"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 12,
    "total_tokens": 22
  }
}
```

### Models List

**Endpoint:** `GET /openai/models`

```bash
curl http://127.0.0.1:9001/openai/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "example",
      "object": "model",
      "created": 1677652288,
      "owned_by": "xaibo"
    }
  ]
}
```

## MCP (Model Context Protocol) API

When using the [`McpApiAdapter`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/mcp.py), Xaibo provides MCP-compatible endpoints:

### MCP JSON-RPC Endpoint

**Endpoint:** `POST /mcp`

All MCP communication happens through this single JSON-RPC 2.0 endpoint.

#### Initialize Connection

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {
        "name": "my-client",
        "version": "1.0.0"
      }
    }
  }'
```

#### List Available Tools

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

#### Call Agent Tool

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "example",
      "arguments": {
        "message": "Hello, what can you help me with?"
      }
    }
  }'
```

## Error Handling

### Common Error Types

#### ConfigurationError
Raised when agent configuration is invalid.

```python
from xaibo.core.exceptions import ConfigurationError

try:
    xaibo.register_agent(invalid_config)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

#### ModuleNotFoundError
Raised when a specified module cannot be imported.

#### ProtocolMismatchError
Raised when a module doesn't implement the required protocol.

### Error Response Format

API errors follow standard HTTP status codes and include detailed error information:

```json
{
  "error": {
    "type": "ConfigurationError",
    "message": "Module 'invalid.module' not found",
    "details": {
      "module_id": "llm",
      "module_path": "invalid.module"
    }
  }
}
```

## Complete Agent Setup

```python
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter
from xaibo.core.config import AgentConfig

# Create agent configuration
agent_config = AgentConfig.from_file("agents/example.yml")

# Initialize Xaibo
xaibo = Xaibo()
xaibo.register_agent(agent_config)

# Create web server with OpenAI adapter
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[OpenAiApiAdapter(xaibo)]
)

# Start server
server.run(host="0.0.0.0", port=8000)