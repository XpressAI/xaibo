#!/usr/bin/env python3
"""
Simple MCP server implementation for stdio transport testing.
This server implements the basic MCP protocol for testing purposes.
"""

import asyncio
import json
import sys
import uuid
from typing import Dict, Any, List


class StdioMCPServer:
    """Simple MCP server that communicates via stdio"""
    
    def __init__(self):
        self.tools = [
            {
                "name": "test_tool",
                "description": "A test tool for stdio server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "First parameter"
                        }
                    },
                    "required": ["param1"]
                }
            },
            {
                "name": "echo_tool",
                "description": "Echoes back the input",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo"
                        }
                    },
                    "required": ["message"]
                }
            }
        ]
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
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
                        "name": "test-stdio-server",
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
            
            if tool_name == "test_tool":
                param1 = arguments.get("param1", "")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Test tool executed with param1: {param1}"
                            }
                        ]
                    }
                }
            elif tool_name == "echo_tool":
                message = arguments.get("message", "")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Echo: {message}"
                            }
                        ]
                    }
                }
            elif tool_name == "error_tool":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -1,
                        "message": "Tool execution failed"
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
    
    async def run(self):
        """Run the server, reading from stdin and writing to stdout"""
        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    continue
                    
                # Handle request
                response = await self.handle_request(request)
                
                # Send response (if not a notification)
                if response is not None:
                    response_line = json.dumps(response) + "\n"
                    sys.stdout.write(response_line)
                    sys.stdout.flush()
                    
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
                response_line = json.dumps(error_response) + "\n"
                sys.stdout.write(response_line)
                sys.stdout.flush()


async def main():
    """Main entry point"""
    server = StdioMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())