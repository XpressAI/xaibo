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

## OneShotTools

Provides LLM-based tools defined with conversation templates and parameter injection.

**Source**: [`src/xaibo/primitives/modules/tools/oneshot.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/oneshot.py)

**Module Path**: `xaibo.primitives.modules.tools.OneShotTools`

**Dependencies**: None

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md), Uses [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | `List[OneShotTool]` | List of one-shot tool definitions |

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | LLM provider for tool execution |

### Tool Definition Structure

Each tool in the `tools` list requires:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique tool identifier |
| `description` | `str` | Tool description for LLM context |
| `parameters` | `List[OneShotToolParameter]` | Input parameters |
| `returns` | `OneShotToolReturn` | Return type specification |
| `conversation` | `List[OneShotToolConversationEntry]` | Conversation template |

### Parameter Definition

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Parameter name |
| `type` | `str` | Parameter type (string, integer, etc.) |
| `description` | `str` | Parameter description |

### Return Type Definition

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Expected return type |
| `description` | `str` | Return value description |

### Conversation Entry Structure

| Field | Type | Description |
|-------|------|-------------|
| `role` | `LLMRole` | Message role (user, assistant, system) |
| `message` | `List[OneShotToolConversationMessage]` | Message content |

### Message Types

| Type | Description | Fields |
|------|-------------|--------|
| `text` | Text content with parameter injection | `text` |
| `image_url` | Image content from URL or file path | `url` |

### Parameter Injection

Parameters are injected into conversation templates using the syntax `$$params.parameter_name$$`:

```yaml
conversation:
  - role: user
    message:
      - type: text
        text: "Analyze this image: $$params.image_path$$"
      - type: image_url
        url: "$$params.image_path$$"
```

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAIProvider
    id: vision-llm
    config:
      model: "gpt-4.1"
  
  - module: xaibo.primitives.modules.tools.OneShotTools
    id: vision-tools
    config:
      tools:
        - name: extract_text_from_image
          description: "Extract text content from an image using OCR"
          parameters:
            - name: image_path
              type: string
              description: "Path to the image file"
          returns:
            type: string
            description: "Extracted text content"
          conversation:
            - role: user
              message:
                - type: text
                  text: "Please extract all text from this image and return it as plain text:"
                - type: image_url
                  url: "$$params.image_path$$"
        
        - name: analyze_chart_data
          description: "Extract structured data from charts and graphs"
          parameters:
            - name: chart_image
              type: string
              description: "Path to chart image file"
            - name: data_format
              type: string
              description: "Desired output format (json, csv, table)"
          returns:
            type: string
            description: "Structured data in requested format"
          conversation:
            - role: user
              message:
                - type: text
                  text: "Analyze this chart and extract the data in $$params.data_format$$ format:"
                - type: image_url
                  url: "$$params.chart_image$$"

exchange:
  - module: vision-tools
    protocol: ToolProviderProtocol
    provider: vision-llm
```

### Use Cases

- **OCR Processing**: Extract text from images using vision-capable LLMs
- **Document Analysis**: Analyze document structure and content
- **Data Extraction**: Extract structured data from charts, tables, forms
- **Image Classification**: Classify images into categories
- **Content Moderation**: Analyze images for policy compliance
- **Visual Question Answering**: Answer questions about image content

### Features

- **Template-Based**: Define tools using conversation templates
- **Parameter Injection**: Dynamic parameter substitution in prompts
- **Multi-Modal Support**: Supports both text and image inputs
- **Vision Integration**: Works with vision-capable LLMs
- **File Path Handling**: Automatic conversion of file paths to base64 data URIs
- **Flexible Prompting**: Full control over LLM conversation structure

## TextBasedToolCallAdapter

Wraps LLM providers to enable tool calling for LLMs without native function calling support by converting tool definitions to text prompts and parsing tool calls from response content.

**Source**: [`src/xaibo/primitives/modules/tools/no_function_calling_adapter.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/no_function_calling_adapter.py)

**Module Path**: `xaibo.primitives.modules.tools.TextBasedToolCallAdapter`

**Dependencies**: None

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md), Uses [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | `{}` | Optional configuration dictionary (currently unused) |

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | The underlying LLM provider to wrap |

### Tool Call Format

The adapter instructs LLMs to use a specific text format for tool calls:

```
TOOL: tool_name {"parameter": "value", "other_param": 123}
```

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAIProvider
    id: base-llm
    config:
      model: "gpt-4.1-nano"
  
  - module: xaibo.primitives.modules.tools.TextBasedToolCallAdapter
    id: text-based-llm

exchange:
  - module: text-based-llm
    protocol: LLMProtocol
    provider: base-llm
```

### Tool Prompt Generation

The adapter automatically generates tool descriptions and injects them into the conversation. The format includes:

- Tool name and description
- Parameter details with type and requirement information
- Usage instructions with the "TOOL:" prefix format
- Example usage

Example generated prompt:
```
Available tools:

get_weather: Get the current weather in a given location
Parameters:
  - location (required): The city and state, e.g. San Francisco, CA
  - unit: The temperature unit to use (celsius or fahrenheit)

To use a tool, write TOOL: followed by the tool name and JSON arguments on a single line.
Whenever you say 'I will now...' , you must follow that up with the appropriate TOOL: invocation.
Example: TOOL: get_weather {"location": "San Francisco, CA"}
```

### Tool Call Parsing

The adapter parses tool calls from LLM responses by:

1. Scanning response content line by line for "TOOL:" prefix
2. Extracting tool name and JSON arguments
3. Creating [`LLMFunctionCall`](../protocols/llm.md) objects with unique IDs
4. Handling malformed JSON by falling back to raw input
5. Removing tool call lines from the final response content

### Message Processing

The adapter modifies input messages by:

- Adding tool descriptions to existing system messages
- Creating a new system message if none exists
- Preserving all other message content and metadata
- Removing function definitions from [`LLMOptions`](../protocols/llm.md) to avoid duplication

### Features

- **Text-Based Tool Calling**: Converts function calling to text-based instructions
- **Automatic Tool Prompt Injection**: Adds tool descriptions to system messages
- **Tool Call Parsing**: Extracts tool calls from LLM responses using "TOOL:" prefix
- **Streaming Support**: Supports both regular and streaming generation modes (note: tool call detection not supported in streaming)
- **Error Handling**: Gracefully handles malformed JSON in tool arguments
- **Content Cleaning**: Removes tool call lines from final response content
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

### LLM-Based Vision Tools

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAIProvider
    id: vision-llm
    config:
      model: "gpt-4.1"
  
  - module: xaibo.primitives.modules.tools.OneShotTools
    id: vision-tools
    config:
      tools:
        - name: document_ocr
          description: "Extract text from document images"
          parameters:
            - name: document_path
              type: string
              description: "Path to document image"
          returns:
            type: string
            description: "Extracted text content"
          conversation:
            - role: user
              message:
                - type: text
                  text: "Extract all text from this document:"
                - type: image_url
                  url: "$$params.document_path$$"
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