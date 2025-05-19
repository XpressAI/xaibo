import os
from pathlib import Path

import pytest

from xaibo.core.models import LLMResponse, LLMUsage
from xaibo.primitives.modules.llm.mock import MockLLM
from xaibo.core.models.tools import Tool, ToolParameter
from xaibo.core.models.llm import LLMMessage, LLMMessageContent, LLMMessageContentType, LLMOptions, LLMRole, LLMFunctionCall, LLMFunctionResult


@pytest.mark.asyncio
async def test_openai_generate():
    # Initialize the LLM
    llm = MockLLM({
        "responses": [LLMResponse(
            content="Hello World",
            usage=LLMUsage(
                prompt_tokens=1,
                completion_tokens=2,
                total_tokens=3
            )
        ).model_dump()]
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
async def test_openai_streaming():
    # Initialize the LLM
    llm = MockLLM({
        "responses": [LLMResponse(
            content="12345"
        ).model_dump()],
        "streaming_chunk_size": 1
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
    assert len(chunks) == 5
    
    # Verify the combined content makes sense
    combined = "".join(chunks)
    assert "1" in combined
    assert "2" in combined
    assert "3" in combined
    assert "4" in combined
    assert "5" in combined