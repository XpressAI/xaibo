import logging

import pytest
import asyncio
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from xaibo import Xaibo, AgentConfig, ModuleConfig
from xaibo.server.adapters.openai import OpenAiApiAdapter
from xaibo.core.protocols import TextMessageHandlerProtocol, ResponseProtocol, ConversationHistoryProtocol


class Echo(TextMessageHandlerProtocol):
    """Simple echo module for testing"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict = None):
        self.config = config or {}
        self.prefix = self.config.get("prefix", "")
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        await self.response.respond_text(f"{self.prefix}{text}")


class SlowEcho(TextMessageHandlerProtocol):
    """Echo module that introduces a delay for testing timeouts"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict = None):
        self.config = config or {}
        self.prefix = self.config.get("prefix", "")
        self.delay_seconds = self.config.get("delay_seconds", 2.0)
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        await asyncio.sleep(self.delay_seconds)
        await self.response.respond_text(f"{self.prefix}{text}")


class StreamingEcho(TextMessageHandlerProtocol):
    """Echo module that supports streaming responses"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict = None):
        self.config = config or {}
        self.prefix = self.config.get("prefix", "")
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        # Stream character by character with small delay
        for char in f"{self.prefix}{text}":
            await self.response.respond_text(char)
            await asyncio.sleep(0.05)


class HistoryAwareEcho(TextMessageHandlerProtocol):
    """Echo module that is aware of conversation history"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, history: ConversationHistoryProtocol, config: dict = None):
        self.config = config or {}
        self.response = response
        self.history = history
        
    async def handle_text(self, text: str) -> None:      
        # Get the current conversation history
        messages = await self.history.get_history()
        message_count = len(messages)
        
        # Create a response that includes history information
        response_text = f"History-aware response to: {text} (Message #{message_count} in conversation)"
        
        # Send the response
        await self.response.respond_text(response_text)

@pytest.fixture
def xaibo_instance():
    """Create a Xaibo instance with test agents"""
    xaibo = Xaibo()
    
    # Register a simple echo agent
    echo_config = AgentConfig(
        id="echo-agent",
        modules=[
            ModuleConfig(
                module=Echo,
                id="echo",
                config={
                    "prefix": "You said: "
                }
            )
        ]
    )
    xaibo.register_agent(echo_config)
    
    # Register a slow echo agent for testing timeouts
    slow_config = AgentConfig(
        id="slow-agent",
        modules=[
            ModuleConfig(
                module=SlowEcho,
                id="slow-echo",
                config={
                    "prefix": "Slow response: ",
                    "delay_seconds": 2.0
                }
            )
        ]
    )
    xaibo.register_agent(slow_config)
    
    # Register a streaming echo agent
    streaming_config = AgentConfig(
        id="streaming-agent",
        modules=[
            ModuleConfig(
                module=StreamingEcho,
                id="streaming-echo",
                config={
                    "prefix": "Streaming: "
                }
            )
        ]
    )
    xaibo.register_agent(streaming_config)
    
    # Register a history-aware echo agent
    history_config = AgentConfig(
        id="history-agent",
        modules=[
            ModuleConfig(
                module=HistoryAwareEcho,
                id="history-echo",
                config={}
            )
        ]
    )
    xaibo.register_agent(history_config)
    
    return xaibo


@pytest.fixture
def app(xaibo_instance):
    """Create a test FastAPI app with OpenAI adapter"""
    app = FastAPI()
    adapter = OpenAiApiAdapter(xaibo_instance, streaming_timeout=0.5)
    adapter.adapt(app)
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


def test_openai_models_endpoint(client):
    """Test the OpenAI models endpoint returns the correct agent list"""
    response = client.get("/openai/models")
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "list"
    
    # Check that our test agents are in the list
    model_ids = [model["id"] for model in data["data"]]
    assert "echo-agent" in model_ids
    assert "slow-agent" in model_ids
    assert "streaming-agent" in model_ids
    assert "history-agent" in model_ids


def test_openai_chat_completion(client):
    """Test the OpenAI chat completion endpoint with non-streaming response"""
    request_data = {
        "model": "echo-agent",
        "messages": [
            {"role": "user", "content": "Hello world"}
        ]
    }
    
    response = client.post(
        "/openai/chat/completions", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"] == "You said: Hello world"


def test_openai_chat_completion_streaming(client):
    """Test the OpenAI chat completion endpoint with streaming response"""
    request_data = {
        "model": "streaming-agent",
        "messages": [
            {"role": "user", "content": "Hello world"}
        ],
        "stream": True
    }
    
    with client.stream(
        "POST",
        "/openai/chat/completions",
        json=request_data
    ) as response:
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/event-stream; charset=utf-8"
        
        # Read the streaming response
        full_response = ""
        complete_content = ""

        for line in response.iter_lines():
            if line.startswith("data: "):
                full_response += line + "\n"

                if line == "data: [DONE]":
                    break

                data = json.loads(line[6:])  # Remove "data: " prefix
                if "choices" in data and data["choices"][0]["delta"].get("content"):
                    content = data["choices"][0]["delta"]["content"]
                    complete_content += content
    
    assert "Streaming: Hello world" == complete_content
    assert "data: [DONE]" in full_response


def test_openai_chat_completion_timeout_handling(client):
    """Test that the streaming endpoint handles timeouts correctly"""
    request_data = {
        "model": "slow-agent",
        "messages": [
            {"role": "user", "content": "Hello world"}
        ],
        "stream": True
    }
    
    with client.stream(
        "POST",
        "/openai/chat/completions",
        json=request_data
    ) as response:
        assert response.status_code == 200

        # Read the streaming response
        timeout_chunks = 0
        for line in response.iter_lines():
            if line == "data: [DONE]":
                break

            if line.startswith("data: "):
                data = json.loads(line[6:])  # Remove "data: " prefix
                if "choices" in data and data["choices"][0]["delta"] == {"content": ""}:
                    timeout_chunks += 1

                # Don't read the whole response, just check for timeout chunks
                if timeout_chunks >= 2:
                    break

    # Verify we got at least some timeout chunks
    assert timeout_chunks >= 2


def test_openai_chat_completion_invalid_model(client):
    """Test the OpenAI chat completion endpoint with an invalid model"""
    request_data = {
        "model": "non-existent-model",
        "messages": [
            {"role": "user", "content": "Hello world"}
        ]
    }
    
    response = client.post(
        "/openai/chat/completions", 
        json=request_data
    )
    assert response.status_code == 400  # Bad request


def test_openai_chat_completion_with_history(client, caplog):
    """Test the OpenAI chat completion endpoint with conversation history"""
    caplog.set_level(logging.DEBUG)

    # First message
    request_data = {
        "model": "history-agent",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "First message"}
        ]
    }
    
    response = client.post(
        "/openai/chat/completions", 
        json=request_data
    )

    assert response.status_code == 200
    
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "History-aware response to: First message (Message #2 in conversation)"
    
    # Second message with history
    request_data = {
        "model": "history-agent",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "History-aware response to: First message (Message #2 in conversation)"},
            {"role": "user", "content": "Second message"}
        ]
    }
    
    response = client.post(
        "/openai/chat/completions", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "History-aware response to: Second message (Message #4 in conversation)"


def test_openai_chat_completion_streaming_with_history(client):
    """Test the OpenAI streaming chat completion with conversation history"""
    request_data = {
        "model": "history-agent",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "History-aware response to: First message (Message #2 in conversation)"},
            {"role": "user", "content": "Hello world"}
        ],
        "stream": True
    }
    
    with client.stream(
        "POST",
        "/openai/chat/completions",
        json=request_data
    ) as response:
        assert response.status_code == 200
        
        # Read the streaming response
        complete_content = ""
        for line in response.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                data = json.loads(line[6:])  # Remove "data: " prefix
                if "choices" in data and data["choices"][0]["delta"].get("content"):
                    content = data["choices"][0]["delta"]["content"]
                    complete_content += content
    
    assert "History-aware response to: Hello world (Message #4 in conversation)" == complete_content


def test_openai_chat_completion_with_complex_history(client):
    """Test the OpenAI chat completion with a more complex conversation history"""
    request_data = {
        "model": "history-agent",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
            {"role": "user", "content": "Final question"}
        ]
    }
    
    response = client.post(
        "/openai/chat/completions", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    # The HistoryAwareEcho agent should report the correct message count
    assert data["choices"][0]["message"]["content"] == "History-aware response to: Final question (Message #6 in conversation)"
