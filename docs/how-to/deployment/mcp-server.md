# How to deploy as an MCP server

This guide shows you how to deploy your Xaibo agents as an MCP (Model Context Protocol) server, making them available as tools for other MCP-compatible applications and development environments.

## Install web server dependencies

Install the required web server dependencies:

```bash
pip install xaibo[webserver]
```

This includes the MCP adapter and JSON-RPC 2.0 support.

## Deploy using the CLI

Use the built-in CLI for quick MCP deployment:

```bash
# Deploy as MCP server
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 127.0.0.1 \
  --port 8000
```

## Create an MCP server deployment

Create a deployment script for your MCP server:

```python
# mcp_deploy.py
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.mcp import McpApiAdapter

def main():
    # Initialize Xaibo
    xaibo = Xaibo()
    
    # Register your agents from the agents directory
    xaibo.register_agents_from_directory("./agents")
    
    # Create web server with MCP adapter
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[McpApiAdapter(xaibo)]
    )
    
    # Start the server
    server.run(host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
```


## Test your MCP server

Test the MCP server with curl:

```bash
# Initialize MCP connection
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'

# List available tools (your agents)
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Call an agent
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "your-agent-id",
      "arguments": {
        "message": "Hello from MCP client!"
      }
    }
  }'
```

## Use with MCP clients

Connect your MCP server to various MCP clients:

### Claude Desktop
Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "xaibo-agents": {
      "command": "python",
      "args": ["-m", "xaibo.server.web", "--agent-dir", "./agents", "--adapter", "xaibo.server.adapters.McpApiAdapter"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Cline (VS Code Extension)
Configure Cline to use your Xaibo MCP server:

```json
{
  "mcp": {
    "servers": [
      {
        "name": "xaibo-agents",
        "transport": {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "xaibo.server.web", "--agent-dir", "./agents", "--adapter", "xaibo.server.adapters.McpApiAdapter"]
        }
      }
    ]
  }
}
```

## Deploy as stdio MCP server

Create a stdio-based MCP server for direct process communication:

```python
# stdio_mcp_server.py
import sys
import json
import asyncio
from xaibo import Xaibo
from xaibo.server.adapters.mcp import McpApiAdapter

class StdioMCPServer:
    def __init__(self):
        self.xaibo = Xaibo()
        self.xaibo.register_agents_from_directory("./agents")
        self.adapter = McpApiAdapter(self.xaibo)
    
    async def handle_request(self, request_data):
        """Handle a single MCP request"""
        try:
            request = json.loads(request_data)
            response = await self.adapter.handle_mcp_request(request)
            return json.dumps(response)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if "request" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            return json.dumps(error_response)
    
    async def run(self):
        """Run the stdio MCP server"""
        while True:
            try:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                # Process request
                response = await self.handle_request(line.strip())
                
                # Write to stdout
                print(response, flush=True)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Server error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)

async def main():
    server = StdioMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

Use the stdio server:

```bash
# Run as stdio server
python stdio_mcp_server.py

# Or use with MCP client that expects stdio
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python stdio_mcp_server.py
```

## Best practices

### Agent design for MCP
- Keep agent responses concise and focused
- Design tools that work well as discrete operations
- Use clear, descriptive agent and tool names
- Implement proper error handling

### Security
- Validate all input parameters
- Implement rate limiting for production
- Use authentication for sensitive operations
- Monitor for unusual usage patterns

### Performance
- Optimize agent response times
- Cache frequently used data
- Use connection pooling for external services
- Monitor memory usage

### Reliability
- Implement proper error handling
- Add health checks and monitoring
- Use graceful shutdown procedures
- Log all operations for debugging

## Troubleshooting

### MCP protocol errors
- Verify JSON-RPC 2.0 format compliance
- Check method names and parameter structures
- Review MCP specification for requirements
- Test with simple MCP clients first

### Agent execution errors
- Check agent configurations and dependencies
- Verify tool implementations work correctly
- Review logs for detailed error messages
- Test agents independently before MCP integration

### Connection issues
- Verify server is listening on correct port
- Check firewall and network settings
- Test with curl before using MCP clients
- Review client configuration and compatibility

### Performance problems
- Monitor response times and resource usage
- Optimize agent configurations
- Check for memory leaks in long-running servers
- Use profiling tools to identify bottlenecks