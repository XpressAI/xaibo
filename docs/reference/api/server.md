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
    debug: bool = False
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

#### Example

```python
from xaibo import Xaibo
from xaibo.server.web import XaiboWebServer

# Initialize Xaibo
xaibo = Xaibo()

# Create server with multiple adapters
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[
        "xaibo.server.adapters.OpenAiApiAdapter",
        "xaibo.server.adapters.McpApiAdapter"
    ],
    agent_dir="./agents",
    host="0.0.0.0",
    port=9000,
    debug=True
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

Each adapter is instantiated with the Xaibo instance:

```python
for adapter in adapters:
    clazz = get_class_by_path(adapter)
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