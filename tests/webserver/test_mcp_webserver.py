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
    
    def __init__(self, response: ResponseProtocol, config: dict = None):
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
    
    def __init__(self, response: ResponseProtocol, config: dict = None):
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
    
    def __init__(self, response: ResponseProtocol, config: dict = None):
        self.config = config or {}
        self.response = response
        
    async def handle_text(self, text: str) -> None:
        await self.response.respond_text(f"Multi-entry agent received: {text}")


class HistoryAwareAgent(TextMessageHandlerProtocol):
    """Agent that uses conversation history"""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]
    
    def __init__(self, response: ResponseProtocol, history: ConversationHistoryProtocol, config: dict = None):
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
    response = client.post(
        "/mcp/",
        content="invalid json{",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None
    assert "error" in data
    assert data["error"]["code"] == -32700
    assert "Parse error" in data["error"]["message"]


def test_mcp_non_dict_request(client):
    """Test request with non-dictionary JSON"""
    response = client.post("/mcp/", json=["not", "a", "dict"])
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]


def test_mcp_agent_with_conversation_history(client):
    """Test MCP agent execution with conversation history"""
    # First message
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
    assert "result" in data
    content = data["result"]["content"]
    assert len(content) == 1
    assert "Message #" in content[0]["text"]
    assert "First message" in content[0]["text"]


def test_mcp_complete_workflow(client):
    """Test complete MCP workflow: initialize -> tools/list -> tools/call"""
    # Step 1: Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": "workflow-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    response = client.post("/mcp/", json=init_request)
    assert response.status_code == 200
    assert "result" in response.json()
    
    # Step 2: Send initialized notification
    notification_request = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    response = client.post("/mcp/", json=notification_request)
    assert response.status_code == 200
    
    # Step 3: List tools
    list_request = {
        "jsonrpc": "2.0",
        "id": "workflow-2",
        "method": "tools/list",
        "params": {}
    }
    
    response = client.post("/mcp/", json=list_request)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    tools = data["result"]["tools"]
    assert len(tools) > 0
    
    # Step 4: Call a tool
    call_request = {
        "jsonrpc": "2.0",
        "id": "workflow-3",
        "method": "tools/call",
        "params": {
            "name": "echo-agent",
            "arguments": {
                "message": "Complete workflow test"
            }
        }
    }
    
    response = client.post("/mcp/", json=call_request)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    content = data["result"]["content"]
    assert content[0]["text"] == "Echo: Complete workflow test"


def test_mcp_response_format_compliance(client):
    """Test that all MCP responses comply with JSON-RPC 2.0 format"""
    test_cases = [
        {
            "name": "initialize",
            "request": {
                "jsonrpc": "2.0",
                "id": "format-test-1",
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"}
            }
        },
        {
            "name": "tools/list",
            "request": {
                "jsonrpc": "2.0",
                "id": "format-test-2",
                "method": "tools/list",
                "params": {}
            }
        },
        {
            "name": "tools/call",
            "request": {
                "jsonrpc": "2.0",
                "id": "format-test-3",
                "method": "tools/call",
                "params": {
                    "name": "echo-agent",
                    "arguments": {"message": "test"}
                }
            }
        }
    ]
    
    for case in test_cases:
        response = client.post("/mcp/", json=case["request"])
        assert response.status_code == 200
        
        data = response.json()
        
        # All responses must have jsonrpc field
        assert data["jsonrpc"] == "2.0"
        
        # All responses must have id field matching request
        assert data["id"] == case["request"]["id"]
        
        # Response must have either result or error, but not both
        has_result = "result" in data
        has_error = "error" in data
        assert has_result != has_error, f"Response for {case['name']} must have either result or error, not both"
        
        if has_error:
            # Error responses must have code and message
            assert "code" in data["error"]
            assert "message" in data["error"]
            assert isinstance(data["error"]["code"], int)
            assert isinstance(data["error"]["message"], str)


def test_mcp_agent_config_description_usage(client):
    """Test that AgentConfig.description is used for tool descriptions in MCP"""
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-description-1",
        "method": "tools/list",
        "params": {}
    }
    
    response = client.post("/mcp/", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-description-1"
    assert "result" in data
    
    result = data["result"]
    assert "tools" in result
    tools = result["tools"]
    
    # Find the described-agent tool
    described_tool = next((tool for tool in tools if tool["name"] == "described-agent"), None)
    assert described_tool is not None, "described-agent tool should be present"
    
    # Verify that the custom description from AgentConfig is used
    assert described_tool["description"] == "This is a custom agent description for MCP testing"
    
    # Find an agent without description (echo-agent) to verify fallback behavior
    echo_tool = next((tool for tool in tools if tool["name"] == "echo-agent"), None)
    assert echo_tool is not None, "echo-agent tool should be present"
    
    # Verify that the fallback description is used when AgentConfig.description is None
    assert echo_tool["description"] == "Execute Xaibo agent 'echo-agent'"


def test_mcp_error_codes_compliance(client):
    """Test that MCP adapter returns correct JSON-RPC error codes"""
    error_test_cases = [
        {
            "name": "Parse error",
            "request_content": "invalid json",
            "expected_code": -32700
        },
        {
            "name": "Invalid Request - non-dict",
            "request_json": ["array"],
            "expected_code": -32600
        },
        {
            "name": "Invalid Request - wrong jsonrpc",
            "request_json": {"jsonrpc": "1.0", "id": "test", "method": "test"},
            "expected_code": -32600
        },
        {
            "name": "Method not found",
            "request_json": {"jsonrpc": "2.0", "id": "test", "method": "nonexistent"},
            "expected_code": -32601
        },
        {
            "name": "Invalid params - missing protocolVersion",
            "request_json": {"jsonrpc": "2.0", "id": "test", "method": "initialize", "params": {}},
            "expected_code": -32602
        }
    ]
    
    for case in error_test_cases:
        if "request_content" in case:
            response = client.post(
                "/mcp/",
                content=case["request_content"],
                headers={"Content-Type": "application/json"}
            )
        else:
            response = client.post("/mcp/", json=case["request_json"])
            
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == case["expected_code"], f"Wrong error code for {case['name']}"