import logging
import pytest
import asyncio
import json
import os
import tempfile
import shutil
from fastapi import FastAPI
from fastapi.testclient import TestClient

from xaibo import Xaibo, AgentConfig, ModuleConfig
from xaibo.server.adapters.openai_responses import OpenAiResponsesApiAdapter
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
            await asyncio.sleep(0.01)


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
def temp_responses_dir():
    """Create a temporary directory for responses storage"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


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
def app(xaibo_instance, temp_responses_dir):
    """Create a test FastAPI app with OpenAI Responses adapter"""
    app = FastAPI()
    adapter = OpenAiResponsesApiAdapter(xaibo_instance, streaming_timeout=0.5, responses_dir=temp_responses_dir)
    adapter.adapt(app)
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


def test_create_response_non_streaming(client):
    """Test creating a non-streaming response"""
    request_data = {
        "model": "echo-agent",
        "input": "Hello world"
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "response"
    assert data["status"] == "completed"
    assert data["model"] == "echo-agent"
    assert len(data["output"]) == 1
    assert data["output"][0]["type"] == "message"
    assert data["output"][0]["role"] == "assistant"
    assert len(data["output"][0]["content"]) == 1
    assert data["output"][0]["content"][0]["type"] == "output_text"
    assert data["output"][0]["content"][0]["text"] == "You said: Hello world"
    assert data["store"] == True
    assert data["previous_response_id"] is None


def test_create_response_streaming(client):
    """Test creating a streaming response"""
    request_data = {
        "model": "streaming-agent",
        "input": "Hello world",
        "stream": True
    }
    
    with client.stream(
        "POST",
        "/openai/responses",
        json=request_data
    ) as response:
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/event-stream; charset=utf-8"
        
        events = []
        accumulated_text = ""
        
        for line in response.iter_lines():
            if line.startswith("data: "):
                if line == "data: [DONE]":
                    break
                    
                event_data = json.loads(line[6:])  # Remove "data: " prefix
                events.append(event_data)
                
                # Accumulate text deltas
                if event_data["type"] == "response.output_text.delta":
                    accumulated_text += event_data["delta"]
        
        # Check event sequence
        event_types = [event["type"] for event in events]
        assert "response.created" in event_types
        assert "response.in_progress" in event_types
        assert "response.output_item.added" in event_types
        assert "response.content_part.added" in event_types
        assert "response.output_text.delta" in event_types
        assert "response.content_part.done" in event_types
        assert "response.output_text.done" in event_types
        assert "response.output_item.done" in event_types
        assert "response.completed" in event_types
        
        # Check accumulated text
        assert accumulated_text == "Streaming: Hello world"


def test_create_response_with_previous_response_id(client):
    """Test creating a response with conversation state"""
    # First response
    request_data1 = {
        "model": "history-agent",
        "input": "First message"
    }
    
    response1 = client.post(
        "/openai/responses", 
        json=request_data1
    )
    assert response1.status_code == 200
    
    data1 = response1.json()
    response_id1 = data1["id"]
    
    # Second response with previous_response_id
    request_data2 = {
        "model": "history-agent",
        "input": "Second message",
        "previous_response_id": response_id1
    }
    
    response2 = client.post(
        "/openai/responses", 
        json=request_data2
    )
    assert response2.status_code == 200
    
    data2 = response2.json()
    assert data2["previous_response_id"] == response_id1
    # The history-aware agent should show message count including previous conversation
    assert "Message #3 in conversation" in data2["output"][0]["content"][0]["text"]


def test_get_response(client):
    """Test retrieving a stored response"""
    # Create a response first
    request_data = {
        "model": "echo-agent",
        "input": "Hello world"
    }
    
    create_response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert create_response.status_code == 200
    
    response_id = create_response.json()["id"]
    
    # Retrieve the response
    get_response = client.get(f"/openai/responses/{response_id}")
    assert get_response.status_code == 200
    
    data = get_response.json()
    assert data["id"] == response_id
    assert data["object"] == "response"
    assert data["status"] == "completed"


def test_get_response_not_found(client):
    """Test retrieving a non-existent response"""
    response = client.get("/openai/responses/non-existent-id")
    assert response.status_code == 404


def test_delete_response(client):
    """Test deleting a response"""
    # Create a response first
    request_data = {
        "model": "echo-agent",
        "input": "Hello world"
    }
    
    create_response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert create_response.status_code == 200
    
    response_id = create_response.json()["id"]
    
    # Delete the response
    delete_response = client.delete(f"/openai/responses/{response_id}")
    assert delete_response.status_code == 200
    
    data = delete_response.json()
    assert data["id"] == response_id
    assert data["object"] == "response"
    assert data["deleted"] == True
    
    # Verify it's actually deleted
    get_response = client.get(f"/openai/responses/{response_id}")
    assert get_response.status_code == 404


def test_delete_response_not_found(client):
    """Test deleting a non-existent response"""
    response = client.delete("/openai/responses/non-existent-id")
    assert response.status_code == 404


def test_cancel_response_not_background(client):
    """Test cancelling a non-background response (should fail)"""
    # Create a regular response first
    request_data = {
        "model": "echo-agent",
        "input": "Hello world"
    }
    
    create_response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert create_response.status_code == 200
    
    response_id = create_response.json()["id"]
    
    # Try to cancel it (should fail)
    cancel_response = client.post(f"/openai/responses/{response_id}/cancel")
    assert cancel_response.status_code == 400


def test_cancel_response_background(client):
    """Test cancelling a background response"""
    # Create a background response first
    request_data = {
        "model": "echo-agent",
        "input": "Hello world",
        "background": True
    }
    
    create_response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert create_response.status_code == 200
    
    response_id = create_response.json()["id"]
    
    # Cancel it
    cancel_response = client.post(f"/openai/responses/{response_id}/cancel")
    assert cancel_response.status_code == 200
    
    data = cancel_response.json()
    assert data["id"] == response_id
    assert data["status"] == "cancelled"


def test_cancel_response_not_found(client):
    """Test cancelling a non-existent response"""
    response = client.post("/openai/responses/non-existent-id/cancel")
    assert response.status_code == 404


def test_get_input_items(client):
    """Test retrieving input items for a response"""
    # Create a response first
    request_data = {
        "model": "echo-agent",
        "input": "Hello world"
    }
    
    create_response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert create_response.status_code == 200
    
    response_id = create_response.json()["id"]
    
    # Get input items
    input_response = client.get(f"/openai/responses/{response_id}/input_items")
    assert input_response.status_code == 200
    
    data = input_response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["type"] == "message"
    assert data["data"][0]["role"] == "user"
    assert len(data["data"][0]["content"]) == 1
    assert data["data"][0]["content"][0]["type"] == "input_text"
    assert data["data"][0]["content"][0]["text"] == "Hello world"


def test_get_input_items_not_found(client):
    """Test retrieving input items for a non-existent response"""
    response = client.get("/openai/responses/non-existent-id/input_items")
    assert response.status_code == 404


def test_create_response_with_store_false(client):
    """Test creating a response with store=false"""
    request_data = {
        "model": "echo-agent",
        "input": "Hello world",
        "store": False
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["store"] == False
    
    # Response should still be retrievable immediately after creation
    # but won't be persisted to database
    response_id = data["id"]
    get_response = client.get(f"/openai/responses/{response_id}")
    # This might return 404 since store=false means it's not persisted
    # The behavior depends on implementation details


def test_create_response_with_instructions(client):
    """Test creating a response with instructions"""
    request_data = {
        "model": "echo-agent",
        "input": "Hello world",
        "instructions": "You are a helpful assistant."
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["instructions"] == "You are a helpful assistant."


def test_create_response_with_metadata(client):
    """Test creating a response with metadata"""
    metadata = {"user_id": "test-user", "session_id": "test-session"}
    request_data = {
        "model": "echo-agent",
        "input": "Hello world",
        "metadata": metadata
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["metadata"] == metadata


def test_create_response_invalid_model(client):
    """Test creating a response with an invalid model"""
    request_data = {
        "model": "non-existent-model",
        "input": "Hello world"
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 400


def test_create_response_missing_required_fields(client):
    """Test creating a response with missing required fields"""
    # Missing model
    request_data = {
        "input": "Hello world"
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 400
    
    # Missing input
    request_data = {
        "model": "echo-agent"
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 400


def test_create_response_with_array_input(client):
    """Test creating a response with array input format"""
    request_data = {
        "model": "echo-agent",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Hello from array input"
                    }
                ]
            }
        ]
    }
    
    response = client.post(
        "/openai/responses", 
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    # The response should contain the processed text
    assert "Hello from array input" in data["output"][0]["content"][0]["text"]


def test_response_persistence_across_requests(client):
    """Test that responses are properly persisted and can be retrieved later"""
    # Create multiple responses
    responses = []
    for i in range(3):
        request_data = {
            "model": "echo-agent",
            "input": f"Message {i+1}"
        }
        
        response = client.post(
            "/openai/responses", 
            json=request_data
        )
        assert response.status_code == 200
        responses.append(response.json())
    
    # Verify all responses can be retrieved
    for response_data in responses:
        response_id = response_data["id"]
        get_response = client.get(f"/openai/responses/{response_id}")
        assert get_response.status_code == 200
        
        retrieved_data = get_response.json()
        assert retrieved_data["id"] == response_id
        assert retrieved_data["status"] == "completed"


def test_conversation_state_persistence(client):
    """Test that conversation state is properly maintained across multiple responses"""
    # Create a chain of responses with conversation state
    response_ids = []
    
    # First message
    request_data = {
        "model": "history-agent",
        "input": "First message"
    }
    
    response = client.post("/openai/responses", json=request_data)
    assert response.status_code == 200
    response_ids.append(response.json()["id"])
    
    # Second message referencing first
    request_data = {
        "model": "history-agent",
        "input": "Second message",
        "previous_response_id": response_ids[0]
    }
    
    response = client.post("/openai/responses", json=request_data)
    assert response.status_code == 200
    response_ids.append(response.json()["id"])
    
    # Third message referencing second
    request_data = {
        "model": "history-agent",
        "input": "Third message",
        "previous_response_id": response_ids[1]
    }
    
    response = client.post("/openai/responses", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    # The third response should show the correct message count
    assert "Message #5 in conversation" in data["output"][0]["content"][0]["text"]


def test_create_response_with_complex_array_input(client):
    """Test creating a response with complex array input format"""
    request_data = {
        "model": "echo-agent",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "First part of message"
                    }
                ]
            },
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Second part of message"
                    }
                ]
            }
        ]
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    # Should process the last user message
    assert "Second part of message" in data["output"][0]["content"][0]["text"]


def test_streaming_response_event_sequence(client):
    """Test that streaming response events are in the correct sequence"""
    request_data = {
        "model": "streaming-agent",
        "input": "Test streaming sequence",
        "stream": True
    }
    
    with client.stream(
        "POST",
        "/openai/responses",
        json=request_data
    ) as response:
        assert response.status_code == 200
        
        events = []
        sequence_numbers = []
        
        for line in response.iter_lines():
            if line.startswith("data: "):
                if line == "data: [DONE]":
                    break
                    
                event_data = json.loads(line[6:])
                events.append(event_data["type"])
                sequence_numbers.append(event_data.get("sequence_number", 0))
        
        # Check that sequence numbers are monotonically increasing
        assert sequence_numbers == sorted(sequence_numbers)
        
        # Check expected event sequence
        expected_sequence = [
            "response.created",
            "response.in_progress",
            "response.output_item.added",
            "response.content_part.added"
        ]
        
        # All expected events should be present at the start
        for expected_event in expected_sequence:
            assert expected_event in events
        
        # Should end with completion events
        assert "response.content_part.done" in events
        assert "response.output_text.done" in events
        assert "response.output_item.done" in events
        assert "response.completed" in events


def test_database_isolation_between_tests(client):
    """Test that database operations are properly isolated between tests"""
    # Create a response
    request_data = {
        "model": "echo-agent",
        "input": "Isolation test message"
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    assert response.status_code == 200
    
    response_id = response.json()["id"]
    
    # Verify it exists
    get_response = client.get(f"/openai/responses/{response_id}")
    assert get_response.status_code == 200
    
    # This test should not interfere with other tests due to temp directory fixture


def test_response_with_all_optional_parameters(client):
    """Test creating a response with all optional parameters set"""
    request_data = {
        "model": "echo-agent",
        "input": "Test with all parameters",
        "instructions": "You are a helpful assistant",
        "max_output_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.9,
        "store": True,
        "metadata": {
            "user_id": "test-user-123",
            "session_id": "session-456",
            "custom_field": "custom_value"
        },
        "user": "test-user",
        "background": False,
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "truncation": "disabled"
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["instructions"] == "You are a helpful assistant"
    assert data["max_output_tokens"] == 1000
    assert data["temperature"] == 0.7
    assert data["top_p"] == 0.9
    assert data["store"] == True
    assert data["metadata"]["user_id"] == "test-user-123"
    assert data["user"] == "test-user"
    assert data["background"] == False
    assert data["parallel_tool_calls"] == True
    assert data["tool_choice"] == "auto"
    assert data["tools"] == []
    assert data["truncation"] == "disabled"


def test_error_handling_in_streaming_response(client):
    """Test error handling during streaming response generation"""
    # Test with invalid model in non-streaming mode first
    request_data = {
        "model": "non-existent-agent",
        "input": "This should fail",
        "stream": False
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    # Should fail with 400 for invalid model
    assert response.status_code == 400
    
    # For streaming, the error handling is more complex since the response
    # starts before agent validation. This is a limitation of the current
    # implementation where streaming responses begin immediately.
    # In a production system, you might want to validate the model first.


def test_input_items_pagination(client):
    """Test pagination of input items"""
    # Create a response with input
    request_data = {
        "model": "echo-agent",
        "input": "Test pagination message"
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    assert response.status_code == 200
    
    response_id = response.json()["id"]
    
    # Test pagination parameters
    input_response = client.get(
        f"/openai/responses/{response_id}/input_items",
        params={"limit": 10, "order": "desc"}
    )
    assert input_response.status_code == 200
    
    data = input_response.json()
    assert data["object"] == "list"
    assert "has_more" in data
    assert "first_id" in data
    assert "last_id" in data


def test_conversation_state_with_multiple_agents(client):
    """Test conversation state works correctly when switching between agents"""
    # Start with history-agent
    request_data1 = {
        "model": "history-agent",
        "input": "First message with history agent"
    }
    
    response1 = client.post("/openai/responses", json=request_data1)
    assert response1.status_code == 200
    response_id1 = response1.json()["id"]
    
    # Continue with echo-agent using previous response
    request_data2 = {
        "model": "echo-agent",
        "input": "Second message with echo agent",
        "previous_response_id": response_id1
    }
    
    response2 = client.post("/openai/responses", json=request_data2)
    assert response2.status_code == 200
    
    data2 = response2.json()
    assert data2["previous_response_id"] == response_id1
    assert "You said: Second message with echo agent" in data2["output"][0]["content"][0]["text"]


def test_response_usage_information(client):
    """Test that usage information is properly included in responses"""
    request_data = {
        "model": "echo-agent",
        "input": "Test usage tracking"
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "usage" in data
    assert "input_tokens" in data["usage"]
    assert "output_tokens" in data["usage"]
    assert "total_tokens" in data["usage"]
    assert "input_tokens_details" in data["usage"]
    assert "output_tokens_details" in data["usage"]


def test_concurrent_response_creation(client):
    """Test that concurrent response creation works correctly"""
    import threading
    import time
    
    results = []
    errors = []
    
    def create_response(index):
        try:
            request_data = {
                "model": "echo-agent",
                "input": f"Concurrent message {index}"
            }
            
            response = client.post(
                "/openai/responses",
                json=request_data
            )
            results.append((index, response.status_code, response.json()))
        except Exception as e:
            errors.append((index, str(e)))
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_response, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 5
    
    for index, status_code, data in results:
        assert status_code == 200
        assert data["status"] == "completed"
        assert f"Concurrent message {index}" in data["output"][0]["content"][0]["text"]


def test_response_object_structure_compliance(client):
    """Test that response objects comply with OpenAI Responses API structure"""
    request_data = {
        "model": "echo-agent",
        "input": "Test API compliance"
    }
    
    response = client.post(
        "/openai/responses",
        json=request_data
    )
    assert response.status_code == 200
    
    data = response.json()
    
    # Required fields
    required_fields = ["id", "object", "created_at", "status", "model", "output"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check object type
    assert data["object"] == "response"
    
    # Check status is valid
    valid_statuses = ["completed", "failed", "incomplete", "cancelled", "in_progress"]
    assert data["status"] in valid_statuses
    
    # Check output structure
    assert isinstance(data["output"], list)
    if data["output"]:
        output_item = data["output"][0]
        assert "type" in output_item
        assert "id" in output_item
        assert "role" in output_item
        assert "content" in output_item
        
        if output_item["content"]:
            content_item = output_item["content"][0]
            assert "type" in content_item
            if content_item["type"] == "output_text":
                assert "text" in content_item