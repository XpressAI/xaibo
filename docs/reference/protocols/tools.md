# Tools Protocol Specification

The Tools Protocol defines the interface for tool providers in Xaibo agents. It standardizes tool discovery, execution, and result handling across different tool implementations.

**Source**: [`src/xaibo/core/protocols/tools.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/tools.py)

## ToolProviderProtocol

The core protocol interface for tool provider implementations.

```python
@runtime_checkable
class ToolProviderProtocol(Protocol):
    """Protocol for providing and executing tools"""
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools provided by this provider"""
        ...
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool with the given parameters"""
        ...
```

### Methods

---

#### `list_tools() -> List[Tool]`

Retrieve all tools available from this provider.

**Returns:**

- `List[Tool]`: List of tool definitions with names, descriptions, and parameter schemas

**Example:**
```python
tools = await tool_provider.list_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
    for param_name, param in tool.parameters.items():
        print(f"  {param_name} ({param.type}): {param.description}")
```

---

#### `execute_tool(tool_name: str, parameters: Dict[str, Any]) -> ToolResult`

Execute a specific tool with provided parameters.

**Parameters:**

- `tool_name` (`str`, required): Name of the tool to execute
- `parameters` (`Dict[str, Any]`, required): Tool parameters as key-value pairs

**Returns:**

- `ToolResult`: Execution result with success status, result data, or error information

**Raises:**

- `ToolNotFoundError`: If the specified tool is not available
- `ToolExecutionError`: If tool execution fails

**Example:**
```python
result = await tool_provider.execute_tool(
    "get_weather", 
    {"city": "Paris", "units": "metric"}
)

if result.success:
    print(f"Weather data: {result.result}")
else:
    print(f"Error: {result.error}")
```

---


## Data Models

### Tool

Definition of an executable tool with its interface specification.

**Source**: [`src/xaibo/core/models/tools.py:15`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/tools.py#L15)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Unique identifier for the tool |
| `description` | `str` | Yes | Human-readable description of tool functionality |
| `parameters` | `Dict[str, ToolParameter]` | No | Parameter definitions (default: empty dict) |

#### Example

```python
tool = Tool(
    name="get_weather",
    description="Get current weather information for a city",
    parameters={
        "city": ToolParameter(
            type="string",
            description="Name of the city",
            required=True
        ),
        "units": ToolParameter(
            type="string",
            description="Temperature units",
            required=False,
            default="celsius",
            enum=["celsius", "fahrenheit", "kelvin"]
        )
    }
)
```

### ToolParameter

Parameter definition for tool inputs.

**Source**: [`src/xaibo/core/models/tools.py:6`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/tools.py#L6)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `str` | Yes | Parameter type (string, number, boolean, object, array) |
| `description` | `str` | No | Human-readable parameter description |
| `required` | `bool` | No | Whether parameter is required (default: False) |
| `default` | `Any` | No | Default value if parameter not provided |
| `enum` | `List[str]` | No | List of allowed values for string parameters |

#### Supported Types

| Type | Description | Example Values |
|------|-------------|----------------|
| `string` | Text values | `"hello"`, `"world"` |
| `number` | Numeric values | `42`, `3.14`, `-10` |
| `integer` | Integer values | `42`, `-10`, `0` |
| `boolean` | Boolean values | `true`, `false` |
| `object` | JSON objects | `{"key": "value"}` |
| `array` | JSON arrays | `[1, 2, 3]`, `["a", "b"]` |

#### Example

```python
param = ToolParameter(
    type="string",
    description="The city name to get weather for",
    required=True
)

enum_param = ToolParameter(
    type="string",
    description="Temperature units",
    required=False,
    default="celsius",
    enum=["celsius", "fahrenheit", "kelvin"]
)

number_param = ToolParameter(
    type="number",
    description="Maximum temperature threshold",
    required=False,
    default=30.0
)
```

### ToolResult

Result of tool execution with success status and data.

**Source**: [`src/xaibo/core/models/tools.py:22`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/tools.py#L22)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | `bool` | Yes | Whether the tool execution succeeded |
| `result` | `Any` | No | Tool execution result data (if successful) |
| `error` | `str` | No | Error message (if execution failed) |

#### Success Result

```python
result = ToolResult(
    success=True,
    result={
        "temperature": 22.5,
        "humidity": 65,
        "conditions": "partly cloudy"
    }
)
```

#### Error Result

```python
result = ToolResult(
    success=False,
    error="City 'InvalidCity' not found"
)
```

## Implementation Example


```python
from xaibo.core.protocols.tools import ToolProviderProtocol
from xaibo.core.models.tools import Tool, ToolParameter, ToolResult
import asyncio
import json

class WeatherToolProvider:
    """Example tool provider for weather information"""
    
    def __init__(self, config: dict):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.weather.com")
    
    async def list_tools(self) -> List[Tool]:
        """Return available weather tools"""
        return [
            Tool(
                name="get_current_weather",
                description="Get current weather conditions for a city",
                parameters={
                    "city": ToolParameter(
                        type="string",
                        description="City name",
                        required=True
                    ),
                    "units": ToolParameter(
                        type="string",
                        description="Temperature units",
                        required=False,
                        default="celsius",
                        enum=["celsius", "fahrenheit", "kelvin"]
                    )
                }
            ),
            Tool(
                name="get_weather_forecast",
                description="Get weather forecast for multiple days",
                parameters={
                    "city": ToolParameter(
                        type="string",
                        description="City name",
                        required=True
                    ),
                    "days": ToolParameter(
                        type="integer",
                        description="Number of days to forecast",
                        required=False,
                        default=5
                    )
                }
            )
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a weather tool"""
        try:
            if tool_name == "get_current_weather":
                return await self._get_current_weather(parameters)
            elif tool_name == "get_weather_forecast":
                return await self._get_weather_forecast(parameters)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
    async def _get_current_weather(self, parameters: Dict[str, Any]) -> ToolResult:
        """Get current weather for a city"""
        city = parameters.get("city")
        units = parameters.get("units", "celsius")
        
        if not city:
            return ToolResult(
                success=False,
                error="City parameter is required"
            )
        
        # Simulate API call
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Mock weather data
        weather_data = {
            "city": city,
            "temperature": 22.5 if units == "celsius" else 72.5,
            "units": units,
            "humidity": 65,
            "conditions": "partly cloudy",
            "wind_speed": 10
        }
        
        return ToolResult(
            success=True,
            result=weather_data
        )
    
    async def _get_weather_forecast(self, parameters: Dict[str, Any]) -> ToolResult:
        """Get weather forecast for a city"""
        city = parameters.get("city")
        days = parameters.get("days", 5)
        
        if not city:
            return ToolResult(
                success=False,
                error="City parameter is required"
            )
        
        # Simulate API call
        await asyncio.sleep(0.2)
        
        # Mock forecast data
        forecast = {
            "city": city,
            "forecast": [
                {
                    "date": f"2024-01-{i+1:02d}",
                    "high": 25 + i,
                    "low": 15 + i,
                    "conditions": "sunny" if i % 2 == 0 else "cloudy"
                }
                for i in range(days)
            ]
        }
        
        return ToolResult(
            success=True,
            result=forecast
        )

# Verify protocol compliance
assert isinstance(WeatherToolProvider({}), ToolProviderProtocol)
```

## Error Handling

Tool providers should handle errors gracefully and return appropriate ToolResult objects:

```python
class ToolError(Exception):
    """Base exception for tool errors"""
    pass

class ToolNotFoundError(ToolError):
    """Tool not found"""
    pass

class ToolExecutionError(ToolError):
    """Tool execution failed"""
    pass

class ToolParameterError(ToolError):
    """Invalid tool parameters"""
    pass

# Example error handling in execute_tool
async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
    try:
        # Validate tool exists
        tools = await self.list_tools()
        tool_names = [t.name for t in tools]
        if tool_name not in tool_names:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found. Available tools: {tool_names}"
            )
        
        # Validate parameters
        tool = next(t for t in tools if t.name == tool_name)
        validation_error = self._validate_parameters(tool, parameters)
        if validation_error:
            return ToolResult(
                success=False,
                error=validation_error
            )
        
        # Execute tool
        result = await self._execute_tool_impl(tool_name, parameters)
        return ToolResult(success=True, result=result)
        
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )
```

## Testing

Mock implementation for testing:

```python
class MockToolProvider:
    """Mock tool provider for testing"""
    
    def __init__(self, tools: List[Tool], results: Dict[str, Any]):
        self.tools = tools
        self.results = results
        self.call_history = []
    
    async def list_tools(self) -> List[Tool]:
        return self.tools
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        self.call_history.append((tool_name, parameters))
        
        if tool_name in self.results:
            result_data = self.results[tool_name]
            if isinstance(result_data, Exception):
                return ToolResult(success=False, error=str(result_data))
            else:
                return ToolResult(success=True, result=result_data)
        else:
            return ToolResult(success=False, error=f"Tool {tool_name} not mocked")

# Usage in tests
mock_tools = [
    Tool(name="test_tool", description="A test tool", parameters={})
]
mock_results = {
    "test_tool": {"message": "success"}
}

mock_provider = MockToolProvider(mock_tools, mock_results)
assert isinstance(mock_provider, ToolProviderProtocol)

# Test execution
result = await mock_provider.execute_tool("test_tool", {})
assert result.success
assert result.result == {"message": "success"}
```

## Integration with LLM Function Calling

Tools integrate with LLM function calling through the LLMOptions:

```python
# Get tools from provider
tools = await tool_provider.list_tools()

# Use in LLM options
options = LLMOptions(
    temperature=0.7,
    functions=tools  # Tools available for function calling
)

# Generate response with tools
response = await llm.generate(messages, options)

# Execute any tool calls
if response.tool_calls:
    for call in response.tool_calls:
        result = await tool_provider.execute_tool(call.name, call.arguments)
        # Add result to conversation history
        messages.append(LLMMessage.function_result(call.id, call.name, str(result.result)))
```

## Best Practices

### Tool Design

1. **Clear Names**: Use descriptive, action-oriented tool names
2. **Comprehensive Descriptions**: Explain what the tool does and when to use it
3. **Parameter Validation**: Validate all input parameters
4. **Error Handling**: Return meaningful error messages
5. **Idempotency**: Tools should be safe to call multiple times

### Parameter Definitions

1. **Type Safety**: Use appropriate parameter types
2. **Required Fields**: Mark required parameters explicitly
3. **Default Values**: Provide sensible defaults where possible
4. **Enums**: Use enums for limited choice parameters
5. **Documentation**: Include clear parameter descriptions

### Result Handling

1. **Consistent Format**: Use consistent result structures
2. **Success Indication**: Always indicate success/failure clearly
3. **Error Details**: Provide actionable error messages
4. **Serializable Results**: Ensure results can be JSON serialized
5. **Size Limits**: Keep results reasonably sized for LLM context