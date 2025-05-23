# Tools and Integrations

This guide covers how to use, configure, and create tools in Xaibo, as well as integrate with external services and systems.

---

## Python Tool Provider

The Python Tool Provider allows you to convert Python functions into tools that agents can use.

### Basic Usage

#### Creating Tools with the @tool Decorator

```python title="tools/example.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
from datetime import datetime, timezone
import requests

@tool
def current_time():
    """Gets the current time in UTC"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def fetch_weather(city: str) -> str:
    """Fetch current weather for a city
    
    Args:
        city: The name of the city to get weather for
        
    Returns:
        Current weather description
    """
    # Mock implementation - replace with real API
    return f"Sunny, 22°C in {city}"

@tool
def calculate_sum(numbers: list[float]) -> float:
    """Calculate the sum of a list of numbers
    
    Args:
        numbers: List of numbers to sum
        
    Returns:
        The sum of all numbers
    """
    return sum(numbers)
```

#### Agent Configuration

```yaml title="agents/tool-user.yml"
id: tool-user
description: Agent that uses Python tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo

  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]  # Import tools from this package

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to various tools.
        Use them to provide accurate and helpful responses.
```

### Advanced Python Tools

#### Tools with Complex Types

```python title="tools/advanced.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str

@tool
def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search the web for information
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, url, and snippet
    """
    # Mock implementation
    results = []
    for i in range(min(max_results, 3)):
        results.append({
            "title": f"Result {i+1} for '{query}'",
            "url": f"https://example.com/result{i+1}",
            "snippet": f"This is a snippet for result {i+1} about {query}"
        })
    return results

@tool
def analyze_data(data: Dict[str, any], analysis_type: str = "summary") -> Dict[str, any]:
    """Analyze structured data
    
    Args:
        data: The data to analyze
        analysis_type: Type of analysis (summary, statistics, trends)
        
    Returns:
        Analysis results
    """
    if analysis_type == "summary":
        return {
            "total_keys": len(data),
            "data_types": {k: type(v).__name__ for k, v in data.items()},
            "sample_values": {k: v for k, v in list(data.items())[:3]}
        }
    elif analysis_type == "statistics":
        numeric_values = [v for v in data.values() if isinstance(v, (int, float))]
        return {
            "numeric_count": len(numeric_values),
            "sum": sum(numeric_values) if numeric_values else 0,
            "average": sum(numeric_values) / len(numeric_values) if numeric_values else 0
        }
    else:
        return {"error": f"Unknown analysis type: {analysis_type}"}
```

### Tool Configuration Options

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      # Import tools from specific packages
      tool_packages: 
        - tools.utilities
        - tools.file_operations
        - tools.external_apis
      
      # Alternatively, provide function objects directly
      tool_functions: []  # List of function objects
      
      # Auto-import packages (default: true)
      auto_import: true
      
      # Tool execution timeout (seconds)
      execution_timeout: 30.0
      
      # Enable/disable specific tools
      enabled_tools: ["current_time", "fetch_weather"]  # If specified, only these tools are available
      disabled_tools: ["dangerous_operation"]  # These tools will be excluded
```

---

## MCP Tool Provider

The MCP (Model Context Protocol) Tool Provider allows you to connect to external MCP servers and use their tools.

### Basic MCP Configuration

```yaml title="agents/mcp-agent.yml"
id: mcp-agent
description: Agent using MCP tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4

  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 30.0
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]
          env:
            LOG_LEVEL: INFO

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You have access to filesystem tools through MCP.
        Use them to help users with file operations.
```

### MCP Server Types

#### Stdio Servers (Local Processes)

```yaml
servers:
  - name: filesystem
    transport: stdio
    command: ["python", "-m", "mcp_server_filesystem"]
    args: ["--root", "/workspace", "--verbose"]
    env:
      LOG_LEVEL: DEBUG
      PYTHONPATH: /custom/path
      API_KEY: your-api-key

  - name: git_tools
    transport: stdio
    command: ["node", "mcp-server-git/dist/index.js"]
    args: ["--repository", "/path/to/repo"]
    env:
      NODE_ENV: production
```

#### SSE Servers (HTTP-based)

```yaml
servers:
  - name: web_search
    transport: sse
    url: https://api.example.com/mcp
    headers:
      Authorization: Bearer your-api-key
      Content-Type: application/json
      User-Agent: Xaibo/1.0
      X-Client-ID: xaibo-client

  - name: database_tools
    transport: sse
    url: https://db-api.company.com/mcp
    headers:
      X-API-Key: your-database-key
      X-Database: production
```

#### WebSocket Servers

```yaml
servers:
  - name: realtime_data
    transport: websocket
    url: ws://localhost:8080/mcp
    headers:
      X-API-Key: your-websocket-key
      X-Client-ID: xaibo-client
      Authorization: Bearer your-token

  - name: chat_integration
    transport: websocket
    url: wss://chat.example.com/mcp
    headers:
      X-Room-ID: general
      X-User-ID: xaibo-bot
```

### MCP Tool Usage

When MCP tools are configured, they become available to the agent with namespaced names:

```python
# Tools are namespaced by server name
# filesystem.read_file
# filesystem.write_file
# web_search.search
# database_tools.query
```

Example interaction:
```
User: "Read the contents of README.md"
Agent: I'll read the README.md file for you.
[Calls filesystem.read_file with path="README.md"]
Agent: Here are the contents of README.md: [file contents]
```

### Advanced MCP Configuration

#### Multiple Server Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 60.0
      connection_retry_attempts: 3
      connection_retry_delay: 5.0
      servers:
        # Development tools
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]
          
        - name: git
          transport: stdio
          command: ["node", "mcp-server-git/dist/index.js"]
          args: ["--repository", "."]
          
        # External APIs
        - name: weather
          transport: sse
          url: https://weather-api.example.com/mcp
          headers:
            Authorization: Bearer ${WEATHER_API_KEY}
            
        - name: database
          transport: websocket
          url: wss://db.example.com/mcp
          headers:
            X-API-Key: ${DATABASE_API_KEY}
            X-Database: ${DATABASE_NAME}
---

## Creating Custom Tools

### Custom Python Tool Provider

```python title="custom/tools/my_tool_provider.py"
from xaibo.core.protocols.tools import ToolsProtocol
from xaibo.core.models.tools import Tool, ToolResult
from typing import List
import asyncio

class CustomToolProvider(ToolsProtocol):
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url
        
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="custom_search",
                description="Search using custom API",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="custom_analyze",
                description="Analyze data using custom service",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Data to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["sentiment", "keywords", "summary"],
                            "description": "Type of analysis"
                        }
                    },
                    "required": ["data", "analysis_type"]
                }
            )
        ]
    
    async def call_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        if tool_name == "custom_search":
            return await self._search(arguments["query"], arguments.get("limit", 10))
        elif tool_name == "custom_analyze":
            return await self._analyze(arguments["data"], arguments["analysis_type"])
        else:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}"
            )
    
    async def _search(self, query: str, limit: int) -> ToolResult:
        # Implement your custom search logic
        try:
            # Mock implementation
            results = [
                {"title": f"Result {i}", "url": f"https://example.com/{i}"}
                for i in range(min(limit, 5))
            ]
            return ToolResult(
                success=True,
                content=f"Found {len(results)} results for '{query}'",
                data={"results": results}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
    
    async def _analyze(self, data: str, analysis_type: str) -> ToolResult:
        # Implement your custom analysis logic
        try:
            if analysis_type == "sentiment":
                # Mock sentiment analysis
                sentiment = "positive"  # Replace with real analysis
                confidence = 0.85
                
                return ToolResult(
                    success=True,
                    content=f"Sentiment: {sentiment} (confidence: {confidence:.2f})",
                    data={"sentiment": sentiment, "confidence": confidence}
                )
            elif analysis_type == "keywords":
                # Mock keyword extraction
                keywords = ["example", "keyword", "analysis"]  # Replace with real extraction
                
                return ToolResult(
                    success=True,
                    content=f"Keywords: {', '.join(keywords)}",
                    data={"keywords": keywords}
                )
            elif analysis_type == "summary":
                # Mock summarization
                summary = f"Summary of the provided data: {data[:100]}..."
                
                return ToolResult(
                    success=True,
                    content=summary,
                    data={"summary": summary}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown analysis type: {analysis_type}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Analysis failed: {str(e)}"
            )
```

#### Using Custom Tool Provider

```yaml title="agents/custom-tools-agent.yml"
id: custom-tools-agent
description: Agent using custom tool provider
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4

  - module: custom.tools.my_tool_provider.CustomToolProvider
    id: custom-tools
    config:
      api_key: your-api-key
      base_url: https://api.example.com

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You have access to custom search and analysis tools.
        Use them to help users with information gathering and analysis.
```

---

## Integration with External Services

### Database Integration

```python title="tools/database.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
import sqlite3
import json
from typing import List, Dict, Any

@tool
def query_database(query: str, database_path: str = "data.db") -> Dict[str, Any]:
    """Execute a SQL query on the database
    
    Args:
        query: SQL query to execute
        database_path: Path to the SQLite database
        
    Returns:
        Query results
    """
    try:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return {
                "success": True,
                "row_count": len(results),
                "data": results
            }
        else:
            conn.commit()
            return {
                "success": True,
                "rows_affected": cursor.rowcount,
                "message": "Query executed successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()

@tool
def insert_record(table: str, data: Dict[str, Any], database_path: str = "data.db") -> Dict[str, Any]:
    """Insert a record into the database
    
    Args:
        table: Table name
        data: Dictionary of column names and values
        database_path: Path to the SQLite database
        
    Returns:
        Insert result
    """
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in values])
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()
        
        return {
            "success": True,
            "inserted_id": cursor.lastrowid,
            "message": f"Record inserted into {table}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()
```

### API Integration

```python title="tools/api_integration.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
import requests
import json
from typing import Dict, Any, Optional

@tool
def make_api_request(url: str, method: str = "GET", 
                    headers: Optional[Dict[str, str]] = None,
                    data: Optional[Dict[str, Any]] = None,
                    timeout: int = 30) -> Dict[str, Any]:
    """Make an HTTP API request
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Optional HTTP headers
        data: Optional request body data
        timeout: Request timeout in seconds
        
    Returns:
        API response data
    """
    try:
        headers = headers or {}
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return {
                "success": False,
                "error": f"Unsupported HTTP method: {method}"
            }
        
        return {
            "success": True,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

@tool
def slack_send_message(channel: str, message: str, webhook_url: str) -> Dict[str, Any]:
    """Send a message to Slack
    
    Args:
        channel: Slack channel name or ID
        message: Message to send
        webhook_url: Slack webhook URL
        
    Returns:
        Send result
    """
    try:
        payload = {
            "channel": channel,
            "text": message,
            "username": "Xaibo Bot"
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Message sent successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Slack API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send message: {str(e)}"
        }
```

---

## Tool Development Best Practices

### Error Handling

```python title="tools/best_practices.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

@tool
def robust_tool_example(input_data: str, timeout: int = 30) -> Dict[str, Any]:
    """Example of a robust tool with proper error handling
    
    Args:
        input_data: Data to process
        timeout: Operation timeout in seconds
        
    Returns:
        Processing result with detailed error information
    """
    try:
        # Validate inputs
        if not input_data or not isinstance(input_data, str):
            return {
                "success": False,
                "error": "Invalid input: input_data must be a non-empty string",
                "error_type": "ValidationError"
            }
        
        if timeout <= 0:
            return {
                "success": False,
                "error": "Invalid timeout: must be positive",
                "error_type": "ValidationError"
            }
        
        # Log the operation
        logger.info(f"Processing data of length {len(input_data)} with timeout {timeout}")
        
        # Simulate processing
        result = input_data.upper()  # Simple transformation
        
        # Log success
        logger.info("Processing completed successfully")
        
        return {
            "success": True,
            "result": result,
            "metadata": {
                "input_length": len(input_data),
                "output_length": len(result),
                "processing_time": 0.1  # Mock processing time
            }
        }
        
    except ValueError as e:
        logger.error(f"Value error in robust_tool_example: {e}")
        return {
            "success": False,
            "error": f"Value error: {str(e)}",
            "error_type": "ValueError"
        }
    except TimeoutError as e:
        logger.error(f"Timeout in robust_tool_example: {e}")
        return {
            "success": False,
            "error": f"Operation timed out: {str(e)}",
            "error_type": "TimeoutError"
        }
    except Exception as e:
        logger.error(f"Unexpected error in robust_tool_example: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        }
```

### Input Validation and Security

```python title="tools/validation.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
from typing import Dict, Any, List
import re
import os

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def sanitize_file_path(file_path: str, allowed_dirs: List[str] = None) -> str:
    """Sanitize file path to prevent directory traversal"""
    # Normalize the path
    normalized = os.path.normpath(file_path)
    
    # Check for directory traversal attempts
    if '..' in normalized or normalized.startswith('/'):
        raise ValueError("Invalid file path: directory traversal detected")
    
    # Check against allowed directories
    if allowed_dirs:
        if not any(normalized.startswith(allowed_dir) for allowed_dir in allowed_dirs):
            raise ValueError(f"File path not in allowed directories: {allowed_dirs}")
    
    return normalized

@tool
def secure_file_operation(file_path: str, operation: str = "read") -> Dict[str, Any]:
    """Secure file operation with path validation
    
    Args:
        file_path: Path to the file
        operation: Operation to perform (read, write, delete)
        
    Returns:
        Operation result
    """
    try:
        # Define allowed directories
        allowed_dirs = ["./workspace", "./data", "./temp"]
        
        # Sanitize the file path
        safe_path = sanitize_file_path(file_path, allowed_dirs)
        
        if operation == "read":
            if not os.path.exists(safe_path):
                return {
                    "success": False,
                    "error": f"File not found: {safe_path}"
                }
            
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "file_size": len(content)
            }
        
        elif operation == "delete":
            if os.path.exists(safe_path):
                os.remove(safe_path)
                return {
                    "success": True,
                    "message": f"File deleted: {safe_path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"File not found: {safe_path}"
                }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported operation: {operation}"
            }
            
    except ValueError as e:
        return {
            "success": False,
            "error": f"Validation error: {str(e)}",
            "error_type": "ValidationError"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Operation failed: {str(e)}",
            "error_type": type(e).__name__
        }
```

### Performance Optimization

```python title="tools/performance.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool
from typing import Dict, Any, List
import time
import asyncio
from functools import lru_cache
import hashlib

# Cache for expensive operations
@lru_cache(maxsize=128)
def expensive_computation(input_data: str) -> str:
    """Cached expensive computation"""
    # Simulate expensive operation
    time.sleep(0.1)
    return f"Processed: {input_data.upper()}"

@tool
def cached_operation(input_data: str) -> Dict[str, Any]:
    """Tool that uses caching for performance
    
    Args:
        input_data: Data to process
        
    Returns:
        Processing result with timing information
    """
    start_time = time.time()
    
    try:
        # Use cached computation
        result = expensive_computation(input_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        return {
            "success": True,
            "result": result,
            "processing_time": processing_time,
            "cached": True  # Subsequent calls will be faster
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@tool
async def parallel_processing(data_list: List[str]) -> Dict[str, Any]:
    """Process multiple items in parallel
    
    Args:
        data_list: List of data items to process
        
    Returns:
        Processing results
    """
    async def process_item(item: str) -> Dict[str, Any]:
        # Simulate async processing
        await asyncio.sleep(0.1)
        return {
            "input": item,
            "output": item.upper(),
            "length": len(item)
        }
    
    try:
        start_time = time.time()
        
        # Process items in parallel
        tasks = [process_item(item) for item in data_list]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        return {
            "success": True,
            "results": results,
            "total_items": len(data_list),
            "processing_time": end_time - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

!!! tip "Tool Development Best Practices"
    - **Error Handling**: Always wrap tool logic in try-catch blocks and return structured error information
    - **Input Validation**: Validate all inputs before processing to prevent security issues
    - **Logging**: Use proper logging for debugging and monitoring tool usage
    - **Documentation**: Provide clear docstrings with parameter descriptions and return value formats
    - **Security**: Sanitize file paths and validate URLs to prevent security vulnerabilities
    - **Performance**: Use caching and async processing for expensive operations
    - **Testing**: Write unit tests for your tools to ensure reliability

!!! warning "Security Considerations"
    - Never execute arbitrary code from user input
    - Validate and sanitize all file paths to prevent directory traversal
    - Use timeouts to prevent infinite loops or long-running operations
    - Limit resource usage (memory, disk space, network requests)
    - Validate URLs and API endpoints before making requests
    - Use environment variables for sensitive configuration like API keys

!!! note "Integration Guidelines"
    - Use consistent error response formats across all tools
    - Implement proper retry logic for external API calls
    - Consider rate limiting for external service integrations
    - Use connection pooling for database operations
    - Implement circuit breakers for unreliable external services
    - Monitor tool usage and performance metrics