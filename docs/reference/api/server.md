# Web Server API Reference

The Xaibo web server provides a FastAPI-based HTTP server with configurable adapters for different API protocols. It supports hot-reloading of agent configurations and comprehensive event tracing.

**Source**: [`src/xaibo/server/web.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/web.py)

## XaiboWebServer

Main web server class that hosts Xaibo agents with configurable API adapters.

### Constructor

```python
XaiboWebServer(
    xaibo: Xaibo,
    adapters: List[str],
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
| `adapters` | `List[str]` | Required | List of adapter class paths to load |
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
| `--debug-ui` | `bool` | `False` | Enable debug UI and tracing |

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

| Adapter | Description | Path |
|---------|-------------|------|
| OpenAI API | OpenAI Chat Completions compatibility | `xaibo.server.adapters.OpenAiApiAdapter` |
| MCP API | Model Context Protocol server | `xaibo.server.adapters.McpApiAdapter` |
| UI API | Debug UI and GraphQL API | `xaibo.server.adapters.UiApiAdapter` |

## Error Handling

### Configuration Errors

```python
# Invalid agent configuration
ValueError: "Invalid agent config in ./agents/broken.yml: Missing required field 'id'"

# Adapter loading error
ImportError: "No module named 'invalid.adapter.path'"
```

### Runtime Errors

```python
# Port already in use
OSError: "[Errno 48] Address already in use"

# Permission denied
PermissionError: "[Errno 13] Permission denied: './agents'"
```

### Agent Registration Errors

```python
# Duplicate agent ID
ValueError: "Agent with ID 'duplicate' already registered"

# Invalid agent configuration
ValidationError: "Agent configuration validation failed"
```

## Performance Considerations

### File Watching

- Uses `watchfiles` for efficient file system monitoring
- Debounces rapid file changes
- Handles large directory structures efficiently

### Agent Loading

- Lazy loading of agent configurations
- Incremental updates for changed files only
- Parallel loading of multiple configurations

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

## Monitoring and Logging

### Server Metrics

```python
# Access server metrics
server_stats = {
    "active_agents": len(xaibo.agents),
    "total_requests": request_counter,
    "uptime": time.time() - start_time
}
```

### Event Tracing

```python
# Event trace structure
{
    "timestamp": "2024-01-15T10:30:00Z",
    "agent_id": "example-agent",
    "event_type": "llm_request",
    "data": {
        "messages": [...],
        "options": {...}
    }
}
```

### Log Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Server-specific logger
logger = logging.getLogger("xaibo.server")
```

## Development Workflow

### Local Development

```python
# Development server setup
from xaibo import Xaibo
from xaibo.server.web import XaiboWebServer

xaibo = Xaibo()
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=["xaibo.server.adapters.OpenAiApiAdapter"],
    agent_dir="./dev-agents",
    debug=True
)
server.start()
```

### Testing

```python
import pytest
from fastapi.testclient import TestClient

def test_server_startup():
    xaibo = Xaibo()
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[],
        agent_dir="./test-agents"
    )
    
    client = TestClient(server.app)
    response = client.get("/health")
    assert response.status_code == 200
```

### Production Deployment

```python
# Production server configuration
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[
        "xaibo.server.adapters.OpenAiApiAdapter",
        "xaibo.server.adapters.McpApiAdapter"
    ],
    agent_dir="/app/agents",
    host="0.0.0.0",
    port=8000,
    debug=False
)

# Use production ASGI server
import uvicorn
uvicorn.run(
    server.app,
    host="0.0.0.0",
    port=8000,
    workers=4,
    access_log=True
)
```

## Configuration Examples

### Environment-Based Configuration

```python
import os

server = XaiboWebServer(
    xaibo=xaibo,
    adapters=os.getenv("XAIBO_ADAPTERS", "").split(","),
    agent_dir=os.getenv("XAIBO_AGENT_DIR", "./agents"),
    host=os.getenv("XAIBO_HOST", "127.0.0.1"),
    port=int(os.getenv("XAIBO_PORT", "8000")),
    debug=os.getenv("XAIBO_DEBUG", "false").lower() == "true"
)
```

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "xaibo.server.web", \
     "--agent-dir", "/app/agents", \
     "--adapter", "xaibo.server.adapters.OpenAiApiAdapter", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
```

### Kubernetes Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xaibo-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xaibo-server
  template:
    metadata:
      labels:
        app: xaibo-server
    spec:
      containers:
      - name: xaibo-server
        image: xaibo:latest
        ports:
        - containerPort: 8000
        env:
        - name: XAIBO_HOST
          value: "0.0.0.0"
        - name: XAIBO_PORT
          value: "8000"
        - name: XAIBO_AGENT_DIR
          value: "/app/agents"
        volumeMounts:
        - name: agent-configs
          mountPath: /app/agents
      volumes:
      - name: agent-configs
        configMap:
          name: xaibo-agents