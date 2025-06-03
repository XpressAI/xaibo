import pytest
import json
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

from xaibo import Xaibo, AgentConfig, ModuleConfig
from xaibo.server.adapters.openai import OpenAiApiAdapter
from xaibo.server.adapters.mcp import McpApiAdapter
from xaibo.core.protocols import TextMessageHandlerProtocol, ResponseProtocol


class SimpleEcho(TextMessageHandlerProtocol):
    """Simple echo module for integration testing"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict | None = None):
        self.config = config or {}
        self.prefix = self.config.get("prefix", "")
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        await self.response.respond_text(f"{self.prefix}{text}")


@pytest.fixture
def xaibo_with_agents():
    """Create a Xaibo instance with test agents"""
    xaibo = Xaibo()
    
    # Register a simple echo agent
    echo_config = AgentConfig(
        id="integration-echo",
        modules=[
            ModuleConfig(
                module=SimpleEcho,
                id="echo",
                config={
                    "prefix": "Integration: "
                }
            )
        ]
    )
    xaibo.register_agent(echo_config)
    
    return xaibo


@pytest.fixture
def app_with_both_adapters_and_keys(xaibo_with_agents):
    """Create a FastAPI app with both OpenAI and MCP adapters with API keys"""
    app = FastAPI()
    
    # Add OpenAI adapter with API key
    openai_adapter = OpenAiApiAdapter(xaibo_with_agents, api_key="integration-openai-key")
    openai_adapter.adapt(app)
    
    # Add MCP adapter with API key
    mcp_adapter = McpApiAdapter(xaibo_with_agents, api_key="integration-mcp-key")
    mcp_adapter.adapt(app)
    
    return app


@pytest.fixture
def app_with_mixed_auth(xaibo_with_agents):
    """Create a FastAPI app with one adapter with API key and one without"""
    app = FastAPI()
    
    # Add OpenAI adapter with API key
    openai_adapter = OpenAiApiAdapter(xaibo_with_agents, api_key="mixed-openai-key")
    openai_adapter.adapt(app)
    
    # Add MCP adapter without API key
    mcp_adapter = McpApiAdapter(xaibo_with_agents, api_key=None)
    mcp_adapter.adapt(app)
    
    return app


@pytest.fixture
def client_with_both_adapters(app_with_both_adapters_and_keys):
    """Create a test client for the app with both adapters"""
    return TestClient(app_with_both_adapters_and_keys)


@pytest.fixture
def client_with_mixed_auth(app_with_mixed_auth):
    """Create a test client for the app with mixed authentication"""
    return TestClient(app_with_mixed_auth)


def test_integration_openai_full_cycle_with_auth(client_with_both_adapters):
    """Test full OpenAI request/response cycle with authentication"""
    headers = {"Authorization": "Bearer integration-openai-key"}
    
    # Test models endpoint
    response = client_with_both_adapters.get("/openai/models", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "list"
    model_ids = [model["id"] for model in data["data"]]
    assert "integration-echo" in model_ids
    
    # Test chat completion
    request_data = {
        "model": "integration-echo",
        "messages": [
            {"role": "user", "content": "Hello integration test"}
        ]
    }
    
    response = client_with_both_adapters.post("/openai/chat/completions", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "Integration: Hello integration test"
    
    # Test streaming chat completion
    request_data["stream"] = True
    
    with client_with_both_adapters.stream(
        "POST",
        "/openai/chat/completions",
        json=request_data,
        headers=headers
    ) as response:
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/event-stream; charset=utf-8"
        
        # Read the streaming response
        complete_content = ""
        for line in response.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                data = json.loads(line[6:])  # Remove "data: " prefix
                if "choices" in data and data["choices"][0]["delta"].get("content"):
                    content = data["choices"][0]["delta"]["content"]
                    complete_content += content
    
    assert "Integration: Hello integration test" == complete_content


def test_integration_mcp_full_cycle_with_auth(client_with_both_adapters):
    """Test full MCP request/response cycle with authentication"""
    headers = {"Authorization": "Bearer integration-mcp-key"}
    
    # Test initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": "integration-init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "integration-test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client_with_both_adapters.post("/mcp/", json=init_request, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "integration-init"
    assert "result" in data
    assert data["result"]["serverInfo"]["name"] == "xaibo-mcp-server"
    
    # Test tools/list
    list_request = {
        "jsonrpc": "2.0",
        "id": "integration-list",
        "method": "tools/list",
        "params": {}
    }
    
    response = client_with_both_adapters.post("/mcp/", json=list_request, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    tools = data["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    assert "integration-echo" in tool_names
    
    # Test tools/call
    call_request = {
        "jsonrpc": "2.0",
        "id": "integration-call",
        "method": "tools/call",
        "params": {
            "name": "integration-echo",
            "arguments": {
                "message": "Hello MCP integration test"
            }
        }
    }
    
    response = client_with_both_adapters.post("/mcp/", json=call_request, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert data["result"]["content"][0]["text"] == "Integration: Hello MCP integration test"


def test_integration_mixed_auth_scenario(client_with_mixed_auth):
    """Test mixed authentication scenario - one adapter with auth, one without"""
    # Test OpenAI with authentication (should require auth)
    openai_headers = {"Authorization": "Bearer mixed-openai-key"}
    
    response = client_with_mixed_auth.get("/openai/models", headers=openai_headers)
    assert response.status_code == 200
    
    # Test OpenAI without authentication (should fail)
    response = client_with_mixed_auth.get("/openai/models")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header"
    
    # Test MCP without authentication (should work - no auth required)
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "mixed-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client_with_mixed_auth.post("/mcp/", json=mcp_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    
    # Test MCP with authentication (should also work - auth is optional)
    mcp_headers = {"Authorization": "Bearer any-key"}  # Any key should work since no auth required
    response = client_with_mixed_auth.post("/mcp/", json=mcp_request, headers=mcp_headers)
    assert response.status_code == 200


def test_integration_error_handling_with_auth(client_with_both_adapters):
    """Test error handling with authentication"""
    # Test OpenAI with wrong API key
    wrong_headers = {"Authorization": "Bearer wrong-key"}
    
    response = client_with_both_adapters.get("/openai/models", headers=wrong_headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"
    
    # Test MCP with wrong API key
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "error-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client_with_both_adapters.post("/mcp/", json=mcp_request, headers=wrong_headers)
    assert response.status_code == 200  # MCP uses 200 for JSON-RPC errors
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32001
    assert "Invalid API key" in data["error"]["message"]


def test_integration_proper_http_status_codes(client_with_both_adapters):
    """Test that proper HTTP status codes are returned"""
    # OpenAI authentication errors should return HTTP 401
    response = client_with_both_adapters.get("/openai/models")
    assert response.status_code == 401
    
    response = client_with_both_adapters.get("/openai/models", headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 401
    
    # OpenAI successful requests should return HTTP 200
    response = client_with_both_adapters.get("/openai/models", headers={"Authorization": "Bearer integration-openai-key"})
    assert response.status_code == 200
    
    # MCP always returns HTTP 200 (JSON-RPC protocol)
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "status-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    # MCP with wrong auth
    response = client_with_both_adapters.post("/mcp/", json=mcp_request, headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 200  # Still 200, but with JSON-RPC error
    
    # MCP with correct auth
    response = client_with_both_adapters.post("/mcp/", json=mcp_request, headers={"Authorization": "Bearer integration-mcp-key"})
    assert response.status_code == 200


def test_integration_environment_variable_fallback(xaibo_with_agents, monkeypatch):
    """Test environment variable fallback in integration scenario"""
    # Set environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "env-openai-integration")
    monkeypatch.setenv("MCP_API_KEY", "env-mcp-integration")
    
    app = FastAPI()
    
    # Create adapters without explicit API keys (should use env vars)
    openai_adapter = OpenAiApiAdapter(xaibo_with_agents)
    openai_adapter.adapt(app)
    
    mcp_adapter = McpApiAdapter(xaibo_with_agents)
    mcp_adapter.adapt(app)
    
    client = TestClient(app)
    
    # Test OpenAI with env var key
    response = client.get("/openai/models", headers={"Authorization": "Bearer env-openai-integration"})
    assert response.status_code == 200
    
    # Test MCP with env var key
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "env-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client.post("/mcp/", json=mcp_request, headers={"Authorization": "Bearer env-mcp-integration"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data


def test_integration_concurrent_requests_with_auth(client_with_both_adapters):
    """Test concurrent requests with authentication"""
    import concurrent.futures
    import threading
    
    def make_openai_request():
        headers = {"Authorization": "Bearer integration-openai-key"}
        response = client_with_both_adapters.get("/openai/models", headers=headers)
        return response.status_code == 200
    
    def make_mcp_request():
        headers = {"Authorization": "Bearer integration-mcp-key"}
        request_data = {
            "jsonrpc": "2.0",
            "id": f"concurrent-{threading.current_thread().ident}",
            "method": "tools/list",
            "params": {}
        }
        response = client_with_both_adapters.post("/mcp/", json=request_data, headers=headers)
        return response.status_code == 200
    
    # Run concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        openai_futures = [executor.submit(make_openai_request) for _ in range(5)]
        mcp_futures = [executor.submit(make_mcp_request) for _ in range(5)]
        
        # Wait for all requests to complete
        openai_results = [future.result() for future in openai_futures]
        mcp_results = [future.result() for future in mcp_futures]
    
    # All requests should succeed
    assert all(openai_results), "Some OpenAI requests failed"
    assert all(mcp_results), "Some MCP requests failed"


def test_integration_malformed_auth_headers(client_with_both_adapters):
    """Test various malformed authentication headers"""
    malformed_headers = [
        {"Authorization": "Basic dGVzdDp0ZXN0"},  # Wrong auth type
        {"Authorization": "Bearertest-key"},      # No space after Bearer
        {"Authorization": "Bearer "},             # Empty key
        {"Authorization": ""},                    # Empty header
        {"Auth": "Bearer test-key"},              # Wrong header name
    ]
    
    for headers in malformed_headers:
        # Test OpenAI
        response = client_with_both_adapters.get("/openai/models", headers=headers)
        assert response.status_code == 401, f"OpenAI should reject malformed header: {headers}"
        
        # Test MCP
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "malformed-test",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            }
        }
        
        response = client_with_both_adapters.post("/mcp/", json=mcp_request, headers=headers)
        assert response.status_code == 200, "MCP should always return 200"
        
        data = response.json()
        assert "error" in data, f"MCP should return error for malformed header: {headers}"
        assert data["error"]["code"] == -32001, "MCP should return auth error code"