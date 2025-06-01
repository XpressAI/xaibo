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

def test_bedrock_array_schema_generation():
    """Test that array type parameters include required items property in schema"""
    # Initialize the LLM (no AWS credentials needed for schema generation test)
    try:
        llm = BedrockLLM({
            "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "region_name": "us-east-1",
            "aws_access_key_id": "test-key",  # Dummy credentials for testing
            "aws_secret_access_key": "test-secret"
        })
    except Exception:
        # If boto3 is not available or other issues, skip the test
        pytest.skip("Unable to initialize BedrockLLM for testing")
    
    # Define a function with array parameter
    test_function = Tool(
        name="process_items",
        description="Process a list of items",
        parameters={
            "items": ToolParameter(
                type="list",
                description="List of items to process",
                required=True
            ),
            "options": ToolParameter(
                type="string",
                description="Processing options",
                required=False
            )
        }
    )
    
    # Create options with the function
    options = LLMOptions(functions=[test_function])
    
    # Generate the function schema by calling the internal method
    messages = [LLMMessage.user("test")]
    bedrock_messages, system_content, tool_config = llm._prepare_messages(messages, options)
    
    # Verify the schema structure
    assert tool_config is not None
    assert "tools" in tool_config
    assert len(tool_config["tools"]) == 1
    
    tool_def = tool_config["tools"][0]
    assert tool_def["toolSpec"]["name"] == "process_items"
    
    # Check the parameters schema
    input_schema = tool_def["toolSpec"]["inputSchema"]["json"]
    assert input_schema["type"] == "object"
    
    # Verify the array parameter has the required items property
    items_param = input_schema["properties"]["items"]
    assert items_param["type"] == "array"
    assert "items" in items_param, "Array type parameter must include 'items' property"
    assert items_param["items"]["type"] == "string", "Array items should default to string type"
    
    # Verify non-array parameter doesn't have items property
    options_param = input_schema["properties"]["options"]
    assert options_param["type"] == "string"
    assert "items" not in options_param, "Non-array parameters should not have 'items' property"
    
    print("✅ Bedrock array schema generation test passed - items property is correctly included")
