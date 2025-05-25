# How to create and integrate Python tools

This guide shows you how to create custom Python functions and make them available as tools for your Xaibo agents.

## Create a Python tool function

Create a new Python file in your project's `tools/` directory:

```python
# tools/my_tools.py
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    """Gets the current time in UTC"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def calculate_sum(numbers: list[float]) -> float:
    """Calculates the sum of a list of numbers"""
    return sum(numbers)

@tool
def format_text(text: str, style: str = "uppercase") -> str:
    """Formats text according to the specified style
    
    Args:
        text: The text to format
        style: Format style - 'uppercase', 'lowercase', or 'title'
    """
    if style == "uppercase":
        return text.upper()
    elif style == "lowercase":
        return text.lower()
    elif style == "title":
        return text.title()
    else:
        return text
```

## Add tools to your agent configuration

Configure your agent to use the Python tool provider:

```yaml
# agents/my_agent.yml
id: my-agent
description: An agent with custom Python tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.my_tools]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to custom tools.
        Use the available tools to help users with their requests.
```

## Test your tools

Start your agent and test the tools:

```bash
# Start the development server
uv run xaibo dev

# Test with curl
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-agent",
    "messages": [
      {"role": "user", "content": "What time is it now?"}
    ]
  }'
```

## Add tools with complex parameters

Create tools that accept structured data:

```python
# tools/advanced_tools.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from xaibo.primitives.modules.tools.python_tool_provider import tool

@dataclass
class Person:
    name: str
    age: int
    email: Optional[str] = None

@tool
def create_person_profile(name: str, age: int, email: str = None) -> Dict:
    """Creates a person profile with the given information
    
    Args:
        name: Person's full name
        age: Person's age in years
        email: Optional email address
    """
    profile = {
        "name": name,
        "age": age,
        "profile_id": f"{name.lower().replace(' ', '_')}_{age}"
    }
    if email:
        profile["email"] = email
    return profile

@tool
def search_database(query: str, filters: Dict = None, limit: int = 10) -> List[Dict]:
    """Searches a mock database with optional filters
    
    Args:
        query: Search query string
        filters: Optional dictionary of filter criteria
        limit: Maximum number of results to return
    """
    # Mock implementation
    results = [
        {"id": 1, "title": f"Result for '{query}'", "score": 0.95},
        {"id": 2, "title": f"Another match for '{query}'", "score": 0.87}
    ]
    
    if filters:
        # Apply mock filtering logic
        results = [r for r in results if r["score"] >= filters.get("min_score", 0)]
    
    return results[:limit]
```

## Handle errors in tools

Add proper error handling to your tools:

```python
# tools/robust_tools.py
import requests
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def fetch_weather(city: str) -> Dict:
    """Fetches weather information for a city
    
    Args:
        city: Name of the city
    """
    try:
        # Mock API call (replace with real weather API)
        if not city or len(city.strip()) == 0:
            raise ValueError("City name cannot be empty")
        
        # Simulate API response
        weather_data = {
            "city": city,
            "temperature": "22°C",
            "condition": "Sunny",
            "humidity": "65%"
        }
        return weather_data
    
    except ValueError as e:
        return {"error": f"Invalid input: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch weather: {str(e)}"}

@tool
def validate_email(email: str) -> Dict:
    """Validates an email address format
    
    Args:
        email: Email address to validate
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    is_valid = bool(re.match(pattern, email))
    
    return {
        "email": email,
        "is_valid": is_valid,
        "message": "Valid email format" if is_valid else "Invalid email format"
    }
```

## Use multiple tool packages

Configure multiple tool packages in your agent:

```yaml
# agents/multi_tool_agent.yml
id: multi-tool-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: 
        - tools.my_tools
        - tools.advanced_tools
        - tools.robust_tools
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

## Add tools from external packages

Use tools from installed Python packages:

```python
# tools/external_tools.py
import json
import base64
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def encode_base64(text: str) -> str:
    """Encodes text to base64"""
    return base64.b64encode(text.encode()).decode()

@tool
def decode_base64(encoded: str) -> str:
    """Decodes base64 text"""
    try:
        return base64.b64decode(encoded.encode()).decode()
    except Exception as e:
        return f"Error decoding: {str(e)}"

@tool
def format_json(data: str) -> str:
    """Formats JSON string with proper indentation"""
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
```

## Best practices

### Tool documentation
- Always include clear docstrings with parameter descriptions
- Use type hints for better tool schema generation
- Document expected return formats

### Error handling
- Validate input parameters
- Return structured error information
- Don't let exceptions crash the agent

### Tool naming
- Use descriptive function names
- Group related tools in the same module
- Avoid name conflicts between packages

### Performance
- Keep tools lightweight and fast
- Use async functions for I/O operations when needed
- Cache expensive computations when appropriate

## Troubleshooting

### Tools not appearing
- Verify the tool package is listed in `tool_packages`
- Check that functions have the `@tool` decorator
- Ensure the Python module can be imported

### Import errors
- Make sure all dependencies are installed
- Check Python path includes your tools directory
- Verify module names match file names

### Tool execution errors
- Add logging to your tool functions
- Check the agent debug UI for detailed error messages
- Test tools independently before integrating

## Debug and troubleshoot tools

Use Xaibo's built-in debugging capabilities to diagnose tool discovery, import, and execution issues.

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
# debug_python_tools.py
import asyncio
from xaibo.primitives.modules.tools.python_tool_provider import PythonToolProvider

async def debug_python_tools():
    """Debug Python tool discovery and availability"""
    config = {
        "tool_packages": ["tools.my_tools", "tools.advanced_tools"]
    }
    
    provider = PythonToolProvider(config=config)
    
    try:
        # List all available tools
        tools = await provider.list_tools()
        
        print(f"Found {len(tools)} Python tools:")
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

if __name__ == "__main__":
    asyncio.run(debug_python_tools())
```

### Step-by-step debugging procedure

Follow these steps to diagnose Python tool issues:

#### 1. Verify tool package imports

Test if your tool packages can be imported correctly:

```python
# Test package imports
try:
    import tools.my_tools
    print("✓ tools.my_tools imported successfully")
    
    # Check for tool functions
    tool_functions = [obj for obj in tools.my_tools.__dict__.values()
                     if hasattr(obj, "__xaibo_tool__")]
    print(f"✓ Found {len(tool_functions)} tool functions")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
```

#### 2. Check tool discovery

Use the debug script to verify tools are discovered:

```python
# Check if tools are found
tools = await provider.list_tools()
if not tools:
    print("No tools discovered - check package configuration")
else:
    print(f"Discovered {len(tools)} tools")
    for tool in tools:
        print(f"  - {tool.name} from {tool.description}")
```

#### 3. Test tool execution

Execute a simple tool to verify functionality:

```python
# Test tool execution
try:
    result = await provider.execute_tool("current_time", {})
    print(f"Tool executed successfully: {result}")
except Exception as e:
    print(f"Tool execution failed: {e}")
    import traceback
    traceback.print_exc()
```

#### 4. Monitor with debug UI

1. Start your agent with debug UI enabled
2. Navigate to [`http://localhost:9001`](http://localhost:9001)
3. Trigger tool operations through your agent
4. Review the event trace for errors or performance issues

### Common troubleshooting scenarios

#### Tools not discovered

**Symptoms:** [`list_tools()`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/tools.py:9) returns empty list

**Solutions:**
- Verify package names in `tool_packages` configuration
- Check that functions have the [`@tool`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/python_tool_provider.py:12) decorator
- Ensure packages can be imported from Python path
- Test imports manually

```python
# Verify tool package configuration
config = {
    "tool_packages": [
        "tools.my_tools",      # Check this path
        "tools.advanced_tools" # Verify this exists
    ]
}

# Test manual import
try:
    import tools.my_tools
    print("Package imports successfully")
except ImportError as e:
    print(f"Import error: {e}")
```

#### Import errors

**Symptoms:** ModuleNotFoundError, ImportError exceptions

**Solutions:**
- Ensure all dependencies are installed
- Check Python path includes your tools directory
- Verify module names match file names
- Add `__init__.py` files to make directories packages

```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Verify package structure
ls -la tools/
# Should show:
# __init__.py
# my_tools.py
# advanced_tools.py

# Test import manually
python -c "import tools.my_tools; print('Import successful')"
```

#### Missing @tool decorator

**Symptoms:** Functions exist but not discovered as tools

**Solutions:**
- Add [`@tool`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/python_tool_provider.py:12) decorator to functions
- Import decorator from correct module
- Verify decorator is applied before function definition

```python
# Correct tool definition
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool  # This decorator is required
def my_function():
    """Function description"""
    return "result"

# Check if function is marked as tool
print(hasattr(my_function, "__xaibo_tool__"))  # Should be True
```

#### Tool execution errors

**Symptoms:** Tools discovered but execution fails

**Solutions:**
- Check function parameter types and names
- Verify return values are JSON-serializable
- Add proper error handling to tool functions
- Test functions independently

```python
# Debug tool parameters
tool = tools[0]  # Get first tool
print(f"Tool name: {tool.name}")
print(f"Required parameters: {[p.name for p in tool.parameters if p.required]}")
print(f"Optional parameters: {[p.name for p in tool.parameters if not p.required]}")

# Test with correct parameters
try:
    # Use actual parameter names from tool definition
    params = {"text": "hello", "style": "uppercase"}  # Example
    result = await provider.execute_tool(tool.name, params)
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
```

#### Type annotation issues

**Symptoms:** Tool schema generation fails, parameter validation errors

**Solutions:**
- Add proper type hints to function parameters
- Use supported types (str, int, float, bool, list, dict)
- Provide default values for optional parameters
- Include comprehensive docstrings

```python
# Good type annotations
@tool
def process_data(
    text: str,                    # Required string parameter
    count: int = 1,              # Optional with default
    options: dict = None,        # Optional complex type
    enabled: bool = True         # Optional boolean
) -> dict:                       # Return type annotation
    """Process text data with options
    
    Args:
        text: Input text to process
        count: Number of times to process (default: 1)
        options: Additional processing options
        enabled: Whether processing is enabled
        
    Returns:
        Dictionary with processing results
    """
    if options is None:
        options = {}
    
    return {
        "processed_text": text * count,
        "options_used": options,
        "was_enabled": enabled
    }
```

### Debug UI features

The debug UI at [`http://localhost:9001`](http://localhost:9001) provides:

#### Event trace viewer
- Real-time display of all tool-related events
- Expandable event details with full context
- Filtering by event type or tool name
- Export capabilities for offline analysis

Access these features by navigating to the debug UI after starting your development server with [`uv run xaibo dev`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/cli/__init__.py:272).