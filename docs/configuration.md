# Configuration Guide

This comprehensive guide covers all aspects of configuring Xaibo agents, from basic setups to advanced scenarios.

---

## Agent Configuration File Format

Xaibo agents are configured using YAML files that define modules, their dependencies, and how they connect together.

### Basic Structure

```yaml
id: my-agent                    # Unique identifier for the agent
description: Agent description  # Human-readable description
modules:                       # List of modules that make up the agent
  - module: module.path.Class  # Python import path
    id: unique-id             # Unique identifier within this agent
    config:                   # Module-specific configuration
      key: value
exchange:                     # Optional: explicit dependency wiring
  - module: consumer-id       # Module that needs a dependency
    protocol: ProtocolName    # Protocol interface required
    provider: provider-id     # Module that provides the implementation
```

### Complete Example

```yaml
id: comprehensive-agent
description: A fully configured agent with multiple capabilities
modules:
  # Language Model
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      temperature: 0.7
      max_tokens: 2000
      timeout: 60.0

  # Memory System
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: ./agent_memories.pkl

  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: all-MiniLM-L6-v2

  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 512
      window_overlap: 50

  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: ./vector_storage

  # Tools
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.utilities, tools.external_apis]

  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 30.0
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]

  # Orchestrator
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 15
      system_prompt: |
        You are an intelligent assistant with access to memory and various tools.
        Use your capabilities to provide helpful and accurate responses.

  # Event Listener
  - module: xaibo.primitives.event_listeners.DebugEventListener
    id: debug-listener

exchange:
  # Connect orchestrator to LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm

  # Connect orchestrator to tools
  - module: orchestrator
    protocol: ToolsProtocol
    provider: [python-tools, mcp-tools]  # Multiple tool providers

  # Connect memory components
  - module: memory
    protocol: ChunkerProtocol
    provider: chunker
  - module: memory
    protocol: EmbedderProtocol
    provider: embedder
  - module: memory
    protocol: VectorIndexProtocol
    provider: vector_index

  # Set entry point
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

---

## Module Configuration Options

### LLM Modules

#### OpenAI Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      # Required
      model: gpt-4                              # Model name

      # Authentication (optional - uses environment variables if not provided)
      api_key: sk-...                          # OpenAI API key
      organization: org-...                    # OpenAI organization ID

      # Connection settings
      base_url: https://api.openai.com/v1     # API endpoint
      timeout: 60.0                           # Request timeout in seconds

      # Generation parameters
      temperature: 0.7                        # Sampling temperature (0.0-2.0)
      max_tokens: 1000                        # Maximum tokens to generate
      top_p: 1.0                             # Nucleus sampling parameter
      frequency_penalty: 0.0                  # Frequency penalty (-2.0 to 2.0)
      presence_penalty: 0.0                   # Presence penalty (-2.0 to 2.0)
      stop: ["\n\n"]                         # Stop sequences
      seed: 42                               # Deterministic sampling seed
```

#### Anthropic Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      # Required
      model: claude-3-opus-20240229           # Model name

      # Authentication (optional - uses ANTHROPIC_API_KEY if not provided)
      api_key: sk-ant-...                    # Anthropic API key

      # Connection settings
      base_url: https://api.anthropic.com    # API endpoint
      timeout: 60.0                          # Request timeout in seconds

      # Generation parameters
      temperature: 0.7                       # Sampling temperature
      max_tokens: 1000                       # Maximum tokens to generate
      top_p: 1.0                            # Top-p sampling
      top_k: 40                             # Top-k sampling
      stop_sequences: ["Human:", "Assistant:"] # Stop sequences
```

#### Google Gemini Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: llm
    config:
      # Required
      model: gemini-2.0-flash-001            # Model name
      api_key: AIza...                       # Google API key

      # Vertex AI settings (optional)
      vertexai: false                        # Use Vertex AI instead of API
      project: my-gcp-project               # GCP project ID (required for Vertex AI)
      location: us-central1                  # GCP region (for Vertex AI)

      # Generation parameters
      temperature: 0.7                       # Sampling temperature
      max_tokens: 1000                       # Maximum tokens to generate
      top_p: 0.95                           # Top-p sampling
      top_k: 40                             # Top-k sampling
```

#### AWS Bedrock Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.BedrockLLM
    id: llm
    config:
      # Required
      model: anthropic.claude-v2             # Bedrock model ID

      # AWS settings (optional - uses default credentials if not provided)
      region_name: us-east-1                 # AWS region
      aws_access_key_id: AKIA...            # AWS access key
      aws_secret_access_key: ...            # AWS secret key
      aws_session_token: ...                # AWS session token (for temporary credentials)

      # Connection settings
      timeout: 60.0                          # Request timeout in seconds

      # Generation parameters
      temperature: 0.7                       # Sampling temperature
      max_tokens: 1000                       # Maximum tokens to generate
      top_p: 1.0                            # Top-p sampling
```

### Memory Modules

#### Vector Memory Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: ./memories.pkl       # Path to store memories
      max_memories: 10000                    # Maximum number of memories to store
      similarity_threshold: 0.7              # Minimum similarity for retrieval
```

#### Embedder Configurations

##### Sentence Transformers

```yaml
modules:
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: all-MiniLM-L6-v2          # Model name from Hugging Face
      model_kwargs:                          # Additional model parameters
        cache_folder: ./models               # Local cache directory
        device: cpu                          # Device to run on (cpu/cuda)
        trust_remote_code: false            # Trust remote code execution
```

##### OpenAI Embeddings

```yaml
modules:
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: text-embedding-ada-002         # Embedding model
      api_key: sk-...                       # OpenAI API key (optional)
      base_url: https://api.openai.com/v1  # API endpoint
      timeout: 30.0                         # Request timeout
      dimensions: 1536                      # Embedding dimensions (for newer models)
```

##### Hugging Face Transformers

```yaml
modules:
  - module: xaibo.primitives.modules.memory.HuggingFaceEmbedder
    id: embedder
    config:
      model_name: sentence-transformers/all-MiniLM-L6-v2  # Model name
      device: cuda                          # Device (cpu/cuda)
      max_length: 512                       # Maximum sequence length
      pooling_strategy: mean                # Pooling strategy (mean/cls/max)
      
      # Audio-specific settings (for audio models)
      audio_sampling_rate: 16000            # Audio sampling rate
      audio_max_length: 30                  # Maximum audio length in seconds
```

#### Chunker Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 512                      # Maximum tokens per chunk
      window_overlap: 50                    # Overlap between chunks
      encoding_name: cl100k_base            # Tiktoken encoding to use
```

#### Vector Index Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: ./vector_storage         # Directory for vector storage
      index_file: vectors.npy               # Vector storage file
      metadata_file: metadata.json          # Metadata storage file
```

### Tool Modules

#### Python Tool Provider

```yaml
modules:
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.utilities, tools.apis]  # Python packages containing tools
      tool_functions: []                    # Specific function objects (optional)
      auto_import: true                     # Automatically import tool packages
```

#### MCP Tool Provider

```yaml
modules:
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 30.0                         # Global timeout for MCP operations
      servers:
        # Stdio server (local process)
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace", "--verbose"]
          env:
            LOG_LEVEL: INFO
            PYTHONPATH: /custom/path

        # SSE server (HTTP-based)
        - name: web_search
          transport: sse
          url: https://api.example.com/mcp
          headers:
            Authorization: Bearer your-api-key
            Content-Type: application/json
            User-Agent: Xaibo/1.0

        # WebSocket server
        - name: database
          transport: websocket
          url: ws://localhost:8080/mcp
          headers:
            X-API-Key: your-websocket-key
            X-Client-ID: xaibo-client
```

### Orchestrator Modules

#### Stressing Tool User

```yaml
modules:
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10                      # Maximum reasoning iterations
      system_prompt: |                      # System prompt for the agent
        You are a helpful assistant with access to various tools.
        Think step by step and use tools when necessary.
      
      # Advanced settings
      thought_timeout: 30.0                 # Timeout for each thought iteration
      tool_timeout: 60.0                    # Timeout for tool execution
      max_tool_calls_per_thought: 5         # Maximum tools per iteration
      enable_parallel_tools: false          # Enable parallel tool execution
```

---

## Exchange Configuration Patterns

Exchange configurations define how modules connect to each other through protocol interfaces.

### Automatic Exchange Resolution

Xaibo can automatically resolve exchanges when there's an unambiguous match:

```yaml
id: simple-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 5
# No exchange section needed - automatically resolved
```

### Explicit Exchange Configuration

For complex scenarios or when you need precise control:

```yaml
exchange:
  # Single provider
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm

  # Multiple providers (list dependency)
  - module: orchestrator
    protocol: ToolsProtocol
    provider: [python-tools, mcp-tools]

  # Field-specific binding (when module has multiple dependencies of same type)
  - module: combinator
    protocol: LLMProtocol
    provider: primary-llm
    field_name: primary_llm
  - module: combinator
    protocol: LLMProtocol
    provider: secondary-llm
    field_name: secondary_llm

  # Entry point configuration
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Common Exchange Patterns

#### Memory-Enabled Agent

```yaml
exchange:
  # Connect memory components
  - module: memory
    protocol: ChunkerProtocol
    provider: chunker
  - module: memory
    protocol: EmbedderProtocol
    provider: embedder
  - module: memory
    protocol: VectorIndexProtocol
    provider: vector_index

  # Connect orchestrator to memory
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
```

#### Multi-LLM Agent

```yaml
exchange:
  # Primary LLM for main reasoning
  - module: orchestrator
    protocol: LLMProtocol
    provider: primary-llm

  # Secondary LLM for specialized tasks
  - module: specialist
    protocol: LLMProtocol
    provider: specialist-llm
```

#### Tool Chain Configuration

```yaml
exchange:
  # Multiple tool providers
  - module: orchestrator
    protocol: ToolsProtocol
    provider: [python-tools, mcp-tools, custom-tools]

  # Tool-specific routing
  - module: tool-router
    protocol: PythonToolsProtocol
    provider: python-tools
  - module: tool-router
    protocol: MCPToolsProtocol
    provider: mcp-tools
```

---

## Environment Variables and Settings

### Core Environment Variables

```bash
# API Keys
OPENAI_API_KEY=sk-...                    # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...            # Anthropic API key
GOOGLE_API_KEY=AIza...                  # Google API key

# AWS Credentials (for Bedrock)
AWS_ACCESS_KEY_ID=AKIA...               # AWS access key
AWS_SECRET_ACCESS_KEY=...               # AWS secret key
AWS_DEFAULT_REGION=us-east-1            # AWS region

# Xaibo Settings
XAIBO_LOG_LEVEL=INFO                    # Logging level
XAIBO_CONFIG_DIR=./agents               # Default agent directory
XAIBO_CACHE_DIR=./cache                 # Cache directory
XAIBO_DEBUG=true                        # Enable debug mode
```

### Development Environment

```bash
# Development settings
XAIBO_DEV_MODE=true                     # Enable development features
XAIBO_HOT_RELOAD=true                   # Enable hot reloading
XAIBO_MOCK_LLMS=false                   # Use mock LLMs for testing
XAIBO_TRACE_CALLS=true                  # Enable call tracing
```

### Server Configuration

```bash
# Web server settings
XAIBO_HOST=0.0.0.0                      # Server host
XAIBO_PORT=9001                         # Server port
XAIBO_WORKERS=1                         # Number of worker processes
XAIBO_CORS_ORIGINS=*                    # CORS allowed origins
```

### .env File Example

```bash title=".env"
# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Xaibo Configuration
XAIBO_LOG_LEVEL=INFO
XAIBO_DEBUG=false
XAIBO_CONFIG_DIR=./agents

# Server Settings
XAIBO_HOST=127.0.0.1
XAIBO_PORT=9001

# Development
XAIBO_DEV_MODE=false
XAIBO_HOT_RELOAD=false
```

---

## Dependency Groups and Installation Options

Xaibo uses optional dependency groups to keep the core package lightweight while allowing you to install only what you need.

### Available Dependency Groups

```bash
# Core package only
pip install xaibo

# Web server capabilities
pip install xaibo[webserver]

# LLM providers
pip install xaibo[openai]
pip install xaibo[anthropic]
pip install xaibo[google]
pip install xaibo[bedrock]

# Local processing
pip install xaibo[local]

# Development tools
pip install xaibo[dev]

# Multiple groups
pip install xaibo[webserver,openai,anthropic]

# All features
pip install xaibo[webserver,openai,anthropic,google,bedrock,local]
```

### Dependency Group Contents

#### webserver
- `fastapi[standard]>=0.115.12` - Web framework
- `strawberry-graphql>=0.262.5` - GraphQL support
- `watchfiles>=1.0.4` - File watching for development
- `python-dotenv>=1.1.0` - Environment variable loading

#### openai
- `openai>=1.65.4` - OpenAI API client

#### anthropic
- `anthropic>=0.49.0` - Anthropic API client

#### google
- `google-genai>=1.5.0` - Google Generative AI client

#### bedrock
- `boto3>=1.37.38` - AWS SDK for Bedrock

#### local
- `sentence-transformers>=4.1.0` - Local embeddings
- `soundfile>=0.13.1` - Audio processing
- `tiktoken>=0.9.0` - Tokenization
- `transformers>=4.51.3` - Hugging Face transformers

#### dev
- `coverage>=7.8.0` - Code coverage
- `devtools>=0.12.2` - Development utilities

---

## Advanced Configuration Scenarios

### Multi-Environment Configuration

#### Development Configuration

```yaml title="agents/dev-agent.yml"
id: dev-agent
description: Development configuration with mocks and debugging
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: llm
    config:
      responses:
        - content: "Mock response for testing"
          model: mock-model
      streaming_delay: 100

  - module: xaibo.primitives.event_listeners.DebugEventListener
    id: debug-listener

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 3  # Reduced for faster testing
      system_prompt: "Development mode assistant"
```

#### Production Configuration

```yaml title="agents/prod-agent.yml"
id: prod-agent
description: Production configuration with real LLMs
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      temperature: 0.3  # Lower temperature for consistency
      timeout: 120.0    # Longer timeout for production

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 20  # More thorough reasoning
      system_prompt: |
        You are a production assistant. Be accurate and helpful.
```

### Configuration Inheritance

```yaml title="agents/base-agent.yml"
# Base configuration
id: base-agent
description: Base agent configuration
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config: &llm-config
      model: gpt-3.5-turbo
      temperature: 0.7
      timeout: 60.0

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config: &orchestrator-config
      max_thoughts: 10
      system_prompt: "You are a helpful assistant"
```

```yaml title="agents/specialized-agent.yml"
# Specialized configuration inheriting from base
id: specialized-agent
description: Specialized agent with enhanced capabilities
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      <<: *llm-config
      model: gpt-4  # Override model

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      <<: *orchestrator-config
      max_thoughts: 15  # Override max thoughts
      system_prompt: |
        You are a specialized assistant with enhanced reasoning capabilities.
```

### Conditional Configuration

```yaml
id: adaptive-agent
description: Agent with conditional configuration
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: "{{ env.XAIBO_MODEL | default('gpt-3.5-turbo') }}"
      temperature: "{{ env.XAIBO_TEMPERATURE | float | default(0.7) }}"
      api_key: "{{ env.OPENAI_API_KEY }}"

  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: "{{ env.XAIBO_MAX_THOUGHTS | int | default(10) }}"
      system_prompt: "{{ env.XAIBO_SYSTEM_PROMPT | default('You are a helpful assistant') }}"
```

### Multi-Agent Configuration

```yaml title="agents/coordinator.yml"
id: coordinator
description: Coordinator agent that manages other agents
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4

  - module: custom.modules.AgentCoordinator
    id: coordinator
    config:
      sub_agents:
        - specialist-agent
        - research-agent
        - writing-agent
      routing_strategy: capability_based
```

!!! tip "Configuration Best Practices"
    - Use environment variables for sensitive data like API keys
    - Keep development and production configurations separate
    - Use YAML anchors and references to avoid duplication
    - Validate configurations before deployment
    - Document custom configuration options
    - Use meaningful IDs and descriptions for modules

!!! warning "Security Considerations"
    - Never commit API keys to version control
    - Use environment variables or secure secret management
    - Restrict file permissions on configuration files
    - Validate all configuration inputs
    - Use HTTPS for all external API connections

!!! note "Performance Tuning"
    - Adjust timeouts based on your use case
    - Configure appropriate batch sizes for embeddings
    - Use local models for development to reduce API costs
    - Monitor memory usage with large vector indices
    - Consider caching strategies for frequently used data