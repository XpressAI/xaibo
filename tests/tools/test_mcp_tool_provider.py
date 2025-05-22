import asyncio
import pytest
import pytest_asyncio
from typing import Dict, Any

from xaibo.primitives.modules.tools.mcp_tool_provider import (
    MCPServerConfig,
    MCPClient,
    MCPToolProvider
)
from xaibo.core.models.tools import Tool, ToolParameter, ToolResult

from tests.tools.mcp_servers.test_utils import get_server_manager, cleanup_test_servers


class TestMCPServerConfig:
    """Test cases for MCPServerConfig class"""
    
    def test_stdio_config_initialization(self):
        """Test initialization with stdio transport"""
        config = MCPServerConfig(
            name="test-server",
            transport="stdio",
            command=["python", "-m", "test_server"],
            args=["--port", "8080"],
            env={"TEST_VAR": "value"}
        )
        
        assert config.name == "test-server"
        assert config.transport == "stdio"
        assert config.command == ["python", "-m", "test_server"]
        assert config.args == ["--port", "8080"]
        assert config.env == {"TEST_VAR": "value"}
    
    def test_sse_config_initialization(self):
        """Test initialization with SSE transport"""
        config = MCPServerConfig(
            name="sse-server",
            transport="SSE",  # Test case insensitive
            url="http://localhost:8080/sse",
            headers={"Authorization": "Bearer token"}
        )
        
        assert config.name == "sse-server"
        assert config.transport == "sse"
        assert config.url == "http://localhost:8080/sse"
        assert config.headers == {"Authorization": "Bearer token"}
    
    def test_websocket_config_initialization(self):
        """Test initialization with WebSocket transport"""
        config = MCPServerConfig(
            name="ws-server",
            transport="websocket",
            url="ws://localhost:8080/ws",
            headers={"X-API-Key": "secret"}
        )
        
        assert config.name == "ws-server"
        assert config.transport == "websocket"
        assert config.url == "ws://localhost:8080/ws"
        assert config.headers == {"X-API-Key": "secret"}
    
    def test_unsupported_transport_raises_error(self):
        """Test that unsupported transport types raise ValueError"""
        with pytest.raises(ValueError, match="Unsupported transport type: invalid"):
            MCPServerConfig(name="test", transport="invalid")
    
    def test_stdio_config_defaults(self):
        """Test stdio config with default values"""
        config = MCPServerConfig(name="test", transport="stdio")
        
        assert config.command == []
        assert config.args == []
        assert config.env == {}
    
    def test_sse_config_defaults(self):
        """Test SSE config with default values"""
        config = MCPServerConfig(name="test", transport="sse")
        
        assert config.url == ""
        assert config.headers == {}


class TestMCPClient:
    """Test cases for MCPClient class using real MCP servers"""
    
    @pytest_asyncio.fixture
    async def stdio_server(self):
        """Start a real stdio MCP server for testing"""
        manager = get_server_manager()
        name, command = await manager.start_stdio_server("test_stdio")
        config = MCPServerConfig(
            name=name,
            transport="stdio",
            command=command
        )
        yield config
        await manager.stop_server(name)
    
    @pytest_asyncio.fixture
    async def websocket_server(self):
        """Start a real WebSocket MCP server for testing"""
        manager = get_server_manager()
        name, url, port = await manager.start_websocket_server("test_ws")
        config = MCPServerConfig(
            name=name,
            transport="websocket",
            url=url
        )
        yield config
        await manager.stop_server(name)
    
    @pytest_asyncio.fixture
    async def sse_server(self):
        """Start a real SSE MCP server for testing"""
        manager = get_server_manager()
        name, url, port = await manager.start_sse_server("test_sse")
        config = MCPServerConfig(
            name=name,
            transport="sse",
            url=url
        )
        yield config
        await manager.stop_server(name)
    
    def test_client_initialization(self, stdio_server):
        """Test MCPClient initialization"""
        client = MCPClient(stdio_server, timeout=60.0)
        
        assert client.config == stdio_server
        assert client.timeout == 60.0
        assert client.process is None
        assert client.websocket is None
        assert client.session is None
        assert client.initialized is False
    
    @pytest.mark.asyncio
    async def test_connect_stdio(self, stdio_server):
        """Test connecting via stdio transport with real server"""
        client = MCPClient(stdio_server)
        await client.connect()
        
        assert client.process is not None
        assert client.initialized is True
        
        # Cleanup
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, websocket_server):
        """Test connecting via WebSocket transport with real server"""
        client = MCPClient(websocket_server)
        await client.connect()
        
        assert client.websocket is not None
        assert client.initialized is True
        
        # Cleanup
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connect_sse(self, sse_server):
        """Test connecting via SSE transport with real server"""
        client = MCPClient(sse_server)
        await client.connect()
        
        assert client.session is not None
        assert client.initialized is True
        
        # Cleanup
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_list_tools_stdio(self, stdio_server):
        """Test listing tools from real stdio server"""
        client = MCPClient(stdio_server)
        await client.connect()
        
        try:
            tools = await client.list_tools()
            
            assert len(tools) >= 1
            # Check for expected tools from stdio_server.py
            tool_names = [tool["name"] for tool in tools]
            assert "test_tool" in tool_names
            assert "echo_tool" in tool_names
            
            # Verify tool structure
            test_tool = next(tool for tool in tools if tool["name"] == "test_tool")
            assert test_tool["description"] == "A test tool for stdio server"
            assert "inputSchema" in test_tool
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_list_tools_websocket(self, websocket_server):
        """Test listing tools from real WebSocket server"""
        client = MCPClient(websocket_server)
        await client.connect()
        
        try:
            tools = await client.list_tools()
            
            assert len(tools) >= 1
            # Check for expected tools from websocket_server.py
            tool_names = [tool["name"] for tool in tools]
            assert "ws_tool" in tool_names
            assert "multi_content_tool" in tool_names
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_list_tools_sse(self, sse_server):
        """Test listing tools from real SSE server"""
        client = MCPClient(sse_server)
        await client.connect()
        
        try:
            tools = await client.list_tools()
            
            assert len(tools) >= 1
            # Check for expected tools from sse_server.py
            tool_names = [tool["name"] for tool in tools]
            assert "sse_tool" in tool_names
            assert "no_content_tool" in tool_names
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_call_tool_stdio(self, stdio_server):
        """Test calling a tool on real stdio server"""
        client = MCPClient(stdio_server)
        await client.connect()
        
        try:
            result = await client.call_tool("test_tool", {"param1": "test_value"})
            
            assert "content" in result
            assert len(result["content"]) == 1
            assert result["content"][0]["type"] == "text"
            assert "test_value" in result["content"][0]["text"]
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_call_tool_websocket(self, websocket_server):
        """Test calling a tool on real WebSocket server"""
        client = MCPClient(websocket_server)
        await client.connect()
        
        try:
            result = await client.call_tool("ws_tool", {"data": "websocket_data"})
            
            assert "content" in result
            assert len(result["content"]) == 1
            assert result["content"][0]["type"] == "text"
            assert "websocket_data" in result["content"][0]["text"]
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_call_tool_sse(self, sse_server):
        """Test calling a tool on real SSE server"""
        client = MCPClient(sse_server)
        await client.connect()
        
        try:
            result = await client.call_tool("sse_tool", {"input": "sse_input"})
            
            assert "content" in result
            assert len(result["content"]) == 1
            assert result["content"][0]["type"] == "text"
            assert "sse_input" in result["content"][0]["text"]
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_call_tool_error(self, stdio_server):
        """Test tool call error handling with real server"""
        client = MCPClient(stdio_server)
        await client.connect()
        
        try:
            with pytest.raises(Exception, match="Tool not found"):
                await client.call_tool("nonexistent_tool", {})
                
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_call_tool_not_initialized(self):
        """Test calling tool when client is not initialized"""
        config = MCPServerConfig(name="test", transport="stdio", command=["echo"])
        client = MCPClient(config)
        
        with pytest.raises(Exception, match="MCP client not initialized"):
            await client.call_tool("test_tool", {})
    
    @pytest.mark.asyncio
    async def test_list_tools_not_initialized(self):
        """Test listing tools when client is not initialized"""
        config = MCPServerConfig(name="test", transport="stdio", command=["echo"])
        client = MCPClient(config)
        
        with pytest.raises(Exception, match="MCP client not initialized"):
            await client.list_tools()
    
    @pytest.mark.asyncio
    async def test_disconnect_stdio(self, stdio_server):
        """Test disconnecting from stdio server"""
        client = MCPClient(stdio_server)
        await client.connect()
        
        assert client.process is not None
        assert client.initialized is True
        
        await client.disconnect()
        
        assert client.process is None
        assert client.initialized is False
    
    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, websocket_server):
        """Test disconnecting from WebSocket server"""
        client = MCPClient(websocket_server)
        await client.connect()
        
        assert client.websocket is not None
        assert client.initialized is True
        
        await client.disconnect()
        
        assert client.websocket is None
        assert client.initialized is False
    
    @pytest.mark.asyncio
    async def test_disconnect_sse(self, sse_server):
        """Test disconnecting from SSE server"""
        client = MCPClient(sse_server)
        await client.connect()
        
        assert client.session is not None
        assert client.initialized is True
        
        await client.disconnect()
        
        assert client.session is None
        assert client.initialized is False


class TestMCPToolProvider:
    """Test cases for MCPToolProvider class using real MCP servers"""
    
    @pytest_asyncio.fixture
    async def multi_server_setup(self):
        """Setup multiple real MCP servers for testing"""
        manager = get_server_manager()
        
        # Start servers (using two stdio servers for now)
        stdio_name1, stdio_command1 = await manager.start_stdio_server("provider_stdio1")
        stdio_name2, stdio_command2 = await manager.start_stdio_server("provider_stdio2")
        
        config = {
            "timeout": 30.0,
            "servers": [
                {
                    "name": stdio_name1,
                    "transport": "stdio",
                    "command": stdio_command1
                },
                {
                    "name": stdio_name2,
                    "transport": "stdio",
                    "command": stdio_command2
                }
            ]
        }
        
        yield config
        
        # Cleanup
        await manager.stop_server(stdio_name1)
        await manager.stop_server(stdio_name2)
    
    @pytest_asyncio.fixture
    async def single_server_setup(self):
        """Setup single real MCP server for testing"""
        manager = get_server_manager()
        
        stdio_name, stdio_command = await manager.start_stdio_server("single_stdio")
        
        config = {
            "servers": [
                {
                    "name": stdio_name,
                    "transport": "stdio",
                    "command": stdio_command
                }
            ]
        }
        
        yield config
        
        await manager.stop_server(stdio_name)
    
    def test_provider_initialization(self, multi_server_setup):
        """Test MCPToolProvider initialization with real server configs"""
        provider = MCPToolProvider(multi_server_setup)
        
        assert provider.timeout == 30.0
        assert len(provider.clients) == 2
        assert "provider_stdio1" in provider.clients
        assert "provider_stdio2" in provider.clients
        assert provider._tools_cache is None
    
    def test_provider_initialization_missing_name(self):
        """Test provider initialization with missing server name"""
        config = {
            "servers": [
                {
                    "transport": "stdio",
                    "command": ["python", "-m", "server"]
                }
            ]
        }
        
        with pytest.raises(ValueError, match="Server configuration must include 'name'"):
            MCPToolProvider(config)
    
    def test_provider_initialization_defaults(self):
        """Test provider initialization with default values"""
        provider = MCPToolProvider({})
        
        assert provider.timeout == 30.0
        assert len(provider.clients) == 0
        assert provider._tools_cache is None
    
    @pytest.mark.asyncio
    async def test_list_tools(self, multi_server_setup):
        """Test listing tools from multiple real servers"""
        provider = MCPToolProvider(multi_server_setup)
        
        try:
            tools = await provider.list_tools()
            
            # Should have tools from both servers
            assert len(tools) >= 4  # At least 2 from each server
            
            # Check for tools from first stdio server
            stdio_tools1 = [t for t in tools if t.name.startswith("provider_stdio1.")]
            assert len(stdio_tools1) >= 2
            
            # Check for tools from second stdio server
            stdio_tools2 = [t for t in tools if t.name.startswith("provider_stdio2.")]
            assert len(stdio_tools2) >= 2
            
            # Verify tool structure
            test_tool = next((t for t in tools if t.name.endswith(".test_tool")), None)
            assert test_tool is not None
            assert test_tool.description == "A test tool for stdio server"
            assert "param1" in test_tool.parameters
            assert test_tool.parameters["param1"].required is True
            assert test_tool.parameters["param1"].type == "string"
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_list_tools_caching(self, single_server_setup):
        """Test that tools are cached after first call"""
        provider = MCPToolProvider(single_server_setup)
        
        try:
            # First call
            tools1 = await provider.list_tools()
            # Second call
            tools2 = await provider.list_tools()
            
            assert tools1 == tools2
            assert provider._tools_cache is not None
            assert len(provider._tools_cache) == len(tools1)
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_execute_tool_success(self, single_server_setup):
        """Test successful tool execution with real server"""
        provider = MCPToolProvider(single_server_setup)
        
        try:
            result = await provider.execute_tool("single_stdio.test_tool", {"param1": "test_value"})
            
            assert result.success is True
            assert "test_value" in result.result
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_execute_tool_multiple_content_items(self, single_server_setup):
        """Test tool execution with multiple content items using real server"""
        provider = MCPToolProvider(single_server_setup)
        
        try:
            # Use echo_tool to test multiple calls
            result1 = await provider.execute_tool("single_stdio.echo_tool", {"message": "first"})
            result2 = await provider.execute_tool("single_stdio.echo_tool", {"message": "second"})
            
            assert result1.success is True
            assert result2.success is True
            assert "first" in result1.result
            assert "second" in result2.result
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_execute_tool_no_content(self, single_server_setup):
        """Test tool execution with no content in result using real SSE server"""
        manager = get_server_manager()
        sse_name, sse_url, sse_port = await manager.start_sse_server("no_content_test")
        
        config = {
            "servers": [
                {
                    "name": sse_name,
                    "transport": "sse",
                    "url": sse_url
                }
            ]
        }
        
        provider = MCPToolProvider(config)
        
        try:
            result = await provider.execute_tool("no_content_test.no_content_tool", {"status": "ok"})
            
            assert result.success is True
            # Should return the raw result when no content field
            assert isinstance(result.result, dict)
            assert result.result.get("status") == "ok"
            
        finally:
            await provider.disconnect_all()
            await manager.stop_server(sse_name)
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_name_format(self, single_server_setup):
        """Test tool execution with invalid name format"""
        provider = MCPToolProvider(single_server_setup)
        
        try:
            result = await provider.execute_tool("invalid_tool_name", {})
            
            assert result.success is False
            assert "Invalid tool name format" in result.error
            assert "server_name.tool_name" in result.error
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_execute_tool_server_not_found(self, single_server_setup):
        """Test tool execution with non-existent server"""
        provider = MCPToolProvider(single_server_setup)
        
        try:
            result = await provider.execute_tool("nonexistent.tool", {})
            
            assert result.success is False
            assert "MCP server 'nonexistent' not found" in result.error
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_execute_tool_client_error(self, single_server_setup):
        """Test tool execution when tool doesn't exist on server"""
        provider = MCPToolProvider(single_server_setup)
        
        try:
            result = await provider.execute_tool("single_stdio.nonexistent_tool", {})
            
            assert result.success is False
            assert "Tool not found" in result.error
            
        finally:
            await provider.disconnect_all()
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self, multi_server_setup):
        """Test disconnecting from all servers"""
        provider = MCPToolProvider(multi_server_setup)
        
        # Connect to servers by listing tools
        await provider.list_tools()
        
        # Verify clients are connected
        for client in provider.clients.values():
            assert client.initialized is True
        
        await provider.disconnect_all()
        
        # Verify all clients are disconnected
        for client in provider.clients.values():
            assert client.initialized is False
        
        assert provider._tools_cache is None
    
    def test_convert_mcp_tool_to_xaibo_tool(self):
        """Test conversion from MCP tool format to xaibo Tool format"""
        provider = MCPToolProvider({})
        
        mcp_tool = {
            "name": "test_tool",
            "description": "A test tool for conversion",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "required_param": {
                        "type": "string",
                        "description": "A required parameter"
                    },
                    "optional_param": {
                        "type": "integer",
                        "description": "An optional parameter",
                        "default": 42
                    },
                    "enum_param": {
                        "type": "string",
                        "description": "Parameter with enum values",
                        "enum": ["option1", "option2", "option3"]
                    }
                },
                "required": ["required_param"]
            }
        }
        
        tool = provider._convert_mcp_tool_to_xaibo_tool(mcp_tool, "test-server")
        
        assert tool.name == "test-server.test_tool"
        assert tool.description == "A test tool for conversion"
        assert len(tool.parameters) == 3
        
        # Check required parameter
        assert "required_param" in tool.parameters
        req_param = tool.parameters["required_param"]
        assert req_param.type == "string"
        assert req_param.description == "A required parameter"
        assert req_param.required is True
        assert req_param.default is None
        assert req_param.enum is None
        
        # Check optional parameter
        assert "optional_param" in tool.parameters
        opt_param = tool.parameters["optional_param"]
        assert opt_param.type == "integer"
        assert opt_param.description == "An optional parameter"
        assert opt_param.required is False
        assert opt_param.default == 42
        
        # Check enum parameter
        assert "enum_param" in tool.parameters
        enum_param = tool.parameters["enum_param"]
        assert enum_param.type == "string"
        assert enum_param.required is False
        assert enum_param.enum == ["option1", "option2", "option3"]
    
    def test_convert_mcp_tool_minimal(self):
        """Test conversion of minimal MCP tool"""
        provider = MCPToolProvider({})
        
        mcp_tool = {
            "name": "minimal_tool"
        }
        
        tool = provider._convert_mcp_tool_to_xaibo_tool(mcp_tool, "server")
        
        assert tool.name == "server.minimal_tool"
        assert tool.description == ""
        assert len(tool.parameters) == 0
    
    def test_convert_mcp_tool_non_object_schema(self):
        """Test conversion of MCP tool with non-object input schema"""
        provider = MCPToolProvider({})
        
        mcp_tool = {
            "name": "simple_tool",
            "description": "Simple tool",
            "inputSchema": {
                "type": "string"
            }
        }
        
        tool = provider._convert_mcp_tool_to_xaibo_tool(mcp_tool, "server")
        
        assert tool.name == "server.simple_tool"
        assert tool.description == "Simple tool"
        assert len(tool.parameters) == 0


# Cleanup fixture to ensure all test servers are stopped
@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_servers():
    """Cleanup all test servers after test session"""
    yield
    await cleanup_test_servers()