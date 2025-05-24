# How to integrate MCP (Model Context Protocol) tools

This guide shows you how to connect external MCP servers to your Xaibo agents, giving them access to tools from other applications and services.

## Configure MCP tool provider

1. Add the MCP tool provider to your agent configuration:

```yaml
# agents/mcp_agent.yml
id: mcp-agent
description: An agent with MCP tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  - id: mcp-tools
    module: xaibo.primitives.modules.tools.MCPToolProvider
    config:
      timeout: 60.0
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to filesystem tools.
        You can read, write, and manage files through MCP tools.
```

## Connect to stdio MCP servers

2. Configure local MCP servers that run as separate processes:

```yaml
servers:
  # Filesystem server
  - name: filesystem
    transport: stdio
    command: ["python", "-m", "mcp_server_filesystem"]
    args: ["--root", "/workspace"]
    env:
      LOG_LEVEL: "INFO"
      
  # Git server
  - name: git
    transport: stdio
    command: ["npx", "@modelcontextprotocol/server-git"]
    args: ["--repository", "/path/to/repo"]
    
  # SQLite server
  - name: database
    transport: stdio
    command: ["python", "-m", "mcp_server_sqlite"]
    args: ["--db-path", "/path/to/database.db"]
```

## Connect to HTTP-based MCP servers

3. Configure MCP servers accessible over HTTP using Server-Sent Events:

```yaml
servers:
  # Web search server
  - name: web_search
    transport: sse
    url: "https://api.example.com/mcp"
    headers:
      Authorization: "Bearer your-api-key"
      Content-Type: "application/json"
      
  # Custom API server
  - name: custom_api
    transport: sse
    url: "https://your-mcp-server.com/mcp"
    headers:
      X-API-Key: "your-api-key"
      User-Agent: "Xaibo-Agent/1.0"
```

## Connect to WebSocket MCP servers

4. Configure MCP servers that use WebSocket connections:

```yaml
servers:
  # Real-time data server
  - name: realtime_data
    transport: websocket
    url: "ws://localhost:8080/mcp"
    headers:
      X-API-Key: "your-websocket-key"
      
  # Chat server
  - name: chat_server
    transport: websocket
    url: "wss://chat.example.com/mcp"
    headers:
      Authorization: "Bearer your-token"
```

## Use multiple MCP servers

5. Configure multiple MCP servers in a single agent:

```yaml
# agents/multi_mcp_agent.yml
id: multi-mcp-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  - id: mcp-tools
    module: xaibo.primitives.modules.tools.MCPToolProvider
    config:
      timeout: 30.0
      servers:
        # Local filesystem access
        - name: fs
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "."]
          
        # Git repository management
        - name: git
          transport: stdio
          command: ["npx", "@modelcontextprotocol/server-git"]
          args: ["--repository", "."]
          
        # Web search capabilities
        - name: search
          transport: sse
          url: "https://search-api.example.com/mcp"
          headers:
            Authorization: "Bearer your-search-api-key"
            
        # Database operations
        - name: db
          transport: websocket
          url: "ws://localhost:8080/mcp"
          headers:
            X-Database-Key: "your-db-key"
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      system_prompt: |
        You are a development assistant with access to:
        - Filesystem operations (fs.* tools)
        - Git repository management (git.* tools) 
        - Web search capabilities (search.* tools)
        - Database operations (db.* tools)
        
        Use these tools to help with development tasks.
```

## Test MCP tool integration

6. Start your agent and verify MCP tools are available:

```bash
# Start the development server
uv run xaibo dev

# Test with a filesystem operation
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mcp-agent",
    "messages": [
      {"role": "user", "content": "List the files in the current directory"}
    ]
  }'
```

## Install common MCP servers

7. Install popular MCP servers for common use cases:

```bash
# Filesystem server
pip install mcp-server-filesystem

# Git server (Node.js)
npm install -g @modelcontextprotocol/server-git

# SQLite server
pip install mcp-server-sqlite

# GitHub server
npm install -g @modelcontextprotocol/server-github

# Brave search server
npm install -g @modelcontextprotocol/server-brave-search
```

## Create a custom MCP server

8. Build your own MCP server for custom functionality:

```python
# custom_mcp_server.py
import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("custom-tools")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="calculate_fibonacci",
            description="Calculate the nth Fibonacci number",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "The position in the Fibonacci sequence"
                    }
                },
                "required": ["n"]
            }
        ),
        Tool(
            name="reverse_string",
            description="Reverse a string",
            inputSchema={
                "type": "object", 
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The string to reverse"
                    }
                },
                "required": ["text"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "calculate_fibonacci":
        n = arguments["n"]
        if n <= 0:
            return [TextContent(type="text", text="Error: n must be positive")]
        
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        
        return [TextContent(type="text", text=f"The {n}th Fibonacci number is {a}")]
    
    elif name == "reverse_string":
        text = arguments["text"]
        reversed_text = text[::-1]
        return [TextContent(type="text", text=f"Reversed: {reversed_text}")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

if __name__ == "__main__":
    asyncio.run(app.run())
```

9. Use your custom MCP server:

```yaml
servers:
  - name: custom
    transport: stdio
    command: ["python", "custom_mcp_server.py"]
```

## Handle MCP server authentication

10. Configure authentication for secure MCP servers:

```yaml
servers:
  # API key authentication
  - name: secure_api
    transport: sse
    url: "https://secure-api.example.com/mcp"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
      X-Client-ID: "${CLIENT_ID}"
      
  # OAuth token authentication  
  - name: oauth_server
    transport: websocket
    url: "wss://oauth-server.com/mcp"
    headers:
      Authorization: "Bearer ${OAUTH_TOKEN}"
      
  # Custom authentication
  - name: custom_auth
    transport: sse
    url: "https://custom.example.com/mcp"
    headers:
      X-API-Key: "${CUSTOM_API_KEY}"
      X-Signature: "${REQUEST_SIGNATURE}"
```

Set environment variables for authentication:

```bash
# .env file
API_TOKEN=your_api_token_here
CLIENT_ID=your_client_id
OAUTH_TOKEN=your_oauth_token
CUSTOM_API_KEY=your_custom_key
REQUEST_SIGNATURE=your_signature
```

## Monitor MCP connections

11. Check MCP server status and debug connection issues:

```python
# debug_mcp.py
import asyncio
from xaibo.primitives.modules.tools.mcp_tool_provider import MCPToolProvider

async def test_mcp_connection():
    config = {
        "servers": [
            {
                "name": "test_server",
                "transport": "stdio", 
                "command": ["python", "-m", "mcp_server_filesystem"],
                "args": ["--root", "."]
            }
        ]
    }
    
    provider = MCPToolProvider(config=config)
    
    try:
        # Initialize and get tools
        await provider.initialize()
        tools = await provider.get_tools()
        
        print(f"Connected to MCP server. Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")
    
    finally:
        await provider.cleanup()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
```

## Best practices

### Server configuration
- Use descriptive server names that indicate their purpose
- Set appropriate timeouts based on server response times
- Group related servers logically in your configuration

### Security
- Store sensitive credentials in environment variables
- Use HTTPS/WSS for remote connections
- Validate server certificates in production

### Error handling
- Configure fallback behavior when servers are unavailable
- Monitor server health and connection status
- Implement retry logic for transient failures

### Performance
- Cache tool definitions to reduce server calls
- Use connection pooling for multiple requests
- Monitor server response times and optimize timeouts

## Troubleshooting

### Server connection failures
- Verify server command and arguments are correct
- Check that required dependencies are installed
- Ensure network connectivity for remote servers

### Authentication errors
- Verify API keys and tokens are valid
- Check header format matches server expectations
- Ensure environment variables are properly set

### Tool execution errors
- Check server logs for detailed error messages
- Verify tool parameters match expected schema
- Test tools directly with the MCP server before integration

### Performance issues
- Increase timeout values for slow servers
- Check network latency for remote connections
- Monitor server resource usage and scaling