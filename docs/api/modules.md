# Module APIs

## LLM Modules

### OpenAILLM

**Module:** [`xaibo.primitives.modules.llm.OpenAILLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/openai.py)

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      api_key: your-api-key  # Optional, uses OPENAI_API_KEY env var
      base_url: https://api.openai.com/v1  # Optional
      timeout: 60.0  # Optional
      temperature: 0.7  # Optional
      max_tokens: 1000  # Optional
```

**Configuration Options:**
- `model` (required): Model name (e.g., "gpt-4", "gpt-3.5-turbo")
- `api_key` (optional): OpenAI API key
- `base_url` (optional): Custom API endpoint
- `timeout` (optional): Request timeout in seconds
- `temperature` (optional): Sampling temperature
- `max_tokens` (optional): Maximum tokens to generate

### AnthropicLLM

**Module:** [`xaibo.primitives.modules.llm.AnthropicLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/anthropic.py)

```yaml
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      model: claude-3-opus-20240229
      api_key: your-api-key  # Optional, uses ANTHROPIC_API_KEY env var
      timeout: 60.0  # Optional
      temperature: 0.7  # Optional
      max_tokens: 1000  # Optional
```

### GoogleLLM

**Module:** [`xaibo.primitives.modules.llm.GoogleLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/google.py)

```yaml
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: llm
    config:
      model: gemini-2.0-flash-001
      api_key: your-api-key
      vertexai: false  # Optional, use Vertex AI
      project: your-project-id  # Required for Vertex AI
      location: us-central1  # Optional for Vertex AI
```

## Memory Modules

### VectorMemory

**Module:** [`xaibo.primitives.modules.memory.VectorMemory`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/vector_memory.py)

```yaml
modules:
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: ./memories.pkl
```

**Dependencies:** Requires chunker, embedder, and vector_index modules.

### SentenceTransformerEmbedder

**Module:** [`xaibo.primitives.modules.memory.SentenceTransformerEmbedder`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/sentence_transformer_embedder.py)

```yaml
modules:
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: all-MiniLM-L6-v2
      model_kwargs:
        cache_folder: ./models
        device: cpu
```

## Tool Modules

### PythonToolProvider

**Module:** [`xaibo.primitives.modules.tools.PythonToolProvider`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/python_tool_provider.py)

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example, tools.utilities]
```

**Usage Example:**

```python
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    """Gets the current time in UTC"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def calculate_sum(numbers: list[float]) -> float:
    """Calculate the sum of a list of numbers"""
    return sum(numbers)
```

### MCPToolProvider

**Module:** [`xaibo.primitives.modules.tools.MCPToolProvider`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/mcp_tool_provider.py)

```yaml
modules:
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 60.0
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]
          env:
            LOG_LEVEL: "INFO"
        - name: web_search
          transport: sse
          url: "https://api.example.com/mcp"
          headers:
            Authorization: "Bearer your-api-key"
```

## Configuration APIs

### Agent Configuration

Agent configurations are defined in YAML files:

```yaml
id: my-agent
description: A comprehensive example agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to tools.
exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolsProtocol
    provider: python-tools
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Programmatic Configuration

```python
from xaibo import Xaibo
from xaibo.core.config import AgentConfig, ModuleConfig

# Create agent configuration
agent_config = AgentConfig(
    id="my-agent",
    description="Programmatically configured agent",
    modules=[
        ModuleConfig(
            module="xaibo.primitives.modules.llm.OpenAILLM",
            id="llm",
            config={"model": "gpt-4"}
        )
    ]
)

# Initialize Xaibo and register agent
xaibo = Xaibo()
xaibo.register_agent(agent_config)
```

## Custom Module Implementation

```python
from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMResponse

class CustomLLM(LLMProtocol):
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    async def generate(self, messages, **kwargs) -> LLMResponse:
        # Custom LLM implementation
        response_text = f"Response from {self.model_name}"
        return LLMResponse(
            content=response_text,
            model=self.model_name,
            usage={"total_tokens": len(response_text)}
        )
```

## Tool Development

```python
from xaibo.primitives.modules.tools.python_tool_provider import tool
import requests

@tool
def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    # Implementation here
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()["current"]["condition"]

@tool
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates"""
    # Implementation here
    import math
    # Haversine formula implementation
    return distance_km
```

!!! tip "API Best Practices"
    - Always handle errors gracefully in custom modules
    - Use type hints for better API documentation
    - Implement proper logging for debugging
    - Follow the protocol interfaces exactly
    - Test modules in isolation before integration

!!! note "Version Compatibility"
    This API reference is for Xaibo version 0.0.0.dev0. APIs may change between versions. Check the [changelog](https://github.com/xpressai/xaibo/releases) for updates.