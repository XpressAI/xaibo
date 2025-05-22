import asyncio
import json
import subprocess
import uuid
from typing import Any, Dict, List, Optional, Union
import aiohttp
import websockets
from urllib.parse import urlparse

from xaibo.core.models.tools import Tool, ToolParameter, ToolResult
from xaibo.core.protocols.tools import ToolProviderProtocol


class MCPServerConfig:
    """Configuration for an MCP server"""
    
    def __init__(self, name: str, transport: str, **kwargs):
        self.name = name
        self.transport = transport.lower()
        
        if self.transport == "stdio":
            self.command = kwargs.get("command", [])
            self.args = kwargs.get("args", [])
            self.env = kwargs.get("env", {})
        elif self.transport in ["sse", "websocket"]:
            self.url = kwargs.get("url", "")
            self.headers = kwargs.get("headers", {})
        else:
            raise ValueError(f"Unsupported transport type: {transport}")


class MCPClient:
    """Client for communicating with MCP servers"""
    
    def __init__(self, config: MCPServerConfig, timeout: float = 30.0):
        self.config = config
        self.timeout = timeout
        self.process = None
        self.websocket = None
        self.session = None
        self.initialized = False
        
    async def connect(self):
        """Connect to the MCP server"""
        if self.config.transport == "stdio":
            await self._connect_stdio()
        elif self.config.transport == "sse":
            await self._connect_sse()
        elif self.config.transport == "websocket":
            await self._connect_websocket()
        
        # Initialize the MCP protocol
        await self._initialize()
        
    async def _connect_stdio(self):
        """Connect via stdio transport"""
        cmd = self.config.command + self.config.args
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.config.env
        )
        
    async def _connect_sse(self):
        """Connect via SSE transport"""
        self.session = aiohttp.ClientSession(
            headers=self.config.headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        
    async def _connect_websocket(self):
        """Connect via WebSocket transport"""
        self.websocket = await websockets.connect(
            self.config.url,
            additional_headers=self.config.headers
        )
        
    async def _initialize(self):
        """Initialize the MCP protocol with the server"""
        init_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "xaibo-mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(init_request)
        if response.get("error"):
            raise Exception(f"Failed to initialize MCP server: {response['error']}")
            
        self.initialized = True
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_notification(initialized_notification)
        
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for response"""
        if self.config.transport == "stdio":
            return await self._send_stdio_request(request)
        elif self.config.transport == "sse":
            return await self._send_sse_request(request)
        elif self.config.transport == "websocket":
            return await self._send_websocket_request(request)
            
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a JSON-RPC notification (no response expected)"""
        if self.config.transport == "stdio":
            await self._send_stdio_notification(notification)
        elif self.config.transport == "sse":
            await self._send_sse_notification(notification)
        elif self.config.transport == "websocket":
            await self._send_websocket_notification(notification)
            
    async def _send_stdio_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via stdio"""
        if not self.process:
            raise Exception("Process not connected")
            
        message = json.dumps(request) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise Exception("No response from MCP server")
            
        return json.loads(response_line.decode().strip())
        
    async def _send_stdio_notification(self, notification: Dict[str, Any]):
        """Send notification via stdio"""
        if not self.process:
            raise Exception("Process not connected")
            
        message = json.dumps(notification) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
        
    async def _send_sse_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via SSE"""
        if not self.session:
            raise Exception("SSE session not connected")
            
        async with self.session.post(
            self.config.url,
            json=request
        ) as response:
            return await response.json()
            
    async def _send_sse_notification(self, notification: Dict[str, Any]):
        """Send notification via SSE"""
        if not self.session:
            raise Exception("SSE session not connected")
            
        async with self.session.post(
            self.config.url,
            json=notification
        ) as response:
            # Notifications don't expect responses
            pass
            
    async def _send_websocket_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
            
        await self.websocket.send(json.dumps(request))
        response_str = await self.websocket.recv()
        return json.loads(response_str)
        
    async def _send_websocket_notification(self, notification: Dict[str, Any]):
        """Send notification via WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
            
        await self.websocket.send(json.dumps(notification))
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        if not self.initialized:
            raise Exception("MCP client not initialized")
            
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list"
        }
        
        response = await self._send_request(request)
        if response.get("error"):
            raise Exception(f"Failed to list tools: {response['error']}")
            
        return response.get("result", {}).get("tools", [])
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.initialized:
            raise Exception("MCP client not initialized")
            
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        if response.get("error"):
            raise Exception(f"Tool call failed: {response['error']}")
            
        return response.get("result", {})
        
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
            
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        if self.session:
            await self.session.close()
            self.session = None
            
        self.initialized = False


class MCPToolProvider(ToolProviderProtocol):
    """Provider for MCP (Model Context Protocol) tools"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the MCP tool provider
        
        Args:
            config: Configuration dictionary containing:
                servers: List of MCP server configurations
                timeout: Optional timeout for server operations (default: 30.0)
        """
        self.timeout = config.get("timeout", 30.0)
        self.clients: Dict[str, MCPClient] = {}
        self._tools_cache: Optional[List[Tool]] = None
        
        # Initialize MCP clients from server configurations
        servers = config.get("servers", [])
        for server_config in servers:
            if isinstance(server_config, dict):
                name = server_config.get("name")
                if not name:
                    raise ValueError("Server configuration must include 'name'")
                    
                mcp_config = MCPServerConfig(**server_config)
                self.clients[name] = MCPClient(mcp_config, self.timeout)
                
    async def _ensure_connected(self):
        """Ensure all MCP clients are connected"""
        for client in self.clients.values():
            if not client.initialized:
                await client.connect()
                
    async def list_tools(self) -> List[Tool]:
        """List all available tools from connected MCP servers"""
        if self._tools_cache is not None:
            return self._tools_cache
            
        await self._ensure_connected()
        
        tools = []
        for server_name, client in self.clients.items():
            try:
                mcp_tools = await client.list_tools()
                for mcp_tool in mcp_tools:
                    tool = self._convert_mcp_tool_to_xaibo_tool(mcp_tool, server_name)
                    tools.append(tool)
            except Exception as e:
                # Log error but continue with other servers
                print(f"Error listing tools from server {server_name}: {e}")
                continue
                
        self._tools_cache = tools
        return tools
        
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool on the appropriate MCP server
        
        Args:
            tool_name: Name of the tool (format: server_name.tool_name)
            parameters: Parameters to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        await self._ensure_connected()
        
        # Parse server name and tool name from the full tool name
        if "." not in tool_name:
            return ToolResult(
                success=False,
                error=f"Invalid tool name format: {tool_name}. Expected format: server_name.tool_name"
            )
            
        server_name, actual_tool_name = tool_name.split(".", 1)
        
        if server_name not in self.clients:
            return ToolResult(
                success=False,
                error=f"MCP server '{server_name}' not found"
            )
            
        client = self.clients[server_name]
        
        try:
            result = await client.call_tool(actual_tool_name, parameters)
            
            # Extract content from MCP result
            content = result.get("content", [])
            if content:
                # Combine all content items
                combined_result = []
                for item in content:
                    if item.get("type") == "text":
                        combined_result.append(item.get("text", ""))
                    else:
                        combined_result.append(str(item))
                result_value = "\n".join(combined_result) if combined_result else result
            else:
                result_value = result
                
            return ToolResult(success=True, result=result_value)
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
            
    def _convert_mcp_tool_to_xaibo_tool(self, mcp_tool: Dict[str, Any], server_name: str) -> Tool:
        """Convert an MCP tool definition to a xaibo Tool"""
        name = f"{server_name}.{mcp_tool['name']}"
        description = mcp_tool.get("description", "")
        
        # Convert MCP input schema to xaibo ToolParameter format
        parameters = {}
        input_schema = mcp_tool.get("inputSchema", {})
        
        if input_schema.get("type") == "object":
            properties = input_schema.get("properties", {})
            required_fields = set(input_schema.get("required", []))
            
            for param_name, param_def in properties.items():
                param_type = param_def.get("type", "string")
                param_desc = param_def.get("description", "")
                param_required = param_name in required_fields
                param_default = param_def.get("default")
                param_enum = param_def.get("enum")
                
                parameters[param_name] = ToolParameter(
                    type=param_type,
                    description=param_desc,
                    required=param_required,
                    default=param_default,
                    enum=param_enum
                )
                
        return Tool(
            name=name,
            description=description,
            parameters=parameters
        )
        
    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for client in self.clients.values():
            await client.disconnect()
        self._tools_cache = None