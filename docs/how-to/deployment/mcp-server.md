# How to deploy as an MCP server

This guide shows you how to deploy your Xaibo agents as an MCP (Model Context Protocol) server, making them available as tools for other MCP-compatible applications and development environments.

## Install web server dependencies

1. Install the required web server dependencies:

```bash
pip install xaibo[webserver]
```

This includes the MCP adapter and JSON-RPC 2.0 support.

## Create an MCP server deployment

2. Create a deployment script for your MCP server:

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

## Deploy using the CLI

3. Use the built-in CLI for quick MCP deployment:

```bash
# Deploy as MCP server
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 127.0.0.1 \
  --port 8000
```

## Test your MCP server

4. Test the MCP server with curl:

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

## Configure agents for MCP

5. Create agents optimized for MCP tool usage:

```yaml
# agents/mcp_tool_agent.yml
id: file-manager
description: A file management agent for MCP clients
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.file_tools]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 5
      system_prompt: |
        You are a file management assistant exposed as an MCP tool.
        Help users with file operations like reading, writing, and organizing files.
        Be concise and focused in your responses.
```

Create specialized tools for MCP usage:

```python
# tools/file_tools.py
import os
import json
from pathlib import Path
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file
    
    Args:
        file_path: Path to the file to read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    """
    try:
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def list_directory(directory_path: str = ".") -> str:
    """List contents of a directory
    
    Args:
        directory_path: Path to the directory to list
    """
    try:
        items = []
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            item_type = "directory" if os.path.isdir(item_path) else "file"
            items.append(f"{item} ({item_type})")
        
        return "\n".join(items) if items else "Directory is empty"
    except Exception as e:
        return f"Error listing directory: {str(e)}"
```

## Deploy with both OpenAI and MCP adapters

6. Create a server that supports both OpenAI and MCP protocols:

```python
# dual_deploy.py
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter
from xaibo.server.adapters.mcp import McpApiAdapter

def main():
    xaibo = Xaibo()
    xaibo.register_agents_from_directory("./agents")
    
    # Create server with both adapters
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[
            OpenAiApiAdapter(xaibo),  # Available at /openai/*
            McpApiAdapter(xaibo)      # Available at /mcp
        ]
    )
    
    server.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

Test both endpoints:

```bash
# Test OpenAI endpoint
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "file-manager",
    "messages": [{"role": "user", "content": "List files in current directory"}]
  }'

# Test MCP endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "file-manager",
      "arguments": {"message": "List files in current directory"}
    }
  }'
```

## Use with MCP clients

7. Connect your MCP server to various MCP clients:

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

### Custom MCP client
```python
# mcp_client.py
import asyncio
import aiohttp
import json

class XaiboMCPClient:
    def __init__(self, base_url="http://localhost:8000/mcp"):
        self.base_url = base_url
        self.session = None
        self.request_id = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _send_request(self, method, params=None):
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        async with self.session.post(
            self.base_url,
            json=request,
            headers={"Content-Type": "application/json"}
        ) as response:
            return await response.json()
    
    async def initialize(self):
        return await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "xaibo-client", "version": "1.0.0"}
        })
    
    async def list_tools(self):
        return await self._send_request("tools/list")
    
    async def call_tool(self, name, arguments):
        return await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

async def main():
    async with XaiboMCPClient() as client:
        # Initialize connection
        init_response = await client.initialize()
        print("Initialized:", init_response)
        
        # List available tools
        tools_response = await client.list_tools()
        print("Available tools:", tools_response)
        
        # Call a tool
        if tools_response.get("result", {}).get("tools"):
            tool_name = tools_response["result"]["tools"][0]["name"]
            call_response = await client.call_tool(tool_name, {
                "message": "Hello from Python client!"
            })
            print("Tool response:", call_response)

if __name__ == "__main__":
    asyncio.run(main())
```

## Deploy as stdio MCP server

8. Create a stdio-based MCP server for direct process communication:

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

## Configure for production deployment

9. Set up production-ready MCP server:

```python
# production_mcp_deploy.py
import logging
import os
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.mcp import McpApiAdapter
from fastapi.middleware.cors import CORSMiddleware

def create_production_app():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    xaibo = Xaibo()
    xaibo.register_agents_from_directory("./agents")
    
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[McpApiAdapter(xaibo)]
    )
    
    # Add CORS for web clients
    server.app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["POST"],
        allow_headers=["*"],
    )
    
    # Add health check
    @server.app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "protocol": "MCP",
            "agents": list(xaibo.agents.keys())
        }
    
    return server.app

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    uvicorn.run(
        create_production_app(),
        host=host,
        port=port,
        log_level="info"
    )
```

## Deploy with Docker

10. Create a Docker deployment for your MCP server:

```dockerfile
# Dockerfile.mcp
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose MCP port
EXPOSE 8000

# Run MCP server
CMD ["python", "production_mcp_deploy.py"]
```

```yaml
# docker-compose.mcp.yml
version: '3.8'

services:
  xaibo-mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8000:8000"
    environment:
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ALLOWED_ORIGINS=*
    volumes:
      - ./agents:/app/agents
      - ./tools:/app/tools
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Start the MCP server:

```bash
docker-compose -f docker-compose.mcp.yml up -d
```

## Monitor MCP server

11. Add monitoring and debugging for your MCP server:

```python
# mcp_monitor.py
import json
import time
import logging
from collections import defaultdict
from xaibo.server.adapters.mcp import McpApiAdapter

class MonitoredMCPAdapter(McpApiAdapter):
    def __init__(self, xaibo):
        super().__init__(xaibo)
        self.request_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    async def handle_mcp_request(self, request):
        method = request.get("method", "unknown")
        start_time = time.time()
        
        try:
            response = await super().handle_mcp_request(request)
            
            # Log successful request
            duration = time.time() - start_time
            self.request_count[method] += 1
            self.response_times[method].append(duration)
            
            self.logger.info(f"MCP {method} completed in {duration:.3f}s")
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            self.logger.error(f"MCP {method} failed after {duration:.3f}s: {str(e)}")
            raise
    
    def get_stats(self):
        """Get server statistics"""
        stats = {
            "total_requests": sum(self.request_count.values()),
            "methods": {}
        }
        
        for method, count in self.request_count.items():
            times = self.response_times[method]
            stats["methods"][method] = {
                "count": count,
                "avg_response_time": sum(times) / len(times) if times else 0,
                "max_response_time": max(times) if times else 0
            }
        
        return stats

# Use monitored adapter
def create_monitored_mcp_server():
    xaibo = Xaibo()
    xaibo.register_agents_from_directory("./agents")
    
    adapter = MonitoredMCPAdapter(xaibo)
    
    server = XaiboWebServer(xaibo=xaibo, adapters=[adapter])
    
    # Add stats endpoint
    @server.app.get("/mcp/stats")
    async def get_mcp_stats():
        return adapter.get_stats()
    
    return server
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