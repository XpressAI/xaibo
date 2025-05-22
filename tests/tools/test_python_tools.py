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
