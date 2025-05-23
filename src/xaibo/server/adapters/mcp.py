import json
import time
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse

from xaibo import Xaibo

logger = logging.getLogger(__name__)


class McpApiAdapter:
    """MCP (Model Context Protocol) adapter that exposes Xaibo agents as MCP tools"""
    
    def __init__(self, xaibo: Xaibo):
        """Initialize the MCP adapter
        
        Args:
            xaibo: The Xaibo instance containing registered agents
        """
        self.xaibo = xaibo
        self.router = APIRouter()
        
        # Register MCP protocol routes
        self.router.add_api_route("/", self.handle_mcp_request, methods=["POST"])
        
    def adapt(self, app: FastAPI):
        """Integrate the MCP adapter with the FastAPI app
        
        Args:
            app: The FastAPI application instance
        """
        app.include_router(self.router, prefix="/mcp")
        
    async def handle_mcp_request(self, request: Request):
        """Handle incoming MCP JSON-RPC 2.0 requests
        
        Args:
            request: The FastAPI request object
            
        Returns:
            JSON-RPC 2.0 response
        """
        try:
            data = await request.json()
            
            # Handle JSON-RPC 2.0 request
            if not isinstance(data, dict):
                return self._create_error_response(None, -32600, "Invalid Request")
                
            jsonrpc = data.get("jsonrpc")
            if jsonrpc != "2.0":
                return self._create_error_response(data.get("id"), -32600, "Invalid Request")
                
            method = data.get("method")
            request_id = data.get("id")
            params = data.get("params", {})
            
            # Handle different MCP methods
            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            elif method == "notifications/initialized":
                # Notification - no response needed
                return JSONResponse(content=None, status_code=200)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id, params)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            else:
                return self._create_error_response(request_id, -32601, "Method not found")
                
        except json.JSONDecodeError:
            return self._create_error_response(None, -32700, "Parse error")
        except Exception as e:
            logger.exception(f"Unexpected error in MCP request handler: {str(e)}")
            return self._create_error_response(None, -32603, "Internal error")
            
    async def _handle_initialize(self, request_id: Optional[str], params: Dict[str, Any]) -> JSONResponse:
        """Handle MCP initialize request
        
        Args:
            request_id: The JSON-RPC request ID
            params: Initialize parameters
            
        Returns:
            Initialize response
        """
        # Validate protocol version
        protocol_version = params.get("protocolVersion")
        if not protocol_version:
            return self._create_error_response(request_id, -32602, "Missing protocolVersion")
            
        # Return server capabilities
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "xaibo-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
        
        return JSONResponse(content=response)
        
    async def _handle_tools_list(self, request_id: Optional[str], params: Dict[str, Any]) -> JSONResponse:
        """Handle tools/list request - list all available agents as tools
        
        Args:
            request_id: The JSON-RPC request ID
            params: List parameters
            
        Returns:
            Tools list response
        """
        try:
            tools = []
            
            # Get all registered agents
            agent_ids = self.xaibo.list_agents()
            
            for agent_id in agent_ids:
                try:
                    config = self.xaibo.get_agent_config(agent_id)
                    
                    # Check for entry points in the agent configuration
                    entry_points = []
                    for exchange in config.exchange:
                        if exchange.module == '__entry__':
                            if isinstance(exchange.provider, list):
                                entry_points.extend(exchange.provider)
                            else:
                                entry_points.append('__entry__')
                    
                    # If no specific entry points found, use default
                    if not entry_points:
                        entry_points = ['__entry__']
                    
                    # Create tools for each entry point
                    for entry_point in entry_points:
                        if entry_point == '__entry__':
                            tool_name = agent_id
                        else:
                            tool_name = f"{agent_id}.{entry_point}"
                            
                        # Use AgentConfig.description if available, otherwise fall back to default
                        if config.description:
                            description = config.description
                            # Add entry point info if not the default entry point
                            if entry_point != '__entry__':
                                description += f" (entry point: {entry_point})"
                        else:
                            # Fallback to original description format
                            description = f"Execute Xaibo agent '{agent_id}'" + (
                                f" with entry point '{entry_point}'" if entry_point != '__entry__' else ""
                            )
                        
                        tool = {
                            "name": tool_name,
                            "description": description,
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {
                                        "type": "string",
                                        "description": "The text message to send to the agent"
                                    }
                                },
                                "required": ["message"]
                            }
                        }
                        tools.append(tool)
                        
                except Exception as e:
                    logger.warning(f"Error processing agent {agent_id}: {str(e)}")
                    continue
                    
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools
                }
            }
            
            return JSONResponse(content=response)
            
        except Exception as e:
            logger.exception(f"Error listing tools: {str(e)}")
            return self._create_error_response(request_id, -32603, "Internal error")
            
    async def _handle_tools_call(self, request_id: Optional[str], params: Dict[str, Any]) -> JSONResponse:
        """Handle tools/call request - execute an agent
        
        Args:
            request_id: The JSON-RPC request ID
            params: Tool call parameters
            
        Returns:
            Tool call response
        """
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return self._create_error_response(request_id, -32602, "Missing tool name")
                
            message = arguments.get("message")
            if not message:
                return self._create_error_response(request_id, -32602, "Missing message argument")
                
            # Parse agent ID and entry point from tool name
            if '.' in tool_name:
                agent_id, entry_point = tool_name.split('.', 1)
            else:
                agent_id = tool_name
                entry_point = '__entry__'
                
            try:
                # Get the agent
                agent = self.xaibo.get_agent(agent_id)
                
                # Execute the agent with the message
                response = await agent.handle_text(message, entry_point=entry_point)
                
                # Convert response to MCP content format
                content = []
                if response.text:
                    content.append({
                        "type": "text",
                        "text": response.text
                    })
                    
                # Handle file attachments if any
                if response.attachments:
                    for attachment in response.attachments:
                        # For now, we'll represent attachments as text descriptions
                        # In a full implementation, you might want to handle binary data differently
                        content.append({
                            "type": "text",
                            "text": f"[Attachment: {attachment.type.value}]"
                        })
                
                # If no content, provide empty text
                if not content:
                    content.append({
                        "type": "text",
                        "text": ""
                    })
                    
                mcp_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content,
                        "isError": False
                    }
                }
                
                return JSONResponse(content=mcp_response)
                
            except KeyError:
                return self._create_error_response(request_id, -32602, f"Agent '{agent_id}' not found")
            except AttributeError as e:
                return self._create_error_response(request_id, -32602, f"Agent does not support text handling: {str(e)}")
            except Exception as e:
                logger.exception(f"Error executing agent {agent_id}: {str(e)}")
                return self._create_error_response(request_id, -32603, f"Agent execution failed: {str(e)}")
                
        except Exception as e:
            logger.exception(f"Error in tools/call: {str(e)}")
            return self._create_error_response(request_id, -32603, "Internal error")
            
    def _create_error_response(self, request_id: Optional[str], code: int, message: str) -> JSONResponse:
        """Create a JSON-RPC 2.0 error response
        
        Args:
            request_id: The request ID (can be None for parse errors)
            code: Error code
            message: Error message
            
        Returns:
            JSON-RPC error response
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        
        return JSONResponse(content=response, status_code=200)  # MCP uses 200 for JSON-RPC errors