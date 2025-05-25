# How to integrate MCP (Model Context Protocol) tools

This guide shows you how to connect external MCP servers to your Xaibo agents, giving them access to tools from other applications and services.

## Configure MCP tool provider

Add the MCP tool provider to your agent configuration:

```yaml
# agents/mcp_agent.yml
id: mcp-agent
description: An agent with MCP tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
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

Configure local MCP servers that run as separate processes:

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

Configure MCP servers accessible over HTTP using Server-Sent Events:

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

Configure MCP servers that use WebSocket connections:

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

Configure multiple MCP servers in a single agent:

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

Start your agent and verify MCP tools are available:

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

Install popular MCP servers for common use cases:

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

Build your own MCP server for custom functionality:

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

Use your custom MCP server:

```yaml
servers:
  - name: custom
    transport: stdio
    command: ["python", "custom_mcp_server.py"]
```

## Handle MCP server authentication

Configure authentication for secure MCP servers:

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

Check MCP server status and debug connection issues:

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
- Configure environment-specific settings for development, staging, and production
- Document server dependencies and requirements clearly
- Use consistent naming conventions across all server configurations

### Security
- Store sensitive credentials in environment variables
- Use HTTPS/WSS for remote connections
- Validate server certificates in production
- Implement proper authentication token rotation
- Restrict server access to necessary network ranges
- Log authentication attempts for security monitoring
- Use least-privilege principles for server permissions

### Error handling
- Configure fallback behavior when servers are unavailable
- Monitor server health and connection status
- Implement retry logic for transient failures
- Design graceful degradation when tools are temporarily unavailable
- Provide meaningful error messages that help users understand what went wrong
- Log errors with sufficient context for debugging
- Implement circuit breaker patterns for unreliable external services

### Performance
- Cache tool definitions to reduce server calls
- Use connection pooling for multiple requests
- Monitor server response times and optimize timeouts
- Implement request queuing for high-traffic scenarios
- Use async operations to prevent blocking
- Monitor memory usage and implement cleanup procedures
- Profile tool execution times to identify bottlenecks

## Exception handling best practices

### When to use exceptions vs. error returns

**Use exceptions for:**
- Server connection failures and network timeouts
- Protocol violations and malformed responses
- Authentication and authorization failures
- Critical system errors that prevent tool execution
- Configuration errors that make tools unusable

**Use error returns for:**
- Invalid tool parameters and user input validation
- Business logic errors and expected failure conditions
- Resource not found scenarios
- Rate limiting and quota exceeded situations
- Recoverable errors that users can fix by adjusting inputs

### Structure error messages for LLM consumption

Design error messages that provide clear, actionable information:

- **Be specific**: Include exact parameter names, expected formats, and current values
- **Provide context**: Explain what the tool was trying to accomplish when it failed
- **Suggest solutions**: Offer concrete steps to resolve the issue
- **Use consistent format**: Structure errors uniformly across all tools
- **Include error codes**: Use standardized error types for programmatic handling
- **Add examples**: Show correct parameter formats when validation fails

### Exception hierarchy and custom exception types

Create a structured exception hierarchy for different error categories:

- **MCPToolError**: Base exception for all tool-related errors
- **ParameterValidationError**: Invalid or missing parameters
- **ExternalServiceError**: Failures from external APIs or services
- **ResourceNotFoundError**: Requested resources don't exist
- **AuthenticationError**: Authentication or authorization failures
- **TimeoutError**: Operations that exceed time limits
- **ConfigurationError**: Invalid server or tool configuration

### Logging and debugging failed tool calls

Implement comprehensive logging strategies:

- **Structured logging**: Use consistent log formats with relevant metadata
- **Call tracking**: Assign unique IDs to track tool calls across systems
- **Performance metrics**: Log execution times and resource usage
- **Error context**: Include full stack traces and relevant state information
- **Security considerations**: Avoid logging sensitive data like credentials
- **Log levels**: Use appropriate levels (DEBUG, INFO, WARN, ERROR) for different events
- **Retention policies**: Configure log rotation and archival strategies

### Async tool implementations

Handle asynchronous operations properly:

- **Timeout management**: Set reasonable timeouts for all async operations
- **Resource cleanup**: Ensure proper cleanup of connections and resources
- **Cancellation handling**: Support operation cancellation when needed
- **Concurrent execution**: Manage concurrent tool calls safely
- **Error propagation**: Properly handle and propagate async exceptions
- **Progress tracking**: Provide feedback for long-running operations

### Complex parameter validation

Implement robust parameter validation:

- **Type checking**: Validate parameter types before processing
- **Range validation**: Check numeric values are within acceptable ranges
- **Format validation**: Use regex or schemas for structured data
- **Dependency validation**: Ensure related parameters are consistent
- **Sanitization**: Clean and normalize input data
- **Default handling**: Provide sensible defaults for optional parameters
- **Custom validators**: Create reusable validation functions for complex types

### Tool testing strategies

Develop comprehensive testing approaches:

- **Unit tests**: Test individual tool functions in isolation
- **Integration tests**: Test tool interactions with external services
- **Error scenario tests**: Verify proper handling of all error conditions
- **Performance tests**: Ensure tools meet response time requirements
- **Security tests**: Validate input sanitization and access controls
- **Mock testing**: Use mocks to test error conditions and edge cases
- **End-to-end tests**: Test complete tool workflows through the MCP protocol

### Performance optimization techniques

Optimize tool performance:

- **Connection reuse**: Maintain persistent connections to external services
- **Caching strategies**: Cache expensive computations and API responses
- **Batch operations**: Group multiple operations when possible
- **Lazy loading**: Load resources only when needed
- **Memory management**: Monitor and optimize memory usage
- **Async patterns**: Use async/await for I/O-bound operations
- **Resource pooling**: Share expensive resources across tool calls

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

## Debug and troubleshoot tools

Use Xaibo's built-in debugging capabilities to diagnose tool discovery, connection, and execution issues.

### Enable debug UI

Start your development server with the debug UI enabled:

```bash
# Start with debug UI (automatically enabled in dev mode)
uv run xaibo dev

# Access debug UI at http://localhost:9001
```

The debug UI provides:

- Real-time event tracing for all tool operations
- Visual representation of tool discovery and execution
- Detailed error logs and stack traces
- Performance metrics for tool calls

### Use list_tools() for programmatic debugging

Access tool information programmatically using the [`list_tools()`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/tools.py:9) method:

```python
# debug_mcp_tools.py
import asyncio
from xaibo.primitives.modules.tools.mcp_tool_provider import MCPToolProvider

async def debug_mcp_tools():
    """Debug MCP tool discovery and availability"""
    config = {
        "servers": [
            {
                "name": "filesystem",
                "transport": "stdio",
                "command": ["python", "-m", "mcp_server_filesystem"],
                "args": ["--root", "."]
            }
        ]
    }
    
    provider = MCPToolProvider(config=config)
    
    try:
        # Initialize the provider
        await provider.initialize()
        
        # List all available tools
        tools = await provider.list_tools()
        
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}")
            print(f"    Description: {tool.description}")
            print(f"    Parameters: {len(tool.parameters)} params")
            for param in tool.parameters:
                print(f"      - {param.name}: {param.type} ({'required' if param.required else 'optional'})")
            print()
            
    except Exception as e:
        print(f"Error debugging tools: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await provider.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_mcp_tools())
```

### Step-by-step debugging procedure

Follow these steps to diagnose MCP tool issues:

#### 1. Verify server connectivity

Test if your MCP server starts correctly:

```bash
# Test filesystem server directly
python -m mcp_server_filesystem --root .

# Test with specific arguments
npx @modelcontextprotocol/server-git --repository .
```

#### 2. Check tool discovery

Use the debug script to verify tools are discovered:

```python
# Check if tools are found
tools = await provider.list_tools()
if not tools:
    print("No tools discovered - check server configuration")
else:
    print(f"Discovered {len(tools)} tools")
```

#### 3. Test tool execution

Execute a simple tool to verify functionality:

```python
# Test tool execution
try:
    result = await provider.execute_tool("list_files", {"path": "."})
    print(f"Tool executed successfully: {result}")
except Exception as e:
    print(f"Tool execution failed: {e}")
```

#### 4. Monitor with debug UI

1. Start your agent with debug UI enabled
2. Navigate to [`http://localhost:9001`](http://localhost:9001)
3. Trigger tool operations through your agent
4. Review the event trace for errors or performance issues

### Common troubleshooting scenarios

#### Server fails to start

**Symptoms:** No tools discovered, connection timeouts

**Solutions:**
- Verify server command and arguments are correct
- Check that required dependencies are installed
- Test server startup independently
- Review server logs for startup errors

```bash
# Test server startup
python -m mcp_server_filesystem --root . --verbose

# Check dependencies
pip list | grep mcp
```

#### Tools not appearing in agent

**Symptoms:** [`list_tools()`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/tools.py:9) returns empty list

**Solutions:**
- Verify server configuration in agent YAML
- Check server name matches configuration
- Ensure transport type is correct
- Test with debug script

```python
# Verify configuration
config = {
    "servers": [
        {
            "name": "test_server",  # Check this name
            "transport": "stdio",   # Verify transport type
            "command": ["python", "-m", "mcp_server_filesystem"],
            "args": ["--root", "."]
        }
    ]
}
```

#### Authentication failures

**Symptoms:** Connection refused, 401/403 errors

**Solutions:**
- Verify API keys and tokens are valid
- Check environment variables are set
- Confirm header format matches server expectations
- Test authentication independently

```bash
# Check environment variables
echo $API_TOKEN
echo $CLIENT_ID

# Test API endpoint directly
curl -H "Authorization: Bearer $API_TOKEN" https://api.example.com/mcp
```

#### Tool execution errors

**Symptoms:** Tools discovered but execution fails

**Solutions:**
- Verify parameter types match tool schema
- Check parameter names are correct
- Review tool documentation for requirements
- Test with minimal parameters first

```python
# Debug tool parameters
tool = tools[0]  # Get first tool
print(f"Required parameters: {[p.name for p in tool.parameters if p.required]}")
print(f"Optional parameters: {[p.name for p in tool.parameters if not p.required]}")

# Test with minimal parameters
minimal_params = {p.name: "test_value" for p in tool.parameters if p.required}
result = await provider.execute_tool(tool.name, minimal_params)
```

#### Performance issues

**Symptoms:** Slow tool responses, timeouts

**Solutions:**
- Increase timeout values in configuration
- Check network latency for remote servers
- Monitor server resource usage
- Use debug UI to identify bottlenecks

```yaml
# Increase timeouts
config:
  timeout: 120.0  # Increase from default 60 seconds
  servers:
    - name: slow_server
      transport: sse
      url: "https://slow-api.example.com/mcp"
```

### Debug UI features

The debug UI at [`http://localhost:9001`](http://localhost:9001) provides:

#### Event trace viewer
- Real-time display of all tool-related events
- Expandable event details with full context
- Filtering by event type or tool name
- Export capabilities for offline analysis

Access these features by navigating to the debug UI after starting your development server with [`uv run xaibo dev`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/cli/__init__.py:272).