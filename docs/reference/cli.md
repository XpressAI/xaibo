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

## xaibo dev

Start the development server with debug UI and API adapters.

### Syntax

```bash
uv run xaibo dev [options]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--host` | `str` | `127.0.0.1` | Host address to bind the server |
| `--port` | `int` | `9001` | Port number for the server |
| `--agent-dir` | `str` | `./agents` | Directory containing agent configurations |
| `--debug` | `bool` | `true` | Enable debug UI and event tracing |

### Default Adapters

The development server automatically includes:
- **OpenAI API Adapter**: Compatible with OpenAI Chat Completions API
- **Debug UI Adapter**: Web interface for visualizing agent operations
- **Event Tracing**: Automatic capture of all agent interactions

### Example

```bash
# Start development server with defaults
uv run xaibo dev

# Start on different port
uv run xaibo dev --port 8080

# Start with custom agent directory
uv run xaibo dev --agent-dir ./my-agents

# Start without debug UI
uv run xaibo dev --debug false
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

### Available Adapters

| Adapter | Description |
|---------|-------------|
| `xaibo.server.adapters.OpenAiApiAdapter` | OpenAI Chat Completions API compatibility |
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

# Custom configuration
python -m xaibo.server.web \
  --agent-dir ./production-agents \
  --host 0.0.0.0 \
  --port 9000 \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter
```

## Environment Variables

Xaibo respects standard environment variables for API keys and configuration:

### LLM Provider Keys

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Bedrock |

### Server Configuration

| Variable | Description |
|----------|-------------|
| `XAIBO_HOST` | Default host for server binding |
| `XAIBO_PORT` | Default port for server |
| `XAIBO_AGENT_DIR` | Default agent configuration directory |

### Example .env File

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# AWS Credentials for Bedrock
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Server Configuration
XAIBO_HOST=0.0.0.0
XAIBO_PORT=8000
XAIBO_AGENT_DIR=./agents

# Debug Settings
LOG_LEVEL=INFO
```

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Configuration error |
| `3` | Import error |
| `4` | Network error |

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
# Start production server
python -m xaibo.server.web \
  --agent-dir ./production-agents \
  --host 0.0.0.0 \
  --port 8000 \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter
```

### MCP Server Setup

```bash
# Start as MCP server only
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --port 8000

# Use with MCP client
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'