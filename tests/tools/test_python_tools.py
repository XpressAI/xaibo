import pytest

from xaibo.primitives.modules.tools.python_tool_provider import PythonToolProvider, tool


@pytest.fixture
def provider():
    """Create a PythonToolProvider with the mock package"""
    return PythonToolProvider({"tool_packages": ["xaibo_examples.demo_tools.test_tools"]})


@pytest.mark.asyncio
async def test_list_tools(provider):
    """Test listing available tools from the package"""
    tools = await provider.list_tools()
    
    # Should find two tools
    assert len(tools) == 2
    
    # Verify the first tool
    weather_tool = next(t for t in tools if t.name == "xaibo_examples-demo_tools-test_tools-sample_function")
    assert weather_tool.description.strip() == "Get the current weather in a given location"
    assert "location" in weather_tool.parameters
    assert weather_tool.parameters["location"].required is True
    assert "unit" in weather_tool.parameters
    assert weather_tool.parameters["unit"].required is False
    
    # Verify the second tool
    search_tool = next(t for t in tools if t.name == "xaibo_examples-demo_tools-test_tools-another_function")
    assert search_tool.description.strip() == "Search for information"
    assert "query" in search_tool.parameters


@pytest.mark.asyncio
async def test_execute_tool(provider):
    """Test executing a tool with parameters"""
    # Execute the weather tool
    result = await provider.execute_tool(
        "xaibo_examples-demo_tools-test_tools-sample_function", 
        {"location": "San Francisco", "unit": "fahrenheit"}
    )
    
    assert result.success is True
    assert result.result == "Weather in San Francisco is sunny and 25 degrees fahrenheit"
    
    # Execute with default parameter
    result = await provider.execute_tool(
        "xaibo_examples-demo_tools-test_tools-sample_function", 
        {"location": "San Francisco"}
    )
    
    assert result.success is True
    assert result.result == "Weather in San Francisco is sunny and 25 degrees celsius"


@pytest.mark.asyncio
async def test_execute_nonexistent_tool(provider):
    """Test executing a tool that doesn't exist"""
    result = await provider.execute_tool("nonexistent-tool", {})
    
    assert result.success is False
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_execute_tool_with_error(provider):
    """Test executing a tool that raises an exception"""
    # Missing required parameter should cause an error
    result = await provider.execute_tool("xaibo_examples-demo_tools-test_tools-sample_function", {})
    
    assert result.success is False
    assert "missing" in result.error.lower() or "required" in result.error.lower()


@pytest.mark.asyncio
async def test_direct_function_tools():
    """Test using directly provided functions as tools"""
    @tool
    def add_numbers(a: int, b: int):
        """Add two numbers together
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of the two numbers
        """
        return a + b
    
    @tool
    def greet(name: str, greeting: str = "Hello"):
        """Generate a greeting
        
        Args:
            name: Person to greet
            greeting: Greeting to use (default: Hello)
            
        Returns:
            Formatted greeting
        """
        return f"{greeting}, {name}!"
    
    provider = PythonToolProvider({"tool_functions": [add_numbers, greet]})
    
    # List tools
    tools = await provider.list_tools()
    assert len(tools) == 2
    
    # Verify tool definitions
    add_tool = next(t for t in tools if t.name.endswith("-add_numbers"))
    assert add_tool.description.strip() == "Add two numbers together"
    assert "a" in add_tool.parameters
    assert add_tool.parameters["a"].required is True
    assert add_tool.parameters["a"].type == "integer"
    
    greet_tool = next(t for t in tools if t.name.endswith("-greet"))
    assert greet_tool.description.strip() == "Generate a greeting"
    assert "name" in greet_tool.parameters
    assert greet_tool.parameters["name"].required is True
    assert "greeting" in greet_tool.parameters
    assert greet_tool.parameters["greeting"].required is False
    
    # Execute tools
    result = await provider.execute_tool(add_tool.name, {"a": 5, "b": 7})
    assert result.success is True
    assert result.result == 12
    
    result = await provider.execute_tool(greet_tool.name, {"name": "World"})
    assert result.success is True
    assert result.result == "Hello, World!"
    
    result = await provider.execute_tool(greet_tool.name, {"name": "World", "greeting": "Hi"})
    assert result.success is True
    assert result.result == "Hi, World!"


@pytest.mark.asyncio
async def test_unmarked_function_auto_marking():
    """Test that unmarked functions are automatically marked as tools"""
    def multiply(x: int, y: int):
        """Multiply two numbers
        
        Args:
            x: First number
            y: Second number
            
        Returns:
            Product of the two numbers
        """
        return x * y
    
    provider = PythonToolProvider({"tool_functions": [multiply]})
    
    # List tools
    tools = await provider.list_tools()
    assert len(tools) == 1
    
    # Verify the tool was marked and converted
    assert hasattr(multiply, "__xaibo_tool__")
    assert tools[0].name.endswith("-multiply")
    
    # Execute the tool
    result = await provider.execute_tool(tools[0].name, {"x": 6, "y": 7})
    assert result.success is True
    assert result.result == 42


@pytest.mark.asyncio
async def test_mixed_tool_sources():
    """Test using both package-based and direct function tools"""
    @tool
    def divide(numerator: float, denominator: float):
        """Divide two numbers
        
        Args:
            numerator: Number to divide
            denominator: Number to divide by
            
        Returns:
            Result of division
        """
        if denominator == 0:
            raise ValueError("Cannot divide by zero")
        return numerator / denominator
    
    provider = PythonToolProvider({
        "tool_packages": ["xaibo_examples.demo_tools.test_tools"],
        "tool_functions": [divide]
    })
    
    # List tools
    tools = await provider.list_tools()
    assert len(tools) == 3  # 2 from package + 1 direct function
    
    # Execute direct function tool
    divide_tool = next(t for t in tools if t.name.endswith("-divide"))
    result = await provider.execute_tool(divide_tool.name, {"numerator": 10, "denominator": 2})
    assert result.success is True
    assert result.result == 5.0
    
    # Test error handling
    result = await provider.execute_tool(divide_tool.name, {"numerator": 10, "denominator": 0})
    assert result.success is False
    assert "divide by zero" in result.error.lower()


@pytest.mark.asyncio
async def test_parameter_types_are_valid_json_schema():
    """Strict providers (OpenAI) reject any type outside JSON Schema's vocabulary —
    one 'Optional'/'dict'/'list' 400s the whole request. Mirrors the real failure:
    gpt-5.5 rejecting github_tools.create_issue over Optional[list[str]]."""
    from typing import Optional

    @tool
    def create_issue(repo: str, title: str, count: int, score: float, flag: bool,
                     labels: Optional[list[str]] = None, meta: dict = None, anything=None):
        """File an issue

        Args:
            repo: repository
            title: issue title
            count: how many
            score: how good
            flag: whether
            labels: labels to apply
            meta: extra fields
            anything: untyped
        """
        return None

    provider = PythonToolProvider({"tool_functions": [create_issue]})
    tools = await provider.list_tools()
    p = tools[0].parameters

    assert p["repo"].type == "string"
    assert p["count"].type == "integer"
    assert p["score"].type == "number"
    assert p["flag"].type == "boolean"
    assert p["labels"].type == "array", "Optional[list[str]] must map to array, not 'Optional'"
    assert p["meta"].type == "object"
    assert p["anything"].type == "string"

    valid = {"string", "integer", "number", "boolean", "array", "object", "null"}
    assert all(q.type in valid for q in p.values()), {k: q.type for k, q in p.items()}


@pytest.mark.asyncio
async def test_string_annotation_complex_types_map_to_json_schema():
    """String annotations (future-import modules) with typing constructs must also
    land on valid JSON Schema types."""
    @tool
    def fancy(labels: "Optional[list[str]]" = None, meta: "dict" = None):
        """Fancy

        Args:
            labels: labels
            meta: meta
        """
        return None

    provider = PythonToolProvider({"tool_functions": [fancy]})
    tools = await provider.list_tools()
    p = tools[0].parameters
    assert p["labels"].type == "array"
    assert p["meta"].type == "object"


@pytest.mark.asyncio
async def test_string_annotations_do_not_crash():
    """Quoted annotations (or `from __future__ import annotations` in the
    tool module) make param.annotation a *string* at runtime; list_tools
    must map them like real classes, not crash with AttributeError."""
    @tool
    def shout(text: "str", times: "int" = 1):
        """Repeat text loudly

        Args:
            text: What to shout
            times: How many times
        """
        return (text.upper() + "! ") * times

    provider = PythonToolProvider({"tool_functions": [shout]})
    tools = await provider.list_tools()
    assert len(tools) == 1
    params = tools[0].parameters
    assert params["text"].type == "string"
    assert params["times"].type == "integer"
    assert params["text"].required is True
    assert params["times"].required is False
