import os
import pytest

from xaibo.primitives.modules.llm.google import GoogleLLM
from xaibo.core.models.tools import Tool, ToolParameter
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMRole


@pytest.mark.asyncio
async def test_google_generate():
    """Test basic generation with Google Gemini LLM"""
    # Skip if no API key is available
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = GoogleLLM({
        "api_key": os.environ.get("GOOGLE_API_KEY"),
        "model": "gemini-2.0-flash-001"
    })
    
    # Create a simple message
    messages = [
        LLMMessage(role=LLMRole.USER, content="Say hello world")
    ]
    
    # Generate a response
    response = await llm.generate(messages)
    
    # Verify the response
    assert response.content is not None
    assert len(response.content) > 0
    assert response.usage is not None
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_google_generate_with_options():
    """Test generation with options"""
    # Skip if no API key is available
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = GoogleLLM({
        "api_key": os.environ.get("GOOGLE_API_KEY"),
        "model": "gemini-2.0-flash-001"
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
async def test_google_function_calling():
    """Test function calling with Google Gemini"""
    # Skip if no API key is available
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = GoogleLLM({
        "api_key": os.environ.get("GOOGLE_API_KEY"),
        "model": "gemini-2.0-flash-001"
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
        LLMMessage(role=LLMRole.USER, content="What's the weather like in San Francisco?")
    ]
    
    # Create options with the function
    options = LLMOptions(
        functions=[get_weather_function]
    )
    
    # Generate a response
    response = await llm.generate(messages, options)
    
    # Verify function call
    assert response.function_call is not None
    assert response.function_call.name == "get_weather"
    assert "location" in response.function_call.arguments
    assert "San Francisco" in response.function_call.arguments["location"]


@pytest.mark.asyncio
async def test_google_streaming():
    """Test streaming with Google Gemini"""
    # Skip if no API key is available
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = GoogleLLM({
        "api_key": os.environ.get("GOOGLE_API_KEY"),
        "model": "gemini-2.0-flash-001"
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
