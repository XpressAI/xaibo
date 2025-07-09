# CLI Commands Reference

Xaibo provides command-line tools for project initialization, development, and server management.

## xaibo init

Initialize a new Xaibo project with recommended structure.

**Source**: [`src/xaibo/cli/__init__.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/cli/__init__.py)

### Syntax

```bash
uvx xaibo init <project_name>
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_name` | `str` | Yes | Name of the project directory to create |

### Generated Structure

```
project_name/
├── agents/
│   └── example.yml    # Example agent configuration
├── modules/
│   └── __init__.py
├── tools/
│   ├── __init__.py
│   └── example.py     # Example tool implementation
├── tests/
│   └── test_example.py
└── .env               # Environment variables
```

### Example

```bash
# Create a new project
uvx xaibo init my_agent_project

# Navigate to project
cd my_agent_project

# Project is ready for development
```
## xaibo eject

Extract modules from the Xaibo core library to your project for customization.

**Source**: [`src/xaibo/cli/__init__.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/cli/__init__.py)

### Syntax

```bash
# Interactive mode
uvx xaibo eject

# List available modules
uvx xaibo eject list

# Eject specific modules
uvx xaibo eject -m <module_name> [<module_name>...] [-d <destination>]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `list` | `action` | - | List all available packages and ejectable items |
| `-m, --module` | `str[]` | - | Module(s) to eject (space-separated) |
| `-d, --dest` | `str` | current directory | Destination directory |

### Behavior Notes

- Files are ejected to ./modules/ in the current working directory unless specified otherwise
- Existing files will not be overwritten and a warning will be displayed instead
- __init__.py files are automatically created in all necessary directories

## xaibo dev

Start the development server with debug UI and API adapters.

### Syntax

```bash
uv run xaibo dev [options]
```

### Default Adapters

The development server automatically includes:

- **OpenAI API Adapter**: Compatible with OpenAI Chat Completions API
- **Debug UI Adapter**: Web interface for visualizing agent operations
- **Event Tracing**: Automatic capture of all agent interactions

### Example

```bash
# Start development server with defaults
uv run xaibo dev
```

## python -m xaibo.server.web

Start the production web server with configurable adapters.

**Source**: [`src/xaibo/server/web.py:89`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/server/web.py#L89)

### Syntax

```bash
python -m xaibo.server.web [options]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--agent-dir` | `str` | `./agents` | Directory containing agent configurations |
| `--adapter` | `str` | `[]` | Python path to API adapter class (repeatable) |
| `--host` | `str` | `127.0.0.1` | Host address to bind the server |
| `--port` | `int` | `8000` | Port number for the server |
| `--debug-ui` | `bool` | `false` | Enable debug UI and event tracing |
| `--openai-api-key` | `str` | `None` | API key for OpenAI adapter authentication (optional) |
| `--mcp-api-key` | `str` | `None` | API key for MCP adapter authentication (optional) |

### Available Adapters

| Adapter | Description |
|---------|-------------|
| `xaibo.server.adapters.OpenAiApiAdapter` | OpenAI Chat Completions API compatibility |
| `xaibo.server.adapters.OpenAiResponsesApiAdapter` | OpenAI Responses API with conversation management |
| `xaibo.server.adapters.McpApiAdapter` | Model Context Protocol (MCP) server |
| `xaibo.server.adapters.UiApiAdapter` | Debug UI and GraphQL API |

### Examples

```bash
# Start with OpenAI adapter only
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter

# Start with multiple adapters
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter

# Start with debug UI
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --debug-ui true

# Start with API key authentication
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --openai-api-key sk-your-secret-key-here

# Start with both adapters and API keys
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --openai-api-key sk-your-openai-key \
  --mcp-api-key your-mcp-secret-key

# Custom configuration
python -m xaibo.server.web \
  --agent-dir ./production-agents \
  --host 0.0.0.0 \
  --port 9000 \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter
```

## Common Usage Patterns

### Development Workflow

```bash
# 1. Initialize project
uvx xaibo init my_project
cd my_project

# 2. Configure environment
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Start development server
uv run xaibo dev

# 4. Test with curl
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "example", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Production Deployment

```bash
# Start production server with API key authentication
python -m xaibo.server.web \
  --agent-dir ./production-agents \
  --host 0.0.0.0 \
  --port 8000 \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --openai-api-key "${CUSTOM_OPENAI_API_KEY}" \
  --mcp-api-key "${MCP_API_KEY}"
```

### MCP Server Setup

```bash
# Start as MCP server only
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --port 8000

# Start with API key authentication
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --mcp-api-key your-secret-key \
  --port 8000

# Use with MCP client (no authentication)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Use with MCP client (with authentication)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## Environment Variables

API keys can be provided via environment variables instead of command line arguments:

| Environment Variable | Description | Corresponding CLI Option |
|---------------------|-------------|-------------------------|
| `CUSTOM_OPENAI_API_KEY` | API key for OpenAI adapter authentication | `--openai-api-key` |
| `MCP_API_KEY` | API key for MCP adapter authentication | `--mcp-api-key` |

### Environment Variable Examples

```bash
# Set environment variables
export CUSTOM_OPENAI_API_KEY="sk-your-openai-key"
export MCP_API_KEY="your-mcp-secret-key"

# Start server (API keys automatically detected)
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter

# Command line arguments override environment variables
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --openai-api-key "different-key"  # Overrides CUSTOM_OPENAI_API_KEY
```

## Authentication

### OpenAI Adapter Authentication

When an API key is configured for the OpenAI adapter, all requests must include a valid `Authorization` header:

```bash
# Without authentication (no API key configured)
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "agent-id", "messages": [{"role": "user", "content": "Hello"}]}'

# With authentication (API key configured)
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-openai-key" \
  -d '{"model": "agent-id", "messages": [{"role": "user", "content": "Hello"}]}'
```

**Authentication Errors:**

- `401 Unauthorized` - Missing or invalid API key
- `WWW-Authenticate: Bearer` header included in error responses

### MCP Adapter Authentication

When an API key is configured for the MCP adapter, all JSON-RPC requests must include a valid `Authorization` header:

```bash
# Without authentication (no API key configured)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# With authentication (API key configured)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-mcp-secret-key" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

**Authentication Errors:**

- JSON-RPC error response with code `-32001` for authentication failures
- Error messages: "Missing Authorization header", "Invalid Authorization header format", "Invalid API key"