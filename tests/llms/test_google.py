import os
from pathlib import Path
import pytest

from xaibo.primitives.modules.llm.google import GoogleLLM
from xaibo.core.models.tools import Tool, ToolParameter
from xaibo.core.models.llm import LLMMessage, LLMMessageContent, LLMMessageContentType, LLMOptions, LLMRole, LLMFunctionCall, LLMFunctionResult


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
        LLMMessage.user("Say exactly 'hello world'")
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
        LLMMessage.user("What's the weather like in San Francisco?")
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
    assert "San Francisco" in response.tool_calls[0].arguments["location"]


@pytest.mark.asyncio
async def test_google_tool_response():
    """Test processing of tool call responses with Google Gemini"""
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
async def test_google_image_content():
    """Test Google Gemini's ability to understand image content"""
    # Skip if no API key is available
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    
    # Initialize the LLM
    llm = GoogleLLM({
        "api_key": os.environ.get("GOOGLE_API_KEY"),
        "model": "gemini-2.0-flash-001"
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


def test_google_array_schema_generation():
    """Test that array type parameters include required items property in schema"""
    # Initialize the LLM (no API key needed for schema generation test)
    llm = GoogleLLM({
        "api_key": "test-key",  # Dummy key for testing
        "model": "gemini-2.0-flash-001"
    })
    
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
    
    # Generate the function schema
    config = llm._prepare_config(options)
    
    # Verify the schema structure
    assert config is not None
    assert hasattr(config, 'tools')
    assert len(config.tools) == 1
    
    tool = config.tools[0]
    assert len(tool.function_declarations) == 1
    
    function_declaration = tool.function_declarations[0]
    assert function_declaration.name == "process_items"
    
    # Check the parameters schema
    parameters = function_declaration.parameters
    assert parameters.type == "OBJECT"
    
    # Verify the array parameter has the required items property
    items_param = parameters.properties["items"]
    assert items_param.type == "ARRAY"
    assert hasattr(items_param, 'items'), "Array type parameter must include 'items' property"
    assert items_param.items is not None, "Array type parameter must have non-null 'items' property"
    assert items_param.items.type == "STRING", "Array items should default to string type"
    
    # Verify non-array parameter has null items property
    options_param = parameters.properties["options"]
    assert options_param.type == "STRING"
    assert options_param.items is None, "Non-array parameters should have null 'items' property"
    
    print("✅ Google array schema generation test passed - items property is correctly included")
