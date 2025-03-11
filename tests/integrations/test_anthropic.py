import os
import pytest

from xaibo.primitives.modules.llm import AnthropicLLM
from xaibo.core.models.tools import Tool, ToolParameter
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMRole, LLMFunctionCall, LLMFunctionResult


@pytest.mark.asyncio
async def test_anthropic_generate():
    """Test basic generation with Anthropic LLM"""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = AnthropicLLM({
        "model": "claude-3-haiku-20240307"
    })
    
    # Create a simple message
    messages = [
        LLMMessage(role=LLMRole.USER, content="Say exactly 'hello world'")
    ]
    
    # Generate a response
    response = await llm.generate(messages)
    
    # Verify the response
    assert response.content is not None
    assert len(response.content) > 0
    assert "Hello World".lower() in response.content.lower()
    assert response.usage is not None
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_anthropic_generate_with_options():
    """Test generation with options"""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = AnthropicLLM({
        "model": "claude-3-haiku-20240307"
    })
    
    # Create a simple message
    messages = [
        LLMMessage(role=LLMRole.SYSTEM, content="You are a helpful assistant that speaks like a pirate."),
        LLMMessage(role=LLMRole.USER, content="Introduce yourself briefly.")
    ]
    
    # Create options
    options = LLMOptions(
        temperature=0.7,
        max_tokens=50,
        stop_sequences=[".", "!"]
    )
    
    # Generate a response
    response = await llm.generate(messages, options)
    
    # Verify the response
    assert response.content is not None
    assert len(response.content) > 0
    assert not (response.content.endswith(".") or response.content.endswith("!"))


@pytest.mark.asyncio
async def test_anthropic_function_calling():
    """Test function calling with Anthropic"""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = AnthropicLLM({
        "model": "claude-3-opus-20240229"  # Using Opus as it has better tool use capabilities
    })
    
    # Define a function
    get_weather_function = Tool(
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
                description="The temperature unit to use",
                required=False
            )
        }
    )
    
    # Create a message that should trigger function calling
    messages = [
        LLMMessage(role=LLMRole.USER, content="What's the weather like in San Francisco, CA?")
    ]
    
    # Create options with the function
    options = LLMOptions(
        functions=[get_weather_function],
        vendor_specific={}
    )
    
    # Generate a response
    response = await llm.generate(messages, options)
    
    # Verify function call
    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "get_weather"
    assert "location" in response.tool_calls[0].arguments
    assert response.tool_calls[0].arguments["location"] == "San Francisco, CA"

@pytest.mark.asyncio
async def test_anthropic_tool_response():
    """Test processing of tool call responses with Anthropic"""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = AnthropicLLM({
        "model": "claude-3-opus-20240229"
    })
    
    # Define a function
    get_weather_function = Tool(
        name="get_weather",
        description="Get the current weather in a given location",
        parameters={
            "location": ToolParameter(
                type="string",
                description="The city and state, e.g. San Francisco, CA",
                required=True
            )
        }
    )
    
    # Create conversation with function call and result
    messages = [
        LLMMessage(role=LLMRole.USER, content="What's the weather like in San Francisco?"),
        LLMMessage(
            role=LLMRole.FUNCTION,
            content="",
            tool_calls=[
                LLMFunctionCall(
                    id="call_1",
                    name="get_weather",
                    arguments={"location": "San Francisco, CA"}
                )
            ]
        ),
        LLMMessage(
            role=LLMRole.FUNCTION,
            tool_results=[
                LLMFunctionResult(
                    id="call_1",
                    name="get_weather",
                    content="72°F and sunny"
                )
            ]
        )
    ]
    
    # Generate a response
    response = await llm.generate(messages, LLMOptions(functions=[get_weather_function]))
    
    # Verify response incorporates tool result
    assert response.content is not None
    assert "72" in response.content or "sunny" in response.content


@pytest.mark.asyncio
async def test_anthropic_streaming():
    """Test streaming with Anthropic"""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = AnthropicLLM({
        "model": "claude-3-haiku-20240307"
    })
    
    # Create a simple message
    messages = [
        LLMMessage(role=LLMRole.USER, content="Count from 1 to 5")
    ]
    
    # Generate a streaming response
    chunks = []
    async for chunk in llm.generate_stream(messages):
        chunks.append(chunk)
    
    # Verify we got multiple chunks
    assert len(chunks) > 1
    
    # Verify the combined content makes sense
    combined = "".join(chunks)
    assert "1" in combined
    assert "2" in combined
    assert "3" in combined
    assert "4" in combined
    assert "5" in combined
