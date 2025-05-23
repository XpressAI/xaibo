# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues when working with Xaibo.

---

## Common Issues and Solutions

### Installation Issues

#### Problem: `pip install xaibo` fails with dependency conflicts

**Symptoms:**
```bash
ERROR: pip's dependency resolver does not currently consider all the packages that are installed
ERROR: Cannot install xaibo because these package versions have conflicts
```

**Solutions:**

1. **Use a virtual environment:**
   ```bash
   python -m venv xaibo-env
   source xaibo-env/bin/activate  # On Windows: xaibo-env\Scripts\activate
   pip install xaibo
   ```

2. **Update pip and setuptools:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install xaibo
   ```

3. **Install with specific dependency groups:**
   ```bash
   # Install only what you need
   pip install xaibo[openai,webserver]
   ```

#### Problem: `uvx xaibo init` command not found

**Symptoms:**
```bash
uvx: command not found
# or
xaibo: command not found
```

**Solutions:**

1. **Install uv first:**
   ```bash
   pip install uv
   uvx xaibo init my_project
   ```

2. **Alternative installation:**
   ```bash
   pip install xaibo
   python -m xaibo init my_project
   ```

3. **Check PATH environment variable:**
   ```bash
   # Ensure Python scripts directory is in PATH
   echo $PATH
   # Add to ~/.bashrc or ~/.zshrc if needed
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Configuration Issues

#### Problem: Agent configuration file not found

**Symptoms:**
```
FileNotFoundError: Agent configuration file 'agents/example.yml' not found
```

**Solutions:**

1. **Check file path and working directory:**
   ```bash
   ls -la agents/
   pwd  # Verify you're in the correct directory
   ```

2. **Use absolute paths:**
   ```yaml
   # In your configuration
   id: example
   # Use full path if relative path doesn't work
   ```

3. **Set XAIBO_CONFIG_DIR environment variable:**
   ```bash
   export XAIBO_CONFIG_DIR=/full/path/to/agents
   ```

#### Problem: Module import errors in agent configuration

**Symptoms:**
```
ModuleNotFoundError: No module named 'xaibo.primitives.modules.llm.OpenAILLM'
```

**Solutions:**

1. **Check module path spelling:**
   ```yaml
   # Correct path
   modules:
     - module: xaibo.primitives.modules.llm.OpenAILLM
       id: llm
   ```

2. **Install required dependencies:**
   ```bash
   pip install xaibo[openai]  # For OpenAI modules
   pip install xaibo[anthropic]  # For Anthropic modules
   ```

3. **Verify Python path:**
   ```python
   import sys
   print(sys.path)
   # Ensure xaibo is in the path
   ```

#### Problem: Exchange configuration errors

**Symptoms:**
```
ExchangeConfigurationError: No provider found for protocol 'LLMProtocol' required by module 'orchestrator'
```

**Solutions:**

1. **Add explicit exchange configuration:**
   ```yaml
   exchange:
     - module: orchestrator
       protocol: LLMProtocol
       provider: llm
   ```

2. **Check module IDs match:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.llm.OpenAILLM
       id: llm  # This ID must match in exchange
   ```

3. **Verify protocol implementations:**
   ```python
   # Check if module implements required protocol
   from xaibo.primitives.modules.llm.openai import OpenAILLM
   from xaibo.core.protocols.llm import LLMProtocol
   print(issubclass(OpenAILLM, LLMProtocol))  # Should be True
   ```

### API and Authentication Issues

#### Problem: OpenAI API key not working

**Symptoms:**
```
AuthenticationError: Incorrect API key provided
```

**Solutions:**

1. **Check API key format:**
   ```bash
   # OpenAI keys start with 'sk-'
   echo $OPENAI_API_KEY
   # Should look like: sk-...
   ```

2. **Set environment variable correctly:**
   ```bash
   export OPENAI_API_KEY="sk-your-actual-key-here"
   # Or in .env file
   echo "OPENAI_API_KEY=sk-your-actual-key-here" >> .env
   ```

3. **Verify API key in configuration:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.llm.OpenAILLM
       id: llm
       config:
         model: gpt-3.5-turbo
         api_key: "${OPENAI_API_KEY}"  # Use environment variable
   ```

4. **Test API key directly:**
   ```python
   import openai
   client = openai.OpenAI(api_key="your-key-here")
   try:
       response = client.models.list()
       print("API key is valid")
   except Exception as e:
       print(f"API key error: {e}")
   ```

#### Problem: Rate limiting errors

**Symptoms:**
```
RateLimitError: Rate limit reached for requests
```

**Solutions:**

1. **Implement retry logic:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.llm.OpenAILLM
       id: llm
       config:
         model: gpt-3.5-turbo
         timeout: 120.0  # Increase timeout
         max_retries: 3  # Add retry attempts
   ```

2. **Use different models or tiers:**
   ```yaml
   config:
     model: gpt-3.5-turbo  # Lower rate limits than gpt-4
   ```

3. **Add delays between requests:**
   ```python
   import time
   import asyncio
   
   # In custom tools
   await asyncio.sleep(1)  # Add delay
   ```

### Server and Network Issues

#### Problem: Development server won't start

**Symptoms:**
```
OSError: [Errno 48] Address already in use
```

**Solutions:**

1. **Check for running processes:**
   ```bash
   lsof -i :9001  # Check what's using port 9001
   kill -9 <PID>  # Kill the process if needed
   ```

2. **Use a different port:**
   ```bash
   uv run xaibo dev --port 9002
   # Or set environment variable
   export XAIBO_PORT=9002
   ```

3. **Check firewall settings:**
   ```bash
   # On macOS
   sudo pfctl -d  # Disable firewall temporarily
   
   # On Linux
   sudo ufw status
   sudo ufw allow 9001
   ```

#### Problem: CORS errors in browser

**Symptoms:**
```
Access to fetch at 'http://localhost:9001' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**

1. **Configure CORS origins:**
   ```bash
   export XAIBO_CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
   ```

2. **Use wildcard for development:**
   ```bash
   export XAIBO_CORS_ORIGINS="*"
   ```

3. **Programmatic CORS configuration:**
   ```python
   from xaibo.server import XaiboWebServer
   
   server = XaiboWebServer(
       xaibo=xaibo,
       cors_origins=["http://localhost:3000"]
   )
   ```

### Tool and Integration Issues

#### Problem: Python tools not being discovered

**Symptoms:**
```
No tools found in package 'tools.example'
```

**Solutions:**

1. **Check package structure:**
   ```
   tools/
   ├── __init__.py  # Must exist
   └── example.py   # Contains @tool decorated functions
   ```

2. **Verify tool decorator usage:**
   ```python
   from xaibo.primitives.modules.tools.python_tool_provider import tool
   
   @tool  # Must use this decorator
   def my_function():
       """Must have docstring"""
       return "result"
   ```

3. **Check Python path:**
   ```python
   import sys
   sys.path.append('.')  # Add current directory
   ```

4. **Debug tool discovery:**
   ```python
   from xaibo.primitives.modules.tools.python_tool_provider import PythonToolProvider
   
   provider = PythonToolProvider(tool_packages=['tools.example'])
   tools = provider.get_tools()
   print(f"Found {len(tools)} tools: {[t.name for t in tools]}")
   ```

#### Problem: MCP server connection failures

**Symptoms:**
```
MCPConnectionError: Failed to connect to MCP server 'filesystem'
```

**Solutions:**

1. **Check server command and path:**
   ```yaml
   servers:
     - name: filesystem
       transport: stdio
       command: ["python", "-m", "mcp_server_filesystem"]  # Verify this exists
       args: ["--root", "/workspace"]
   ```

2. **Test server manually:**
   ```bash
   python -m mcp_server_filesystem --root /workspace
   # Should start without errors
   ```

3. **Check environment variables:**
   ```yaml
   servers:
     - name: filesystem
       transport: stdio
       command: ["python", "-m", "mcp_server_filesystem"]
       env:
         PYTHONPATH: "/path/to/mcp/servers"
         LOG_LEVEL: "DEBUG"
   ```

4. **Verify network connectivity for remote servers:**
   ```bash
   curl -I https://api.example.com/mcp  # Test SSE endpoint
   telnet localhost 8080  # Test WebSocket endpoint
   ```

### Memory and Performance Issues

#### Problem: High memory usage with vector memory

**Symptoms:**
- Slow performance
- Out of memory errors
- Large memory files

**Solutions:**

1. **Optimize chunk size:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.memory.TokenChunker
       id: chunker
       config:
         window_size: 256  # Reduce from default 512
         window_overlap: 25  # Reduce overlap
   ```

2. **Limit memory size:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.memory.VectorMemory
       id: memory
       config:
         max_memories: 1000  # Limit total memories
         memory_file_path: ./memories.pkl
   ```

3. **Use more efficient embeddings:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
       id: embedder
       config:
         model_name: all-MiniLM-L6-v2  # Smaller, faster model
   ```

4. **Monitor memory usage:**
   ```python
   import psutil
   import os
   
   process = psutil.Process(os.getpid())
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
   ```

#### Problem: Slow LLM responses

**Symptoms:**
- Long wait times for responses
- Timeout errors

**Solutions:**

1. **Optimize model selection:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.llm.OpenAILLM
       id: llm
       config:
         model: gpt-3.5-turbo  # Faster than gpt-4
         max_tokens: 500  # Limit response length
   ```

2. **Adjust timeout settings:**
   ```yaml
   config:
     timeout: 120.0  # Increase timeout
     temperature: 0.3  # Lower temperature for faster responses
   ```

3. **Use streaming for long responses:**
   ```python
   # In custom implementations
   async for chunk in llm.stream_generate(messages):
       yield chunk
   ```

---

## Debugging Techniques

### Enable Debug Logging

```bash
# Set log level
export XAIBO_LOG_LEVEL=DEBUG

# Enable debug mode
export XAIBO_DEBUG=true

# Enable call tracing
export XAIBO_TRACE_CALLS=true
```

```python
# In Python code
import logging
logging.basicConfig(level=logging.DEBUG)

# Xaibo-specific logging
logger = logging.getLogger('xaibo')
logger.setLevel(logging.DEBUG)
```

### Use Debug Event Listener

```yaml
modules:
  - module: xaibo.primitives.event_listeners.DebugEventListener
    id: debug-listener
```

This will capture all module interactions and provide detailed debugging information.

### Inspect Agent State

```python
from xaibo import Xaibo
from xaibo.core.config import AgentConfig

# Load and inspect agent
xaibo = Xaibo()
agent_config = AgentConfig.from_file("agents/example.yml")
agent = xaibo.register_agent(agent_config)

# Inspect modules
print("Registered modules:")
for module_id, module in agent.modules.items():
    print(f"  {module_id}: {type(module).__name__}")

# Inspect exchanges
print("Exchange configuration:")
for exchange in agent.exchanges:
    print(f"  {exchange.module} -> {exchange.protocol} -> {exchange.provider}")
```

### Test Individual Components

```python
# Test LLM module
from xaibo.primitives.modules.llm.openai import OpenAILLM

llm = OpenAILLM(model="gpt-3.5-turbo")
response = await llm.generate([{"role": "user", "content": "Hello"}])
print(response)

# Test tool provider
from xaibo.primitives.modules.tools.python_tool_provider import PythonToolProvider

tools = PythonToolProvider(tool_packages=["tools.example"])
available_tools = tools.get_tools()
print(f"Available tools: {[t.name for t in available_tools]}")

# Test tool execution
result = await tools.call_tool("current_time", {})
print(result)
```

### Network Debugging

```bash
# Test API connectivity
curl -v https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test local server
curl -v http://localhost:9001/openai/models

# Monitor network traffic
tcpdump -i any port 443  # Monitor HTTPS traffic
```

---

## Performance Optimization

### LLM Performance

1. **Model Selection:**
   ```yaml
   # Fast models for development
   model: gpt-3.5-turbo
   
   # Balanced performance/quality
   model: gpt-4-turbo
   
   # High quality (slower)
   model: gpt-4
   ```

2. **Request Optimization:**
   ```yaml
   config:
     temperature: 0.3  # Lower for faster, more deterministic responses
     max_tokens: 500   # Limit response length
     top_p: 0.9       # Reduce sampling space
   ```

3. **Caching:**
   ```python
   # Implement response caching
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def cached_llm_call(prompt_hash):
       # Cache LLM responses
       pass
   ```

### Memory Performance

1. **Efficient Embeddings:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
       id: embedder
       config:
         model_name: all-MiniLM-L6-v2  # Fast, small model
         model_kwargs:
           device: cpu  # Use GPU if available
   ```

2. **Chunking Strategy:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.memory.TokenChunker
       id: chunker
       config:
         window_size: 256    # Smaller chunks
         window_overlap: 25  # Less overlap
   ```

3. **Vector Index Optimization:**
   ```yaml
   modules:
     - module: xaibo.primitives.modules.memory.NumpyVectorIndex
       id: vector_index
       config:
         storage_dir: ./vectors
         batch_size: 100  # Process in batches
   ```

### Tool Performance

1. **Async Tools:**
   ```python
   @tool
   async def async_tool(data: str) -> str:
       """Use async for I/O bound operations"""
       async with aiohttp.ClientSession() as session:
           async with session.get(f"https://api.example.com/{data}") as response:
               return await response.text()
   ```

2. **Connection Pooling:**
   ```python
   # Reuse connections
   import aiohttp
   
   # Global session
   session = aiohttp.ClientSession()
   
   @tool
   async def api_call(endpoint: str) -> dict:
       async with session.get(endpoint) as response:
           return await response.json()
   ```

3. **Caching:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=256)
   @tool
   def cached_computation(input_data: str) -> str:
       """Cache expensive computations"""
       # Expensive operation here
       return result
   ```

---

## Error Messages and Meanings

### Configuration Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `ModuleNotFoundError: No module named 'xaibo.primitives.modules.llm.OpenAILLM'` | Missing dependency | Install with `pip install xaibo[openai]` |
| `ExchangeConfigurationError: No provider found for protocol 'LLMProtocol'` | Missing exchange configuration | Add explicit exchange or ensure module provides protocol |
| `ValidationError: Invalid agent configuration` | YAML syntax or structure error | Check YAML syntax and required fields |

### Runtime Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `AuthenticationError: Incorrect API key provided` | Invalid API key | Check API key format and environment variables |
| `RateLimitError: Rate limit reached` | Too many API requests | Implement retry logic or use different model |
| `TimeoutError: Request timed out` | Request took too long | Increase timeout or optimize request |
| `ConnectionError: Failed to connect` | Network connectivity issue | Check internet connection and firewall |

### Tool Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `ToolNotFoundError: Tool 'example' not found` | Tool not registered | Check tool package import and @tool decorator |
| `ToolExecutionError: Tool execution failed` | Tool runtime error | Check tool implementation and error handling |
| `ValidationError: Invalid tool arguments` | Wrong arguments passed to tool | Check tool parameter schema |

---

## FAQ

### General Questions

**Q: Can I use multiple LLM providers in the same agent?**

A: Yes, you can configure multiple LLM modules and route them through different exchanges or use an LLM combinator.

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: primary-llm
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: secondary-llm
  - module: xaibo.primitives.modules.llm.LLMCombinator
    id: combined-llm
```

**Q: How do I handle sensitive data like API keys?**

A: Always use environment variables or secure secret management:

```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Q: Can I run Xaibo in production?**

A: Yes, Xaibo is designed for production use. Use proper configuration management, monitoring, and security practices.

### Technical Questions

**Q: How do I create custom protocols?**

A: Define a protocol interface and implement it in your modules:

```python
from abc import ABC, abstractmethod

class CustomProtocol(ABC):
    @abstractmethod
    async def custom_method(self, data: str) -> str:
        pass
```

**Q: How do I monitor agent performance?**

A: Use the debug event listener and implement custom monitoring:

```python
class PerformanceMonitor:
    def on_event(self, event):
        if event.type == "module.call.end":
            duration = event.data.get("duration")
            print(f"Module call took {duration}ms")
```

**Q: Can I use Xaibo with other frameworks?**

A: Yes, Xaibo provides OpenAI-compatible APIs and can integrate with any system that supports OpenAI's chat completions format.

!!! tip "Getting Help"
    - Check the [GitHub Issues](https://github.com/xpressai/xaibo/issues) for known problems
    - Join the [Discord community](https://discord.gg/uASMzSSVKe) for real-time help
    - Enable debug logging to get detailed error information
    - Use the debug UI to visualize agent operations

!!! warning "Common Pitfalls"
    - Don't commit API keys to version control
    - Always validate user inputs in custom tools
    - Use timeouts for external API calls
    - Monitor memory usage with large vector indices
    - Test configurations in development before production deployment