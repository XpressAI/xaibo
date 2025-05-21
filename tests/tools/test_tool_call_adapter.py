import pytest
from unittest.mock import AsyncMock, Mock

from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMResponse, LLMRole, LLMUsage
from xaibo.core.models.tools import Tool, ToolParameter
from xaibo.primitives.modules.tools.no_function_calling_adapter import TextBasedToolCallAdapter


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing"""
    mock = AsyncMock()
    mock.generate = AsyncMock()
    mock.generate_stream = Mock()
    return mock


@pytest.fixture
def sample_tool():
    """Create a sample tool for testing"""
    return Tool(
        name="get_weather",
        description="Get the current weather in a given location",
        parameters={
            "location": ToolParameter(
                type="string",
                description="The city and state, e.g. San Francisco, CA",
                required=True
            ),
            "unit": ToolParameter(
                type="string",
                description="The temperature unit to use (celsius or fahrenheit)",
                required=False,
                enum=["celsius", "fahrenheit"],
                default="celsius"
            )
        }
    )


def test_make_tools_prompt(mock_llm, sample_tool):
    """Test that the tool prompt is correctly formatted"""
    adapter = TextBasedToolCallAdapter(mock_llm)
    prompt = adapter._make_tools_prompt([sample_tool])
    
    # Check that the prompt contains the tool name and description
    assert "get_weather: Get the current weather in a given location" in prompt
    
    # Check that the prompt contains parameter details
    assert "location (required): The city and state" in prompt
    assert "unit: The temperature unit to use" in prompt
    
    # Check that the prompt contains usage instructions
    assert "To use a tool, write TOOL:" in prompt
    assert "Example:" in prompt


def test_extract_tool_call(mock_llm):
    """Test extracting tool calls from response content"""
    adapter = TextBasedToolCallAdapter(mock_llm)
    
    # Test with valid tool call
    content = "Here's the weather information you requested.\n\nTOOL: get_weather {\"location\": \"San Francisco, CA\", \"unit\": \"celsius\"}"
    function_call = adapter._extract_tool_call(content)
    
    assert function_call is not None
    assert function_call.name == "get_weather"
    assert function_call.arguments["location"] == "San Francisco, CA"
    assert function_call.arguments["unit"] == "celsius"
    
    # Test with no tool call
    content = "Here's some information without a tool call."
    function_call = adapter._extract_tool_call(content)
    assert function_call is None
    
    # Test with malformed JSON
    content = "TOOL: get_weather {location: San Francisco}"
    function_call = adapter._extract_tool_call(content)
    assert function_call is not None
    assert function_call.name == "get_weather"
    assert "raw_input" in function_call.arguments


def test_modify_messages_with_tools(mock_llm, sample_tool):
    """Test modifying messages to include tool descriptions"""
    adapter = TextBasedToolCallAdapter(mock_llm)
    
    # Test with existing system message
    messages = [
        LLMMessage.system("You are a helpful assistant."),
        LLMMessage.user("What's the weather like?")
    ]
    
    modified = adapter._modify_messages_with_tools(messages, [sample_tool])
    
    assert len(modified) == 2
    assert modified[0].role == LLMRole.SYSTEM
    assert "You are a helpful assistant." in modified[0].content[0].text
    assert "get_weather:" in modified[0].content[-1].text
    
    # Test without system message
    messages = [
        LLMMessage.user("What's the weather like?")
    ]
    
    modified = adapter._modify_messages_with_tools(messages, [sample_tool])
    
    assert len(modified) == 2
    assert modified[0].role == LLMRole.SYSTEM
    assert "get_weather:" in modified[0].content[-1].text
    assert modified[1].role == LLMRole.USER


@pytest.mark.asyncio
async def test_generate_with_tool_call(mock_llm, sample_tool):
    """Test generating a response with a tool call"""
    # Setup mock response
    mock_llm.generate.return_value = LLMResponse(
        content="I'll check the weather for you.\n\nTOOL: get_weather {\"location\": \"San Francisco, CA\"}",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        vendor_specific={"model": "test-model"}
    )
    
    adapter = TextBasedToolCallAdapter(mock_llm)
    
    # Generate response
    messages = [
        LLMMessage.user("What's the weather like in San Francisco?")
    ]
    
    options = LLMOptions(functions=[sample_tool])
    response = await adapter.generate(messages, options)
    
    # Verify the response
    assert response.content == "I'll check the weather for you."
    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "get_weather"
    assert response.tool_calls[0].arguments["location"] == "San Francisco, CA"
    
    # Verify the mock was called with modified messages
    called_messages = mock_llm.generate.call_args[0][0]
    assert len(called_messages) == 2
    assert called_messages[0].role == LLMRole.SYSTEM
    assert "get_weather:" in called_messages[0].content[0].text
    
    # Verify that functions were not passed to the underlying LLM
    called_options = mock_llm.generate.call_args[0][1]
    assert called_options.functions is None or len(called_options.functions) == 0


@pytest.mark.asyncio
async def test_generate_without_tool_call(mock_llm):
    """Test generating a response without a tool call"""
    # Setup mock response
    mock_llm.generate.return_value = LLMResponse(
        content="I don't have access to weather information.",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        vendor_specific={"model": "test-model"}
    )
    
    adapter = TextBasedToolCallAdapter(mock_llm)
    
    # Generate response
    messages = [
        LLMMessage.user("What's the weather like in San Francisco?")
    ]
    
    response = await adapter.generate(messages)
    
    # Verify the response
    assert response.content == "I don't have access to weather information."
    assert response.tool_calls is None


@pytest.mark.asyncio
async def test_generate_stream(mock_llm, sample_tool):
    """Test streaming generation"""
    # Setup mock stream
    async def mock_stream(*args, **kwargs):
        chunks = ["I'll ", "check ", "the ", "weather ", "for ", "you."]
        for chunk in chunks:
            yield chunk
    
    mock_llm.generate_stream.return_value = mock_stream()
    
    adapter = TextBasedToolCallAdapter(mock_llm)
    
    # Generate streaming response
    messages = [
        LLMMessage.user("What's the weather like in San Francisco?")
    ]
    
    options = LLMOptions(functions=[sample_tool])
    
    # Collect chunks
    chunks = []
    async for chunk in adapter.generate_stream(messages, options):
        chunks.append(chunk)
    
    # Verify chunks
    assert chunks == ["I'll ", "check ", "the ", "weather ", "for ", "you."]
    
    # Verify the mock was called with modified messages
    called_messages = mock_llm.generate_stream.call_args[0][0]
    assert len(called_messages) == 2
    assert called_messages[0].role == LLMRole.SYSTEM
    assert "get_weather:" in called_messages[0].content[0].text
    
    # Verify that functions were not passed to the underlying LLM
    called_options = mock_llm.generate_stream.call_args[0][1]
    assert called_options.functions is None or len(called_options.functions) == 0
