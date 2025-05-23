#!/usr/bin/env python3
"""
Simple MCP server implementation for SSE transport testing.
This server implements the basic MCP protocol over HTTP/SSE for testing purposes.
"""

import asyncio
import json
import argparse
from aiohttp import web, web_request
from typing import Dict, Any, Optional


class SSEMCPServer:
    """Simple MCP server that communicates via SSE (HTTP POST)"""
    
    def __init__(self):
        self.tools = [
            {
                "name": "sse_tool",
                "description": "A test tool for SSE server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input parameter"
                        }
                    },
                    "required": ["input"]
                }
            },
            {
                "name": "no_content_tool",
                "description": "Tool that returns no content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Status parameter",
                            "default": "success"
                        }
                    }
                }
            }
        ]
        
    async def handle_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming JSON-RPC request"""
        method = request_data.get("method")
        request_id = request_data.get("id")
        params = request_data.get("params", {})
        
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
                        "name": "test-sse-server",
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
            
            if tool_name == "sse_tool":
                input_param = arguments.get("input", "")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"SSE tool executed with input: {input_param}"
                            }
                        ]
                    }
                }
            elif tool_name == "no_content_tool":
                status = arguments.get("status", "success")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "status": status
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
    
    async def handle_http_request(self, request: web_request.Request) -> web.Response:
        """Handle HTTP POST request"""
        try:
            # Parse JSON request body
            request_data = await request.json()
            
            # Handle request
            response_data = await self.handle_request(request_data)
            
            # Return response (or empty response for notifications)
            if response_data is not None:
                return web.json_response(response_data)
            else:
                return web.Response(status=204)  # No content for notifications
                
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
            return web.json_response(error_response, status=400)
            
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
            return web.json_response(error_response, status=500)
    
    def create_app(self) -> web.Application:
        """Create the aiohttp application"""
        app = web.Application()
        app.router.add_post("/mcp", self.handle_http_request)
        app.router.add_post("/", self.handle_http_request)  # Default route
        return app
    
    async def start_server(self, host: str = "localhost", port: int = 8080):
        """Start the HTTP server"""
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        print(f"Starting SSE MCP server on http://{host}:{port}")
        return runner


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SSE MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    args = parser.parse_args()
    
    server = SSEMCPServer()
    runner = await server.start_server(args.host, args.port)
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())