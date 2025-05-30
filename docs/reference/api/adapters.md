# API Adapters Reference

API adapters provide protocol-specific interfaces for interacting with Xaibo agents. They translate external API requests into Xaibo agent calls and format responses according to the target protocol specifications.

## Available Adapters

- **[OpenAiApiAdapter](#openaiapiadapter)** - OpenAI Chat Completions API compatibility
- **[OpenAiResponsesApiAdapter](openai-responses-adapter.md)** - OpenAI Responses API with conversation management
- **[McpApiAdapter](#mcpapiadapter)** - Model Context Protocol (MCP) server functionality
- **[UiApiAdapter](#uiapiadapter)** - GraphQL API for web interface

## OpenAiApiAdapter

Provides OpenAI Chat Completions API compatibility for Xaibo agents.

**Source**: [`src/xaibo/server/adapters/openai.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai.py)

**Class Path**: `xaibo.server.adapters.OpenAiApiAdapter`

### Constructor

```python
OpenAiApiAdapter(xaibo: Xaibo, streaming_timeout=10)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `xaibo` | `Xaibo` | Xaibo instance containing registered agents |
| `streaming_timeout` | `int` | Timeout in seconds for streaming responses (default: 10) |

### API Endpoints

#### GET `/openai/models`

Returns list of available agents as OpenAI-compatible models.

**Response Format:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "my-agent",
      "object": "model",
      "created": 0,
      "owned_by": "organization-owner"
    }
  ]
}
```

#### POST `/openai/chat/completions`

OpenAI-compatible chat completions endpoint.

**Request Format:**

```json
{
  "model": "agent-id",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user", 
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `str` | Yes | Xaibo agent ID to use |
| `messages` | `List[dict]` | Yes | Conversation messages |
| `stream` | `bool` | No | Enable streaming responses |
| `temperature` | `float` | No | *Not yet implemented* - Sampling temperature (0.0-2.0) |
| `max_tokens` | `int` | No | *Not yet implemented* - Maximum tokens to generate |
| `top_p` | `float` | No | *Not yet implemented* - Nucleus sampling parameter |
| `stop` | `List[str]` | No | *Not yet implemented* - Stop sequences |
| `presence_penalty` | `float` | No | *Not yet implemented* - Presence penalty (-2.0 to 2.0) |
| `frequency_penalty` | `float` | No | *Not yet implemented* - Frequency penalty (-2.0 to 2.0) |
| `user` | `str` | No | *Not yet implemented* - User identifier |

**Response Format (Non-Streaming):**

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "agent-id",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

**Response Format (Streaming):**

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"agent-id","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"agent-id","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"agent-id","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### Message Format Support

#### Text Messages

Currently only text messages are supported:

```json
{
  "role": "user",
  "content": "What is the weather like?"
}
```

#### Image Messages (*Planned*)

Image message support is planned for future releases:

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "What's in this image?"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
      }
    }
  ]
}
```

#### Function Calls (*Planned*)

Function call support is planned for future releases:

```json
{
  "role": "assistant",
  "content": null,
  "function_call": {
    "name": "get_weather",
    "arguments": "{\"city\": \"San Francisco\"}"
  }
}
```

### Error Handling

Basic error handling is implemented. Full OpenAI-compatible error response format and specific error codes are not yet fully implemented.

#### Agent Not Found

```json
{
  "detail": "model not found"
}
```

**Note**: Token counting is not yet implemented, so the `usage` field in responses currently returns zeros. OpenAI-compatible error response format and specific error codes are planned for future releases.

### Example Usage

#### cURL

```bash
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-agent",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7
  }'
```

#### Python (OpenAI SDK)

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/openai",
    api_key="not-needed"  # Xaibo doesn't require API keys
)

response = client.chat.completions.create(
    model="my-agent",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
```

#### Streaming

```python
stream = client.chat.completions.create(
    model="my-agent",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

## McpApiAdapter

Implements Model Context Protocol (MCP) server functionality.

**Source**: [`src/xaibo/server/adapters/mcp.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/mcp.py)

**Class Path**: `xaibo.server.adapters.McpApiAdapter`

### Constructor

```python
McpApiAdapter(xaibo: Xaibo)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `xaibo` | `Xaibo` | Xaibo instance containing registered agents |

### API Endpoints

#### POST `/mcp/`

Main MCP JSON-RPC 2.0 endpoint for all protocol communication.

**Request Format:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "method_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Response Format:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "data": "response_data"
  }
}
```

**Error Response Format:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Additional error information"
  }
}
```

### Supported MCP Methods

#### `initialize`

Establishes connection and exchanges capabilities.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    },
    "capabilities": {}
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "xaibo-mcp-server",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {}
    }
  }
}
```

#### `notifications/initialized`

Confirms initialization completion.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

**Response:** No response (notification)

#### `tools/list`

Returns available Xaibo agents as MCP tools.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "my-agent",
        "description": "Execute Xaibo agent 'my-agent'",
        "inputSchema": {
          "type": "object",
          "properties": {
            "message": {
              "type": "string",
              "description": "The text message to send to the agent"
            }
          },
          "required": ["message"]
        }
      }
    ]
  }
}
```

#### `tools/call`

Executes a specific agent with provided arguments.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "my-agent",
    "arguments": {
      "message": "Hello, what can you help me with?"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello! I'm a helpful assistant. I can help you with various tasks..."
      }
    ]
  }
}
```

### Agent Entry Points

For agents with multiple entry points, tools are named as `agent_id.entry_point`:

```json
{
  "tools": [
    {
      "name": "multi-agent.text",
      "description": "Execute text handler for 'multi-agent'"
    },
    {
      "name": "multi-agent.image", 
      "description": "Execute image handler for 'multi-agent'"
    }
  ]
}
```

### Error Codes

| Code | Description | Meaning |
|------|-------------|---------|
| `-32700` | Parse error | Invalid JSON |
| `-32600` | Invalid Request | Missing required fields |
| `-32601` | Method not found | Unsupported MCP method |
| `-32602` | Invalid params | Missing agent or arguments |
| `-32603` | Internal error | Agent execution failure |

### Example Usage

#### cURL

```bash
# Initialize connection
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'

# List available tools
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Call an agent
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "my-agent",
      "arguments": {"message": "Hello!"}
    }
  }'
```

#### Python (MCP Client)

```python
import json
import requests

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.request_id = 0
    
    def _call(self, method: str, params: dict = None):
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def initialize(self):
        return self._call("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "python-client", "version": "1.0.0"}
        })
    
    def list_tools(self):
        return self._call("tools/list")
    
    def call_tool(self, name: str, arguments: dict):
        return self._call("tools/call", {
            "name": name,
            "arguments": arguments
        })

# Usage
client = MCPClient("http://localhost:8000")

# Initialize
init_response = client.initialize()
print("Initialized:", init_response)

# List tools
tools_response = client.list_tools()
print("Available tools:", tools_response["result"]["tools"])

# Call agent
result = client.call_tool("my-agent", {"message": "Hello!"})
print("Agent response:", result["result"]["content"])
```

## UiApiAdapter

Provides debug UI and GraphQL API for agent inspection and monitoring.

**Source**: [`src/xaibo/server/adapters/ui.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/ui.py)

**Class Path**: `xaibo.server.adapters.UiApiAdapter`

### Constructor

```python
UiApiAdapter(xaibo: Xaibo)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `xaibo` | `Xaibo` | Xaibo instance for agent management |

### API Endpoints

#### GET `/`

Serves static UI files.

**Response:** Static files for the web interface

#### POST `/api/ui/graphql`

GraphQL endpoint for querying agent data and execution traces.

**Request Format:**

```json
{
  "query": "query GetAgents { agents { id description modules { id module } } }"
}
```

**Response Format:**

```json
{
  "data": {
    "agents": [
      {
        "id": "my-agent",
        "description": "Example agent",
        "modules": [
          {"id": "llm", "module": "xaibo.primitives.modules.llm.OpenAILLM"}
        ]
      }
    ]
  }
}
```

### GraphQL Schema

#### Agent Type

```graphql
type Agent {
  id: String!
}
```

**Note**: Currently only the `id` field is implemented. The `description`, `modules`, and `exchange` fields are planned for future releases.

#### Module Type

```graphql
type Module {
  id: String!
  module: String!
  config: JSON
  provides: [String!]
  uses: [String!]
}
```

#### Exchange Type

```graphql
type Exchange {
  module: String!
  protocol: String!
  provider: String!
  fieldName: String
}
```

#### DebugTrace Type

```graphql
type DebugTrace {
  agent_id: String!
  events: [Event!]!
}
```

**Note**: The `debug_log` query returns `DebugTrace` instead of `Trace`. The `Trace` type is not implemented.

### Example Queries

#### List All Agents

```graphql
query GetAgents {
  list_agents {
    id
  }
}
```

#### Get Agent Configuration

```graphql
query GetAgentConfig($agentId: String!) {
  agent_config(agent_id: $agentId) {
    id
    modules {
      id
      module
      provides
      uses
      config
    }
    exchange {
      module
      protocol
      provider
    }
  }
}
```

#### Get Debug Traces

```graphql
query GetDebugLog($agentId: String!) {
  debug_log(agent_id: $agentId) {
    agent_id
    events {
      agent_id
      event_name
      event_type
      module_id
      module_class
      method_name
      time
      call_id
      caller_id
      arguments
      result
      exception
    }
  }
}
```

### Debug UI Features

#### Agent Overview

- List of all registered agents
- Agent configuration visualization
- Module dependency graphs

#### Execution Traces

- Real-time trace viewing
- Filtering by agent and event type
- Detailed event inspection

#### Performance Metrics

- Response time statistics
- Token usage tracking
- Error rate monitoring

## Adapter Development

### Creating Custom Adapters

```python
from fastapi import FastAPI
from xaibo import Xaibo

class CustomApiAdapter:
    def __init__(self, xaibo: Xaibo):
        self.xaibo = xaibo
    
    def adapt(self, app: FastAPI):
        """Add routes to the FastAPI application"""
        
        @app.post("/custom/endpoint")
        async def custom_endpoint(request: CustomRequest):
            # Convert request to Xaibo format
            agent_id = request.agent_id
            message = request.message
            
            # Execute agent
            agent = self.xaibo.get_agent(agent_id)
            response = await agent.handle_text_message(message)
            
            # Convert response to custom format
            return CustomResponse(
                result=response.content,
                metadata=response.metadata
            )
```

### Adapter Registration

```python
# Register custom adapter
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=["my.custom.CustomApiAdapter"],
    agent_dir="./agents"
)
```

### Best Practices

1. **Error Handling**: Implement comprehensive error handling
2. **Validation**: Validate all input parameters
3. **Documentation**: Provide clear API documentation
4. **Testing**: Include thorough test coverage
5. **Performance**: Optimize for expected load patterns

## Configuration Examples

### Multi-Adapter Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  xaibo-server:
    image: xaibo:latest
    ports:
      - "8000:8000"
    command: >
      python -m xaibo.server.web
      --agent-dir /app/agents
      --adapter xaibo.server.adapters.OpenAiApiAdapter
      --adapter xaibo.server.adapters.McpApiAdapter
      --adapter xaibo.server.adapters.UiApiAdapter
      --host 0.0.0.0
      --port 8000
    volumes:
      - ./agents:/app/agents
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Load Balancer Configuration

```nginx
upstream xaibo_backend {
    server xaibo-1:8000;
    server xaibo-2:8000;
    server xaibo-3:8000;
}

server {
    listen 80;
    server_name api.example.com;
    
    location /openai/ {
        proxy_pass http://xaibo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /mcp {
        proxy_pass http://xaibo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}