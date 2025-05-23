#!/usr/bin/env python3
"""
Simple MCP server implementation for WebSocket transport testing.
This server implements the basic MCP protocol over WebSocket for testing purposes.
"""

import asyncio
import json
import websockets
import argparse
from typing import Dict, Any, Optional


class WebSocketMCPServer:
    """Simple MCP server that communicates via WebSocket"""
    
    def __init__(self):
        self.tools = [
            {
                "name": "ws_tool",
                "description": "A test tool for WebSocket server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Data parameter"
                        }
                    },
                    "required": ["data"]
                }
            },
            {
                "name": "multi_content_tool",
                "description": "Tool that returns multiple content items",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of content items to return",
                            "default": 2
                        }
                    }
                }
            }
        ]
        
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "test-websocket-server",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": self.tools
                }
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "ws_tool":
                data = arguments.get("data", "")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"WebSocket tool executed with data: {data}"
                            }
                        ]
                    }
                }
            elif tool_name == "multi_content_tool":
                count = arguments.get("count", 2)
                content_items = []
                for i in range(count):
                    content_items.append({
                        "type": "text",
                        "text": f"Content item {i + 1}"
                    })
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content_items
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
                
        elif method == "notifications/initialized":
            # No response for notifications
            return None
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def handle_client(self, websocket):
        """Handle a WebSocket client connection"""
        try:
            async for message in websocket:
                try:
                    # Parse JSON-RPC request
                    request = json.loads(message)
                    
                    # Handle request
                    response = await self.handle_request(request)
                    
                    # Send response (if not a notification)
                    if response is not None:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    # Send error response for invalid JSON
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    await websocket.send(json.dumps(error_response))
                    
                except Exception as e:
                    # Send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    await websocket.send(json.dumps(error_response))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server"""
        print(f"Starting WebSocket MCP server on {host}:{port}")
        return await websockets.serve(self.handle_client, host, port)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="WebSocket MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    args = parser.parse_args()
    
    server = WebSocketMCPServer()
    websocket_server = await server.start_server(args.host, args.port)
    
    try:
        await websocket_server.wait_closed()
    except KeyboardInterrupt:
        print("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())