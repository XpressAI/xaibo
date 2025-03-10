import pytest

from xaibo.primitives.modules.tools.python_tool_provider import PythonToolProvider


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
    assert weather_tool.description == "Get the current weather in a given location"
    assert "location" in weather_tool.parameters
    assert weather_tool.parameters["location"].required is True
    assert "unit" in weather_tool.parameters
    assert weather_tool.parameters["unit"].required is False
    
    # Verify the second tool
    search_tool = next(t for t in tools if t.name == "xaibo_examples-demo_tools-test_tools-another_function")
    assert search_tool.description == "Search for information"
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
