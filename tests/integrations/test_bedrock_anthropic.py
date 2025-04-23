import os
from pathlib import Path

import pytest

from xaibo.primitives.modules.llm.bedrock import BedrockLLM
from xaibo.core.models.tools import Tool, ToolParameter
from xaibo.core.models.llm import LLMMessage, LLMMessageContent, LLMMessageContentType, LLMOptions, LLMRole, LLMFunctionCall, LLMFunctionResult


@pytest.mark.asyncio
async def test_bedrock_anthropic_generate():
    """Test basic generation with Bedrock Anthropic LLM"""
    # Skip if no AWS credentials are available
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials environment variables not set")
    
    # Initialize the LLM
    llm = BedrockLLM({
        "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "region_name": "ap-northeast-1"
    })
    
    # Create a simple message
    messages = [
        LLMMessage.user("Say exactly 'hello world'")
    ]
    
    # Generate a response
    response = await llm.generate(messages)
    
    # Verify the response
    assert response.content is not None
    assert len(response.content) > 0
    assert "hello world" in response.content.lower()


@pytest.mark.asyncio
async def test_bedrock_anthropic_generate_with_options():
    """Test generation with options"""
    # Skip if no AWS credentials are available
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials environment variables not set")
    
    # Initialize the LLM
    llm = BedrockLLM({
        "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "region_name": "ap-northeast-1"
    })
    
    # Create a simple message
    messages = [
        LLMMessage.system("You are a helpful assistant that speaks like a pirate."),
        LLMMessage.user("Introduce yourself briefly.")
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
async def test_bedrock_anthropic_function_calling():
    """Test function calling with Bedrock Anthropic"""
    # Skip if no AWS credentials are available
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials environment variables not set")
    
    # Initialize the LLM
    llm = BedrockLLM({
        "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "region_name": "ap-northeast-1"
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
        LLMMessage.user("What's the weather like in San Francisco using Fahrenheit?")
    ]
    
    # Create options with the function
    options = LLMOptions(
        functions=[get_weather_function]
    )
    
    # Generate a response
    response = await llm.generate(messages, options)
    
    # Verify function call
    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "get_weather"
    assert "location" in response.tool_calls[0].arguments
    assert response.tool_calls[0].arguments["location"].lower() == "san francisco" or response.tool_calls[0].arguments["location"] == "San Francisco, CA"


@pytest.mark.asyncio
async def test_bedrock_anthropic_tool_response():
    """Test processing of tool call responses with Bedrock Anthropic"""
    # Skip if no AWS credentials are available
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials environment variables not set")
    
    # Initialize the LLM
    llm = BedrockLLM({
        "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "region_name": "ap-northeast-1"
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
        LLMMessage.user("What's the weather like in San Francisco?"),
        LLMMessage.function(
            id="call_1",
            name="get_weather",
            arguments={"location": "San Francisco, CA"}
        ),
        LLMMessage.function_result(
            id="call_1",
            name="get_weather",
            content="72°F and sunny"
        )
    ]
    
    # Generate a response
    response = await llm.generate(messages, LLMOptions(functions=[get_weather_function]))
    
    # Verify response incorporates tool result
    assert response.content is not None
    assert "72" in response.content or "sunny" in response.content


@pytest.mark.asyncio
async def test_bedrock_anthropic_streaming():
    """Test streaming with Bedrock Anthropic"""
    # Skip if no AWS credentials are available
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials environment variables not set")
    
    # Initialize the LLM
    llm = BedrockLLM({
        "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "region_name": "ap-northeast-1"
    })
    
    # Create a simple message
    messages = [
        LLMMessage.user("Count from 1 to 5")
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


@pytest.mark.asyncio
async def test_bedrock_anthropic_image_content():
    """Test Bedrock Anthropic's ability to understand image content"""
    # Skip if no AWS credentials are available
    if not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials environment variables not set")
    
    # Initialize the LLM
    llm = BedrockLLM({
        "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "region_name": "ap-northeast-1"
    })

    test_dir = Path(__file__).parent
    image_path = test_dir.parent / "resources" / "images" / "hello-xaibo.png"

    image_message = LLMMessage.user_image(str(image_path))

    # Create a message with image content
    messages = [
        LLMMessage(
            role=LLMRole.USER,
            content=[
                LLMMessageContent(type=LLMMessageContentType.TEXT, text="What text appears in this image?"),
                image_message.content[0]
            ]
        )
    ]
    
    # Generate a response
    response = await llm.generate(messages)
    
    # Verify the response mentions the text from the image
    assert response.content is not None
    assert "Hello Xaibo" in response.content
