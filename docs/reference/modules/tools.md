# Tool Modules Reference

Tool modules provide implementations of the [`ToolProviderProtocol`](../protocols/tools.md) for different tool sources. They handle tool discovery, parameter validation, and execution across various tool types.

## PythonToolProvider

Converts Python functions into tools using the `@tool` decorator.

**Source**: [`src/xaibo/primitives/modules/tools/python_tool_provider.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/python_tool_provider.py)

**Module Path**: `xaibo.primitives.modules.tools.PythonToolProvider`

**Dependencies**: `docstring_parser` (core dependency)

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_packages` | `List[str]` | `[]` | List of Python package paths containing tool functions |
| `tool_functions` | `List[Callable]` | `[]` | Optional list of function objects to use as tools |

### Tool Decorator

The `@tool` decorator converts Python functions into Xaibo tools:

```python
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    """Returns the current time in UTC"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def get_weather(city: str, units: str = "celsius") -> dict:
    """Get weather information for a city
    
    Args:
        city: Name of the city
        units: Temperature units (celsius, fahrenheit, kelvin)
    
    Returns:
        Weather information dictionary
    """
    # Implementation here
    return {"temperature": 22, "conditions": "sunny"}
```

### Parameter Type Mapping

| Python Type | Tool Parameter Type | Description |
|-------------|-------------------|-------------|
| `str` | `string` | Text values |
| `int` | `integer` | Integer numbers |
| `float` | `number` | Floating point numbers |
| `bool` | `boolean` | Boolean values |
| `dict` | `object` | JSON objects |
| `list` | `array` | JSON arrays |
| `Union[str, None]` | `string` (optional) | Optional string |
| `Optional[int]` | `integer` (optional) | Optional integer |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages:
        - tools.weather
        - tools.calendar
        - tools.filesystem
```

### Tool Package Structure

```
tools/
├── __init__.py
├── weather.py          # Weather-related tools
├── calendar.py         # Calendar tools
└── filesystem.py       # File operations
```

Example tool package (`tools/weather.py`):

```python
from xaibo.primitives.modules.tools.python_tool_provider import tool
import requests

@tool
def get_current_weather(city: str, units: str = "celsius") -> dict:
    """Get current weather for a city
    
    Args:
        city: Name of the city to get weather for
        units: Temperature units (celsius, fahrenheit, kelvin)
    
    Returns:
        Current weather information
    """
    # API call implementation
    response = requests.get(f"https://api.weather.com/v1/current", 
                          params={"city": city, "units": units})
    return response.json()

@tool
def get_weather_forecast(city: str, days: int = 5) -> list:
    """Get weather forecast for multiple days
    
    Args:
        city: Name of the city
        days: Number of days to forecast (1-10)
    
    Returns:
        List of daily weather forecasts
    """
    if not 1 <= days <= 10:
        raise ValueError("Days must be between 1 and 10")
    
    # Implementation here
    return [{"date": f"2024-01-{i+1}", "temp": 20+i} for i in range(days)]
```

### Features

- **Automatic Discovery**: Scans packages for `@tool` decorated functions
- **Type Inference**: Automatically infers parameter types from annotations
- **Docstring Parsing**: Extracts descriptions from function docstrings
- **Error Handling**: Converts Python exceptions to tool errors
- **Validation**: Validates parameters before function execution

## MCPToolProvider

Connects to MCP (Model Context Protocol) servers to provide their tools.

**Source**: [`src/xaibo/primitives/modules/tools/mcp_tool_provider.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/mcp_tool_provider.py)

**Module Path**: `xaibo.primitives.modules.tools.MCPToolProvider`

**Dependencies**: `aiohttp`, `websockets` (core dependencies)

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `servers` | `List[dict]` | Required | List of MCP server configurations |
| `timeout` | `float` | `30.0` | Timeout for server operations in seconds |

### Server Configuration

Each server in the `servers` list requires:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Unique identifier for the server |
| `transport` | `str` | Yes | Transport type: "stdio", "sse", or "websocket" |

#### STDIO Transport

For local process-based MCP servers:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `command` | `List[str]` | `[]` | Command and arguments to start the server |
| `args` | `List[str]` | `[]` | Additional arguments |
| `env` | `Dict[str, str]` | `{}` | Environment variables |

#### SSE Transport

For HTTP Server-Sent Events based servers:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | `str` | `""` | Server URL |
| `headers` | `Dict[str, str]` | `{}` | HTTP headers for authentication |

#### WebSocket Transport

For WebSocket-based servers:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | `str` | `""` | WebSocket URL |
| `headers` | `Dict[str, str]` | `{}` | HTTP headers for connection |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 60.0
      servers:
        # Local filesystem server
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]
          env:
            LOG_LEVEL: "INFO"
        
        # Remote web search server
        - name: web_search
          transport: sse
          url: "https://api.example.com/mcp"
          headers:
            Authorization: "Bearer your-api-key"
            Content-Type: "application/json"
        
        # WebSocket database server
        - name: database
          transport: websocket
          url: "ws://localhost:8080/mcp"
          headers:
            X-API-Key: "your-websocket-key"
```

### Tool Namespacing

Tools from MCP servers are namespaced with the server name:

```
filesystem.read_file
filesystem.write_file
web_search.search
web_search.get_page
database.query
database.insert
```

### Features

- **Multiple Transports**: Supports stdio, SSE, and WebSocket transports
- **Connection Management**: Automatic connection establishment and recovery
- **Tool Caching**: Caches tool definitions for performance
- **Error Handling**: Robust error handling for network issues
- **Concurrent Servers**: Supports multiple servers simultaneously

## ToolCollector

Aggregates tools from multiple tool providers.

**Source**: [`src/xaibo/primitives/modules/tools/tool_collector.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/tool_collector.py)

**Module Path**: `xaibo.primitives.modules.tools.ToolCollector`

**Dependencies**: None

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md), Uses [`ToolProviderProtocol`](../protocols/tools.md) (list)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `providers` | `List[ToolProviderProtocol]` | List of tool providers to aggregate |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.weather]
  
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
  
  - module: xaibo.primitives.modules.tools.ToolCollector
    id: all-tools

exchange:
  - module: all-tools
    protocol: ToolProviderProtocol
    provider: [python-tools, mcp-tools]
```

### Features

- **Tool Aggregation**: Combines tools from multiple providers
- **Name Conflict Resolution**: Handles duplicate tool names
- **Provider Routing**: Routes tool execution to correct provider
- **Unified Interface**: Presents single interface for all tools

## OneshotToolProvider

Executes tools once and caches results.

**Source**: [`src/xaibo/primitives/modules/tools/oneshot.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/oneshot.py)

**Module Path**: `xaibo.primitives.modules.tools.OneshotToolProvider`

**Dependencies**: None

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md), Uses [`ToolProviderProtocol`](../protocols/tools.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_duration` | `int` | `3600` | Cache duration in seconds |
| `max_cache_size` | `int` | `1000` | Maximum number of cached results |

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `provider` | `ToolProviderProtocol` | Underlying tool provider |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: base-tools
    config:
      tool_packages: [tools.expensive_operations]
  
  - module: xaibo.primitives.modules.tools.OneshotToolProvider
    id: cached-tools
    config:
      cache_duration: 1800  # 30 minutes
      max_cache_size: 500

exchange:
  - module: cached-tools
    protocol: ToolProviderProtocol
    provider: base-tools
```

### Features

- **Result Caching**: Caches tool execution results
- **TTL Support**: Configurable time-to-live for cache entries
- **Memory Management**: LRU eviction for cache size limits
- **Cache Keys**: Intelligent cache key generation

## NoFunctionCallingAdapter

Adapts tool providers for LLMs without native function calling support.

**Source**: [`src/xaibo/primitives/modules/tools/no_function_calling_adapter.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/no_function_calling_adapter.py)

**Module Path**: `xaibo.primitives.modules.tools.NoFunctionCallingAdapter`

**Dependencies**: None

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md), Uses [`ToolProviderProtocol`](../protocols/tools.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_format` | `str` | `"json"` | Format for tool descriptions ("json", "xml", "markdown") |
| `include_examples` | `bool` | `True` | Include usage examples in descriptions |

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `provider` | `ToolProviderProtocol` | Underlying tool provider |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: base-tools
    config:
      tool_packages: [tools.weather]
  
  - module: xaibo.primitives.modules.tools.NoFunctionCallingAdapter
    id: text-tools
    config:
      tool_format: "markdown"
      include_examples: true

exchange:
  - module: text-tools
    protocol: ToolProviderProtocol
    provider: base-tools
```

### Features

- **Text-Based Tools**: Converts tools to text descriptions
- **Multiple Formats**: Supports JSON, XML, and Markdown formats
- **Usage Examples**: Generates example usage for each tool
- **LLM Integration**: Works with LLMs that don't support function calling

## Common Configuration Patterns

### Multi-Source Tool Setup

```yaml
modules:
  # Python tools for custom functions
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.custom, tools.utilities]
  
  # MCP tools for external services
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
        - name: web
          transport: sse
          url: "https://api.example.com/mcp"
  
  # Aggregate all tools
  - module: xaibo.primitives.modules.tools.ToolCollector
    id: all-tools

exchange:
  - module: all-tools
    protocol: ToolProviderProtocol
    provider: [python-tools, mcp-tools]
```

### Cached Expensive Operations

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: expensive-tools
    config:
      tool_packages: [tools.ai_analysis, tools.data_processing]
  
  - module: xaibo.primitives.modules.tools.OneshotToolProvider
    id: cached-expensive-tools
    config:
      cache_duration: 3600  # 1 hour
      max_cache_size: 100

exchange:
  - module: cached-expensive-tools
    protocol: ToolProviderProtocol
    provider: expensive-tools
```

### Development vs Production Tools

```yaml
# Development configuration
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.development, tools.testing]

# Production configuration
modules:
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: tools
    config:
      servers:
        - name: production_api
          transport: sse
          url: "https://prod-api.example.com/mcp"
          headers:
            Authorization: "Bearer ${PROD_API_KEY}"
```

## Error Handling

Tool modules handle various error scenarios:

### Tool Discovery Errors

```python
# Package not found
ToolError: "Package 'tools.nonexistent' not found"

# No tools found
ToolError: "No tools found in package 'tools.empty'"
```

### Execution Errors

```python
# Tool not found
ToolNotFoundError: "Tool 'nonexistent_tool' not found"

# Parameter validation
ToolParameterError: "Required parameter 'city' not provided"

# Execution failure
ToolExecutionError: "Tool execution failed: Connection timeout"
```

### MCP Server Errors

```python
# Connection failure
MCPConnectionError: "Failed to connect to MCP server 'filesystem'"

# Protocol error
MCPProtocolError: "Invalid MCP response from server"

# Server timeout
MCPTimeoutError: "MCP server 'web_search' timed out after 30 seconds"
```

## Performance Considerations

### Tool Loading

1. **Lazy Loading**: Load tools on first access
2. **Caching**: Cache tool definitions and schemas
3. **Parallel Loading**: Load from multiple sources concurrently
4. **Error Recovery**: Handle individual tool failures gracefully

### Execution Optimization

1. **Connection Pooling**: Reuse connections for MCP servers
2. **Batch Operations**: Group related tool calls when possible
3. **Timeout Management**: Set appropriate timeouts for different tools
4. **Resource Limits**: Implement memory and CPU limits

### Monitoring

1. **Execution Metrics**: Track tool usage and performance
2. **Error Rates**: Monitor tool failure rates
3. **Cache Hit Rates**: Monitor cache effectiveness
4. **Resource Usage**: Track memory and CPU usage

## Security Considerations

### Python Tools

1. **Code Review**: Review all tool functions for security
2. **Input Validation**: Validate all tool parameters
3. **Sandboxing**: Consider running tools in sandboxed environments
4. **Permission Checks**: Implement appropriate permission checks

### MCP Servers

1. **Authentication**: Use proper authentication for MCP servers
2. **Network Security**: Secure network connections (TLS/SSL)
3. **Input Sanitization**: Sanitize inputs before sending to servers
4. **Rate Limiting**: Implement rate limiting for external servers

### General

1. **Principle of Least Privilege**: Grant minimal necessary permissions
2. **Audit Logging**: Log all tool executions for audit trails
3. **Error Information**: Avoid exposing sensitive information in errors
4. **Resource Limits**: Implement appropriate resource limits