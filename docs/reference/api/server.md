# Web Server API Reference

The Xaibo web server provides a FastAPI-based HTTP server with configurable adapters for different API protocols. It supports hot-reloading of agent configurations and comprehensive event tracing.

**Source**: [`src/xaibo/server/web.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/web.py)

## XaiboWebServer

Main web server class that hosts Xaibo agents with configurable API adapters.

### Constructor

```python
XaiboWebServer(
    xaibo: Xaibo,
    adapters: list[str],
    agent_dir: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
    openai_api_key: Optional[str] = None,
    mcp_api_key: Optional[str] = None
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `xaibo` | `Xaibo` | Required | Xaibo instance for agent management |
| `adapters` | `list[str]` | Required | List of adapter class paths to load |
| `agent_dir` | `str` | Required | Directory containing agent configuration files |
| `host` | `str` | `"127.0.0.1"` | Host address to bind the server |
| `port` | `int` | `8000` | Port number for the server |
| `debug` | `bool` | `False` | Enable debug mode with UI and event tracing |
| `openai_api_key` | `Optional[str]` | `None` | API key for OpenAI adapter authentication |
| `mcp_api_key` | `Optional[str]` | `None` | API key for MCP adapter authentication |

#### Example

```python
from xaibo import Xaibo
from xaibo.server.web import XaiboWebServer

# Initialize Xaibo
xaibo = Xaibo()

# Create server with multiple adapters and API keys
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[
        "xaibo.server.adapters.OpenAiApiAdapter",
        "xaibo.server.adapters.McpApiAdapter"
    ],
    agent_dir="./agents",
    host="0.0.0.0",
    port=9000,
    debug=True,
    openai_api_key="sk-your-openai-key",
    mcp_api_key="your-mcp-secret-key"
)
```

### Methods

#### `start() -> None`

Start the web server using uvicorn.

```python
server.start()
```

**Features:**
- Starts FastAPI application with uvicorn
- Enables hot-reloading of agent configurations
- Configures CORS middleware for cross-origin requests
- Sets up event tracing if debug mode is enabled

### Configuration File Watching

The server automatically watches the agent directory for changes and reloads configurations:

#### Supported File Types

- `.yml` files
- `.yaml` files

#### Watch Behavior

- **Added Files**: Automatically registers new agents
- **Modified Files**: Reloads and re-registers changed agents
- **Deleted Files**: Unregisters removed agents
- **Subdirectories**: Recursively watches all subdirectories

#### Example Directory Structure

```
agents/
├── production/
│   ├── customer_service.yml
│   └── data_analysis.yml
├── development/
│   ├── test_agent.yml
│   └── experimental.yml
└── shared/
    └── common_tools.yml
```

### Debug Mode Features

When `debug=True`, the server enables additional features:

#### Event Tracing

- Captures all agent interactions
- Stores traces in `./debug` directory
- Provides detailed execution logs

#### Debug UI

- Adds UI adapter automatically
- Provides web interface for agent inspection
- Visualizes agent execution flows

#### Event Listener

```python
from xaibo.server.adapters.ui import UIDebugTraceEventListener
from pathlib import Path

# Automatically added in debug mode
event_listener = UIDebugTraceEventListener(Path("./debug"))
xaibo.register_event_listener("", event_listener.handle_event)
```

### CORS Configuration

The server includes permissive CORS settings for development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Note**: Configure more restrictive CORS settings for production deployments.

### Lifecycle Management

The server uses FastAPI's lifespan events for proper resource management:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start configuration file watcher
    watcher_task = asyncio.create_task(watch_config_files())
    yield
    # Shutdown: Cancel watcher and cleanup
    watcher_task.cancel()
    try:
        await watcher_task
    except asyncio.CancelledError:
        pass
```

## Command Line Interface

The server can be started directly from the command line:

```bash
python -m xaibo.server.web [options]
```

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--agent-dir` | `str` | `"./agents"` | Directory containing agent configurations |
| `--adapter` | `str` | `[]` | Adapter class path (repeatable) |
| `--host` | `str` | `"127.0.0.1"` | Host address to bind |
| `--port` | `int` | `8000` | Port number |
| `--debug-ui` | `bool` | `False` | Enable writing debug traces and start web ui |
| `--openai-api-key` | `str` | `None` | API key for OpenAI adapter authentication |
| `--mcp-api-key` | `str` | `None` | API key for MCP adapter authentication |

### Examples

#### Basic Server

```bash
python -m xaibo.server.web \
  --agent-dir ./my-agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter
```

#### Multi-Adapter Server

```bash
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 0.0.0.0 \
  --port 9000
```

#### Debug Server

```bash
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --debug-ui true
```

## Adapter Integration

### Adapter Loading

Adapters are loaded dynamically using the `get_class_by_path` utility:

```python
def get_class_by_path(path: str) -> Type:
    """Load a class from its import path"""
    parts = path.split('.')
    pkg = '.'.join(parts[:-1])
    cls = parts[-1]
    package = importlib.import_module(pkg)
    clazz = getattr(package, cls)
    return clazz
```

### Adapter Instantiation

Each adapter is instantiated with the Xaibo instance and appropriate API keys:

```python
for adapter in adapters:
    clazz = get_class_by_path(adapter)
    # Pass API keys to appropriate adapters based on class name
    class_name = clazz.__name__
    if class_name == "OpenAiApiAdapter":
        instance = clazz(self.xaibo, api_key=self.openai_api_key)
    elif class_name == "McpApiAdapter":
        instance = clazz(self.xaibo, api_key=self.mcp_api_key)
    else:
        instance = clazz(self.xaibo)
    instance.adapt(self.app)
```

### Available Adapters

| Adapter | Description | Path | Endpoints |
|---------|-------------|------|-----------|
| OpenAI API | OpenAI Chat Completions compatibility | `xaibo.server.adapters.OpenAiApiAdapter` | `/openai/models`, `/openai/chat/completions` |
| OpenAI Responses API | OpenAI Responses API with conversation management | `xaibo.server.adapters.OpenAiResponsesApiAdapter` | `/openai/responses` |
| MCP API | Model Context Protocol server | `xaibo.server.adapters.McpApiAdapter` | `/mcp/` |
| UI API | Debug UI and GraphQL API | `xaibo.server.adapters.UiApiAdapter` | `/api/ui/graphql`, `/` (static files) |

## Error Handling

### Configuration Errors

```python
# Invalid agent configuration
ValueError: "Agent configuration validation error"

# Adapter loading error
ImportError: "Failed to load adapter class"
```

### Runtime Errors

```python
# Port already in use
OSError: "Address already in use"

# Permission denied
PermissionError: "Permission denied accessing agent directory"
```

### Agent Registration Errors

```python
# Duplicate agent ID
ValueError: "Agent ID already registered"

# Invalid agent configuration
ValidationError: "Agent configuration validation failed"
```

## Performance Considerations

### File Watching

- Uses `watchfiles.awatch` for efficient file system monitoring
- Monitors agent directory for configuration changes
- Handles large directory structures efficiently

### Agent Loading

- Lazy loading of agent configurations
- Incremental updates for changed files only
- Sequential loading and registration of configurations

### Memory Management

- Automatic cleanup of unregistered agents
- Efficient event listener management
- Resource cleanup on server shutdown

## Security Considerations

### File System Access

- Restricts agent loading to specified directory
- Validates file paths to prevent directory traversal
- Sandboxes agent execution environments

### Network Security

- Configurable host binding
- CORS policy configuration
- Request validation and sanitization

### Agent Isolation

- Isolated agent execution contexts
- Resource limits per agent
- Error containment between agents

## Authentication

The web server supports optional API key authentication for OpenAI and MCP adapters.

### Environment Variables

API keys can be provided via environment variables:

| Environment Variable | Description | Adapter |
|---------------------|-------------|---------|
| `CUSTOM_OPENAI_API_KEY` | API key for OpenAI adapter authentication | [`OpenAiApiAdapter`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai.py) |
| `MCP_API_KEY` | API key for MCP adapter authentication | [`McpApiAdapter`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/mcp.py) |

### OpenAI Adapter Authentication

When `openai_api_key` is configured, the OpenAI adapter requires Bearer token authentication:

#### Request Format

```http
POST /openai/chat/completions
Authorization: Bearer sk-your-openai-key
Content-Type: application/json

{
  "model": "agent-id",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

#### Authentication Verification

**Source**: [`src/xaibo/server/adapters/openai.py:41`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/openai.py#L41)

```python
async def _verify_api_key(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Verify API key for protected endpoints"""
    if not self.api_key:
        return  # No API key configured, allow access
        
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    if credentials.credentials != self.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
```

#### Error Responses

| Status Code | Description | Response Headers |
|-------------|-------------|------------------|
| `401` | Missing Authorization header | `WWW-Authenticate: Bearer` |
| `401` | Invalid API key | `WWW-Authenticate: Bearer` |

### MCP Adapter Authentication

When `mcp_api_key` is configured, the MCP adapter requires Bearer token authentication:

#### Request Format

```http
POST /mcp
Authorization: Bearer your-mcp-secret-key
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

#### Authentication Verification

**Source**: [`src/xaibo/server/adapters/mcp.py:52`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/adapters/mcp.py#L52)

```python
# Verify API key if configured
if self.api_key:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return self._create_error_response(None, -32001, "Missing Authorization header")
    
    if not auth_header.startswith("Bearer "):
        return self._create_error_response(None, -32001, "Invalid Authorization header format")
    
    provided_key = auth_header[7:]  # Remove "Bearer " prefix
    if provided_key != self.api_key:
        return self._create_error_response(None, -32001, "Invalid API key")
```

#### Error Responses

JSON-RPC 2.0 error responses with HTTP status `200`:

| Error Code | Description |
|------------|-------------|
| `-32001` | Missing Authorization header |
| `-32001` | Invalid Authorization header format |
| `-32001` | Invalid API key |

#### Example Error Response

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32001,
    "message": "Invalid API key"
  }
}
```

### Security Best Practices

#### API Key Management

- Store API keys in environment variables, not in code
- Use different API keys for different environments
- Rotate API keys regularly
- Monitor API key usage for unusual patterns

#### Network Security

- Use HTTPS in production environments
- Configure restrictive CORS policies for production
- Implement rate limiting for public endpoints
- Use reverse proxies for additional security layers

#### Example Production Configuration

```bash
# Set environment variables
export CUSTOM_OPENAI_API_KEY="sk-prod-key-$(date +%s)"
export MCP_API_KEY="mcp-prod-key-$(date +%s)"

# Start server with authentication
python -m xaibo.server.web \
  --agent-dir ./production-agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 0.0.0.0 \
  --port 8000
```