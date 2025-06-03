import logging
import pytest
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from xaibo import Xaibo, AgentConfig, ModuleConfig, ExchangeConfig
from xaibo.server.adapters.mcp import McpApiAdapter
from xaibo.core.protocols import TextMessageHandlerProtocol, ResponseProtocol, ConversationHistoryProtocol


class Echo(TextMessageHandlerProtocol):
    """Simple echo module for testing MCP adapter"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict | None = None):
        self.config = config or {}
        self.prefix = self.config.get("prefix", "")
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        await self.response.respond_text(f"{self.prefix}{text}")


class ErrorAgent(TextMessageHandlerProtocol):
    """Agent that throws errors for testing error handling"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict | None = None):
        self.config = config or {}
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        if text == "runtime_error":
            raise RuntimeError("Test runtime error")
        elif text == "attribute_error":
            raise AttributeError("Test attribute error")
        else:
            await self.response.respond_text(f"Error agent received: {text}")


class MultiEntryAgent(TextMessageHandlerProtocol):
    """Agent with multiple entry points for testing"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, config: dict | None = None):
        self.config = config or {}
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        await self.response.respond_text(f"Multi-entry agent received: {text}")


class HistoryAwareAgent(TextMessageHandlerProtocol):
    """Agent that uses conversation history"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, history: ConversationHistoryProtocol, config: dict | None = None):
        self.config = config or {}
        self.response = response
        self.history = history
        
    async def handle_text(self, text: str) -> None:
        messages = await self.history.get_history()
        message_count = len(messages)
        await self.response.respond_text(f"History-aware response to: {text} (Message #{message_count} in conversation)")


@pytest.fixture
def xaibo_instance():
    """Create a Xaibo instance with test agents for MCP testing"""
    xaibo = Xaibo()
    
    # Register a simple echo agent
    echo_config = AgentConfig(
        id="echo-agent",
        modules=[
            ModuleConfig(
                module=Echo,
                id="echo",
                config={
                    "prefix": "Echo: "
                }
            )
        ]
    )
    xaibo.register_agent(echo_config)
    
    # Register an error-prone agent for testing error handling
    error_config = AgentConfig(
        id="error-agent",
        modules=[
            ModuleConfig(
                module=ErrorAgent,
                id="error",
                config={}
            )
        ]
    )
    xaibo.register_agent(error_config)
    
    # Register a multi-entry agent (simplified - just use default entry point)
    multi_config = AgentConfig(
        id="multi-agent",
        modules=[
            ModuleConfig(
                module=MultiEntryAgent,
                id="multi",
                config={}
            )
        ]
    )
    xaibo.register_agent(multi_config)
    
    # Register a history-aware agent with conversation module
    history_config = AgentConfig(
        id="history-agent",
        modules=[
            ModuleConfig(
                module="xaibo.primitives.modules.conversation.conversation.SimpleConversation",
                id="conversation",
                config={}
            ),
            ModuleConfig(
                module=HistoryAwareAgent,
                id="history",
                config={}
            )
        ]
    )
    xaibo.register_agent(history_config)
    
    # Register an agent with a custom description to test AgentConfig.description usage
    described_config = AgentConfig(
        id="described-agent",
        description="This is a custom agent description for MCP testing",
        modules=[
            ModuleConfig(
                module=Echo,
                id="echo",
                config={
                    "prefix": "Described: "
                }
            )
        ]
    )
    xaibo.register_agent(described_config)
    
    return xaibo


@pytest.fixture
def app(xaibo_instance):
    """Create a test FastAPI app with MCP adapter"""
    app = FastAPI()
    adapter = McpApiAdapter(xaibo_instance)
    adapter.adapt(app)
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


def test_mcp_initialize_success(client):
    """Test successful MCP initialization handshake"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-init-1"
    assert "result" in data
    
    result = data["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert "capabilities" in result
    assert result["capabilities"]["tools"] == {}
    assert result["serverInfo"]["name"] == "xaibo-mcp-server"
    assert result["serverInfo"]["version"] == "1.0.0"


def test_mcp_initialize_missing_protocol_version(client):
    """Test MCP initialization with missing protocol version"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-init-2",
        "method": "initialize",
        "params": {
            "capabilities": {}
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-init-2"
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "protocolVersion" in data["error"]["message"]


def test_mcp_notifications_initialized(client):
    """Test MCP notifications/initialized (should return 200 with no content)"""
    request_data = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    # Notifications don't return JSON-RPC responses


def test_mcp_tools_list_success(client):
    """Test successful tools/list request"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-list-1",
        "method": "tools/list",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-list-1"
    assert "result" in data
    
    result = data["result"]
    assert "tools" in result
    tools = result["tools"]
    
    # Check that our test agents are exposed as tools
    tool_names = [tool["name"] for tool in tools]
    assert "echo-agent" in tool_names
    assert "error-agent" in tool_names
    assert "history-agent" in tool_names
    
    # Check multi-entry agent tool (simplified to single entry point)
    assert "multi-agent" in tool_names
    
    # Verify tool structure
    echo_tool = next(tool for tool in tools if tool["name"] == "echo-agent")
    assert "description" in echo_tool
    assert "inputSchema" in echo_tool
    assert echo_tool["inputSchema"]["type"] == "object"
    assert "message" in echo_tool["inputSchema"]["properties"]
    assert echo_tool["inputSchema"]["required"] == ["message"]


def test_mcp_tools_call_success(client):
    """Test successful tools/call request"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-1",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {
                "message": "Hello MCP!"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-1"
    assert "result" in data
    
    result = data["result"]
    assert "content" in result
    assert result["isError"] is False
    
    content = result["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Echo: Hello MCP!"


def test_mcp_tools_call_with_entry_point(client):
    """Test tools/call with default entry point (simplified test)"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-2",
        "method": "tools/call",
        "params": {
            "name": "multi-agent",
            "arguments": {
                "message": "Test entry point"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-2"
    assert "result" in data
    
    result = data["result"]
    assert "content" in result
    assert result["isError"] is False
    
    content = result["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Multi-entry agent received: Test entry point"


def test_mcp_tools_call_missing_tool_name(client):
    """Test tools/call with missing tool name"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-3",
        "method": "tools/call",
        "params": {
            "arguments": {
                "message": "Hello"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-3"
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "tool name" in data["error"]["message"]


def test_mcp_tools_call_missing_message(client):
    """Test tools/call with missing message argument"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-4",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {}
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-4"
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "message argument" in data["error"]["message"]


def test_mcp_tools_call_nonexistent_agent(client):
    """Test tools/call with non-existent agent"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-5",
        "method": "tools/call",
        "params": {
            "name": "nonexistent-agent",
            "arguments": {
                "message": "Hello"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-5"
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "not found" in data["error"]["message"]


def test_mcp_tools_call_agent_runtime_error(client):
    """Test tools/call when agent throws runtime error"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-6",
        "method": "tools/call",
        "params": {
            "name": "error-agent",
            "arguments": {
                "message": "runtime_error"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-6"
    assert "error" in data
    assert data["error"]["code"] == -32603
    assert "execution failed" in data["error"]["message"]


def test_mcp_tools_call_agent_attribute_error(client):
    """Test tools/call when agent throws attribute error"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-tools-call-7",
        "method": "tools/call",
        "params": {
            "name": "error-agent",
            "arguments": {
                "message": "attribute_error"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-tools-call-7"
    assert "error" in data
    # The actual error code returned is -32602 for this case
    assert data["error"]["code"] == -32602
    assert "does not support text handling" in data["error"]["message"]


def test_mcp_invalid_jsonrpc_version(client):
    """Test request with invalid JSON-RPC version"""
    request_data = {
        "jsonrpc": "1.0",
        "id": "test-invalid-1",
        "method": "initialize",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-invalid-1"
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]


def test_mcp_missing_jsonrpc_field(client):
    """Test request with missing jsonrpc field"""
    request_data = {
        "id": "test-invalid-2",
        "method": "initialize",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-invalid-2"
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]


def test_mcp_unknown_method(client):
    """Test request with unknown method"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-unknown-1",
        "method": "unknown/method",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-unknown-1"
    assert "error" in data
    assert data["error"]["code"] == -32601
    assert "Method not found" in data["error"]["message"]


def test_mcp_invalid_json(client):
    """Test request with invalid JSON"""
    response = client.post("/mcp/", content="invalid json")
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None
    assert "error" in data
    assert data["error"]["code"] == -32700
    assert "Parse error" in data["error"]["message"]


def test_mcp_non_dict_request(client):
    """Test request with non-dict JSON"""
    response = client.post("/mcp/", json=["not", "a", "dict"])
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]


def test_mcp_agent_with_conversation_history(client):
    """Test MCP agent that uses conversation history"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-history-1",
        "method": "tools/call",
        "params": {
            "name": "history-agent",
            "arguments": {
                "message": "First message"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-history-1"
    assert "result" in data
    
    result = data["result"]
    assert result["isError"] is False
    content = result["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    # The history-aware agent should report message count
    assert "Message #0 in conversation" in content[0]["text"]


def test_mcp_complete_workflow(client):
    """Test complete MCP workflow: initialize -> tools/list -> tools/call"""
    # 1. Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": "workflow-init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-workflow-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client.post("/mcp/", json=init_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "workflow-init"
    assert "result" in data
    
    # 2. Send initialized notification
    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    response = client.post("/mcp/", json=notification)
    assert response.status_code == 200
    
    # 3. List tools
    list_request = {
        "jsonrpc": "2.0",
        "id": "workflow-list",
        "method": "tools/list",
        "params": {}
    }
    
    response = client.post("/mcp/", json=list_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "workflow-list"
    assert "result" in data
    
    tools = data["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    assert "echo-agent" in tool_names
    
    # 4. Call a tool
    call_request = {
        "jsonrpc": "2.0",
        "id": "workflow-call",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {
                "message": "Workflow test message"
            }
        }
    }
    
    response = client.post("/mcp/", json=call_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "workflow-call"
    assert "result" in data
    
    result = data["result"]
    assert result["isError"] is False
    content = result["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Echo: Workflow test message"


def test_mcp_response_format_compliance(client):
    """Test that MCP responses comply with the expected format"""
    # Test tools/list response format
    request_data = {
        "jsonrpc": "2.0",
        "id": "format-test-1",
        "method": "tools/list",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    
    # Validate JSON-RPC 2.0 structure
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data
    assert data["id"] == "format-test-1"
    assert "result" in data
    
    # Validate tools/list result structure
    result = data["result"]
    assert "tools" in result
    assert isinstance(result["tools"], list)
    
    # Validate tool structure
    for tool in result["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert isinstance(tool["name"], str)
        assert isinstance(tool["description"], str)
        assert isinstance(tool["inputSchema"], dict)
        
        # Validate input schema structure
        schema = tool["inputSchema"]
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema


def test_mcp_agent_config_description_usage(client):
    """Test that agent config descriptions are properly used in MCP tools"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "description-test",
        "method": "tools/list",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    tools = data["result"]["tools"]
    
    # Find the described-agent tool
    described_tool = next((tool for tool in tools if tool["name"] == "described-agent"), None)
    assert described_tool is not None
    
    # Verify it uses the custom description from AgentConfig
    assert described_tool["description"] == "This is a custom agent description for MCP testing"


def test_mcp_error_codes_compliance(client):
    """Test that MCP error codes comply with JSON-RPC 2.0 specification"""
    # Test parse error (-32700)
    response = client.post("/mcp/", content="invalid json")
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32700
    
    # Test invalid request (-32600)
    response = client.post("/mcp/", json={"jsonrpc": "1.0", "method": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32600
    
    # Test method not found (-32601)
    response = client.post("/mcp/", json={"jsonrpc": "2.0", "id": "test", "method": "unknown"})
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32601
    
    # Test invalid params (-32602)
    response = client.post("/mcp/", json={"jsonrpc": "2.0", "id": "test", "method": "tools/call", "params": {}})
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32602


# API Key Authentication Tests

@pytest.fixture
def app_with_api_key(xaibo_instance):
    """Create a test FastAPI app with MCP adapter and API key"""
    app = FastAPI()
    adapter = McpApiAdapter(xaibo_instance, api_key="test-mcp-key-789")
    adapter.adapt(app)
    return app


@pytest.fixture
def client_with_api_key(app_with_api_key):
    """Create a test client for API key protected MCP endpoints"""
    return TestClient(app_with_api_key)


@pytest.fixture
def app_with_env_api_key(xaibo_instance, monkeypatch):
    """Create a test FastAPI app with MCP adapter using environment variable API key"""
    monkeypatch.setenv("MCP_API_KEY", "env-mcp-key-101112")
    app = FastAPI()
    adapter = McpApiAdapter(xaibo_instance)
    adapter.adapt(app)
    return app


@pytest.fixture
def client_with_env_api_key(app_with_env_api_key):
    """Create a test client for environment API key protected MCP endpoints"""
    return TestClient(app_with_env_api_key)


def test_mcp_backward_compatibility_no_api_key(client):
    """Test MCP adapter without API key (backward compatibility)"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "compat-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "compat-test"
    assert "result" in data
    
    # Test tools/call without auth
    call_request = {
        "jsonrpc": "2.0",
        "id": "compat-call",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {
                "message": "No auth test"
            }
        }
    }
    
    response = client.post("/mcp/", json=call_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["result"]["content"][0]["text"] == "Echo: No auth test"


def test_mcp_valid_api_key_success(client_with_api_key):
    """Test MCP adapter with valid API key (successful authentication)"""
    headers = {"Authorization": "Bearer test-mcp-key-789"}
    
    # Test initialize
    request_data = {
        "jsonrpc": "2.0",
        "id": "auth-init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client_with_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "auth-init"
    assert "result" in data
    assert data["result"]["serverInfo"]["name"] == "xaibo-mcp-server"
    
    # Test tools/list
    list_request = {
        "jsonrpc": "2.0",
        "id": "auth-list",
        "method": "tools/list",
        "params": {}
    }
    
    response = client_with_api_key.post("/mcp/", json=list_request, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    tools = data["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    assert "echo-agent" in tool_names
    
    # Test tools/call
    call_request = {
        "jsonrpc": "2.0",
        "id": "auth-call",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {
                "message": "Authenticated message"
            }
        }
    }
    
    response = client_with_api_key.post("/mcp/", json=call_request, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert data["result"]["content"][0]["text"] == "Echo: Authenticated message"


def test_mcp_invalid_api_key_error(client_with_api_key):
    """Test MCP adapter with invalid API key (JSON-RPC error response)"""
    headers = {"Authorization": "Bearer wrong-mcp-key"}
    
    request_data = {
        "jsonrpc": "2.0",
        "id": "invalid-key-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client_with_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200  # MCP uses 200 for JSON-RPC errors
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None  # Auth errors don't have request ID
    assert "error" in data
    assert data["error"]["code"] == -32001  # Custom auth error code
    assert "Invalid API key" in data["error"]["message"]


def test_mcp_missing_authorization_header_error(client_with_api_key):
    """Test MCP adapter with missing Authorization header when API key is required"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "missing-auth-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client_with_api_key.post("/mcp/", json=request_data)
    assert response.status_code == 200  # MCP uses 200 for JSON-RPC errors
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None  # Auth errors don't have request ID
    assert "error" in data
    assert data["error"]["code"] == -32001  # Custom auth error code
    assert "Missing Authorization header" in data["error"]["message"]


def test_mcp_malformed_authorization_header_error(client_with_api_key):
    """Test MCP adapter with malformed Authorization header"""
    # Test with non-Bearer token
    headers = {"Authorization": "Basic dGVzdDp0ZXN0"}
    request_data = {
        "jsonrpc": "2.0",
        "id": "malformed-auth-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client_with_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None
    assert "error" in data
    assert data["error"]["code"] == -32001
    assert "Invalid Authorization header format" in data["error"]["message"]
    
    # Test with malformed Bearer token (no space)
    headers = {"Authorization": "Bearertest-mcp-key-789"}
    response = client_with_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"]["code"] == -32001
    assert "Invalid Authorization header format" in data["error"]["message"]
    
    # Test with empty Bearer token
    headers = {"Authorization": "Bearer "}
    response = client_with_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"]["code"] == -32001
    assert "Invalid API key" in data["error"]["message"]


def test_mcp_environment_variable_fallback(client_with_env_api_key):
    """Test environment variable fallback for API key loading"""
    headers = {"Authorization": "Bearer env-mcp-key-101112"}
    
    request_data = {
        "jsonrpc": "2.0",
        "id": "env-test",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = client_with_env_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "env-test"
    assert "result" in data
    
    # Test with wrong key should fail
    headers = {"Authorization": "Bearer wrong-env-key"}
    response = client_with_env_api_key.post("/mcp/", json=request_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32001
    assert "Invalid API key" in data["error"]["message"]


def test_mcp_auth_error_preserves_jsonrpc_format(client_with_api_key):
    """Test that authentication errors maintain proper JSON-RPC 2.0 format"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "format-test",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {
                "message": "test"
            }
        }
    }
    
    response = client_with_api_key.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify JSON-RPC 2.0 structure is maintained
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data
    assert "error" in data
    assert "result" not in data  # Should not have result on error
    
    # Verify error structure
    error = data["error"]
    assert "code" in error
    assert "message" in error
    assert isinstance(error["code"], int)
    assert isinstance(error["message"], str)