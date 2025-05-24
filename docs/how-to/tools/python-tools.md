# How to create and integrate Python tools

This guide shows you how to create custom Python functions and make them available as tools for your Xaibo agents.

## Create a Python tool function

1. Create a new Python file in your project's `tools/` directory:

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

2. Configure your agent to use the Python tool provider:

```yaml
# agents/my_agent.yml
id: my-agent
description: An agent with custom Python tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
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

3. Start your agent and test the tools:

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

4. Create tools that accept structured data:

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

5. Add proper error handling to your tools:

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

6. Configure multiple tool packages in your agent:

```yaml
# agents/multi_tool_agent.yml
id: multi-tool-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
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

7. Use tools from installed Python packages:

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