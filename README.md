# Xaibo

Xaibo is a modular agent framework designed for building flexible AI systems with clean protocol-based interfaces.

## Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
  - [Interacting with Xaibo](#interacting-with-xaibo)
  - [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Core Concepts](#core-concepts)
- [Detailed Documentation](#detailed-documentation)
  - [Dependency Groups](#dependency-groups)
  - [Exchange Configuration](#exchange-configuration)
  - [Protocol Implementations](#protocol-implementations)
  - [Web Server and API Adapters](#web-server-and-api-adapters)
- [Development](#development)
- [Get Involved](#get-involved)

## Introduction

Xaibo uses a protocol-driven architecture that allows components to interact through well-defined interfaces. This approach enables:

- **Modularity**: Easily swap components without changing other parts of the system
- **Extensibility**: Add new capabilities by implementing existing protocols or defining new ones  
- **Testability**: Mock dependencies for isolated testing

## Prerequisites

Before installing Xaibo, ensure you have:
- Python 3.10 or higher installed
- pip or uv package manager

## Quick Start

```bash
# Install uv if you don't have it
pip install uv

# Initialize a new Xaibo project
uvx xaibo init my_project

# Start the development server
cd my_project
uv run xaibo dev
```

This sets up a recommended project structure with an example agent and starts a server with a debug UI and OpenAI-compatible API.

### Interacting with Xaibo

Once the development server is running, you can interact with it using the OpenAI-compatible API:

```bash
# Send a simple chat completion request to the Xaibo OpenAI-compatible API
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Hello, what time is it now?"}
    ]
  }'
```

```bash
# Same request using HTTPie (a more user-friendly alternative to curl)
http POST http://127.0.0.1:9001/openai/chat/completions \
  model=example \
  messages:='[{"role": "user", "content": "Hello, what time is it now?"}]'
```

This will route your request to the example agent configured in your project.

The development server also provides a debug UI that visualizes the agent's operations:

<div style="display: flex; gap: 10px; margin: 20px 0;">
  <div style="flex: 1;">
    <img src="docs/images/sequence-diagram.png" alt="Xaibo Debug UI - Sequence Diagram Overview" width="100%">
    <p><em>Sequence Diagram Overview</em></p>
  </div>
  <div style="flex: 1;">
    <img src="docs/images/detail-view.png" alt="Xaibo Debug UI - Detail View" width="100%">
    <p><em>Detail View of Component Interactions</em></p>
  </div>
</div>

### Project Structure

When you run `uvx xaibo init my_project`, Xaibo creates the following structure:

```
my_project/
├── agents/
│   └── example.yml    # Example agent configuration
├── modules/
│   └── __init__.py
├── tools/
│   ├── __init__.py
│   └── example.py     # Example tool implementation
├── tests/
│   └── test_example.py
└── .env               # Environment variables
```

#### Example Agent

The initialization creates an example agent with a simple tool:

```yaml
# agents/example.yml
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.
```

#### Example Tool

```python
# tools/example.py
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
```

## Key Features

### Protocol-Based Architecture

Components communicate through well-defined protocol interfaces, creating clear boundaries:

- **Clean Separation**: Modules interact only through protocols, not implementation details
- **Easy Testing**: Mock any component by providing an alternative that implements the same protocol
- **Flexible Composition**: Mix and match components as long as they fulfill required protocols

### Dependency Injection

Components explicitly declare what they need:

- **Easy Swapping**: Change implementations without rewriting core logic (e.g., switch memory from SQLite to cloud)
- **Superior Testing**: Inject predictable mocks instead of real LLMs for deterministic tests
- **Clear Boundaries**: Explicit dependencies create better architecture

### Transparent Proxies

Every component is wrapped with a "two-way mirror" that:

- **Observes Every Call**: Parameters, timing, exceptions are all captured
- **Enables Complete Visibility**: Detailed runtime insights into your agent's operations
- **Provides Debug Data**: Automatic generation of test cases from production runs

### Comprehensive Event System

Built-in event system for monitoring:

- **Debug Event Viewer**: Visual inspection of agent operations in real-time
- **Call Sequences**: Track every interaction between components
- **Performance Monitoring**: Identify bottlenecks and optimize agent behavior

## Core Concepts

Xaibo is built around several key architectural concepts that provide its flexibility and power:

### Protocols

Protocols define interfaces that components must implement, creating clear boundaries between different parts of the system. Core protocols include:

- **LLM Protocol**: Defines how to interact with language models
- **Tools Protocol**: Standardizes tool integration
- **Memory Protocol**: Defines how agents store and retrieve information
- **Response Protocol**: Specifies how agents provide responses
- **Conversation Protocol**: Manages dialog history
- **Message Handlers Protocol**: Defines how to process different input types

### Modules

Modules are the building blocks of Xaibo agents. Each module implements one or more protocols and can depend on other modules. Examples include:

- LLM modules (OpenAI, Anthropic, Google, etc.)
- Memory modules (Vector memory, embedders, chunkers)
- Tool modules (Python tools, function calling)
- Orchestrator modules (manage agent behavior)

### Exchanges

Exchanges are the connections between modules that define how dependencies are resolved. They create a flexible wiring system that allows modules to declare what protocols they need without knowing the specific implementation.

## Detailed Documentation

<details>
<summary><strong>Dependency Groups</strong> - How to install dependencies for different use cases</summary>

Xaibo organizes its dependencies into logical groups that can be installed based on your specific needs. This approach keeps the core package lightweight while allowing you to add only the dependencies required for your use case.

### Available Dependency Groups

- **webserver**: Dependencies for running the web server and API adapters
  - Includes: fastapi, strawberry-graphql, watchfiles, python-dotenv
  - Use when: You need to run the Xaibo server with UI and API endpoints

- **openai**: Dependencies for OpenAI LLM integration
  - Includes: openai client library
  - Use when: You want to use OpenAI models (GPT-3.5, GPT-4, etc.)

- **anthropic**: Dependencies for Anthropic Claude integration
  - Includes: anthropic client library
  - Use when: You want to use Anthropic Claude models

- **google**: Dependencies for Google Gemini integration
  - Includes: google-genai client library
  - Use when: You want to use Google's Gemini models

- **bedrock**: Dependencies for AWS Bedrock integration
  - Includes: boto3
  - Use when: You want to use AWS Bedrock models

- **local**: Dependencies for local embeddings, tokenization, and transformers
  - Includes: sentence-transformers, soundfile, tiktoken, transformers
  - Use when: You want to run embeddings or tokenization locally

- **dev**: Dependencies for development tools
  - Includes: coverage, devtools
  - Use when: You're developing or contributing to Xaibo

### Installing Dependency Groups

You can install Xaibo with specific dependency groups using pip's "extras" syntax:

```bash
# Install core package
pip install xaibo

# Install with specific dependency groups
pip install xaibo[openai,anthropic]

# Install all dependency groups
pip install xaibo[webserver,openai,anthropic,google,bedrock,local]

# Install for development
pip install xaibo[dev]
```

</details>

<details>
<summary><strong>Exchange Configuration</strong> - How to configure module connections</summary>

The exchange configuration is a core concept in Xaibo that defines how modules are connected to each other. It enables the dependency injection system by specifying which module provides an implementation for a protocol that another module requires.

### What are Exchanges in Xaibo?

In Xaibo, exchanges are the connections between modules that define how dependencies are resolved. They create a flexible wiring system that allows:

- Modules to declare what protocols they need without knowing the specific implementation
- Easy swapping of implementations without changing the modules that use them
- Clear separation of concerns through protocol-based interfaces
- Support for both singleton and list-type dependencies

### Exchange Configuration Structure

An exchange configuration consists of:

- `module`: The ID of the module that requires a dependency
- `protocol`: The protocol interface that defines the dependency
- `provider`: The ID of the module that provides the implementation (or a list of module IDs for list dependencies)
- `field_name`: Optional parameter name in the module's constructor (useful when a module has multiple dependencies of the same protocol type)

### Configuring Exchanges

Exchanges can be configured explicitly in your agent YAML file or automatically inferred by Xaibo:

#### Explicit Configuration

```yaml
id: my-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
exchange:
  # Connect the orchestrator to the LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  # Set the entry point for text messages
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

#### Implicit Configuration

Xaibo can automatically infer exchange configurations when there's an unambiguous match between a module that requires a protocol and a module that provides it. For example, if only one module provides the `LLMProtocol` and another module requires it, Xaibo will automatically create the exchange.

### Examples from Test Resources

#### Minimal Configuration (echo.yaml)

```yaml
# This is a minimal configuration where exchanges are inferred
id: echo-agent-minimal
modules:
  - module: xaibo_examples.echo.Echo
    id: echo
    config:
        prefix: "You said: "
```

In this example, the Echo module provides the `TextMessageHandlerProtocol` and requires the `ResponseProtocol`. Xaibo automatically configures the exchanges.

#### Complete Configuration (echo_complete.yaml)

```yaml
id: echo-agent
modules:
  - module: xaibo_examples.echo.Echo
    id: echo
    provides: [TextMessageHandlerProtocol]
    uses: [ResponseProtocol]
    config:
        prefix: "You said: "
  - module: xaibo.primitives.modules.ResponseHandler
    id: __response__
    provides: [ResponseProtocol]
exchange:
  # Set the entry point for text messages
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: echo
  # Connect the echo module to the response handler
  - module: echo
    protocol: ResponseProtocol
    provider: __response__
```

This example explicitly defines all exchanges, making the configuration more verbose but also more explicit.

#### List Dependencies

Xaibo also supports list-type dependencies, where a module can depend on multiple implementations of the same protocol:

```yaml
exchange:
  # Provide multiple dependencies to a single module
  - module: list_module
    protocol: DependencyProtocol
    provider: [dep1, dep2, dep3]
```

This is useful for modules that need to work with multiple implementations of the same protocol, such as a module that needs to process multiple types of tools.

### Special Exchange Configurations

- `__entry__`: A special module identifier that represents the entry point for handling messages. It must be connected to a module that provides a message handler protocol.
- `__response__`: A special module that provides the `ResponseProtocol` for sending responses back to the user.

</details>

<details>
<summary><strong>Protocol Implementations</strong> - Available implementations for each protocol</summary>

Xaibo provides several implementations for each protocol to support different use cases:

### LLM Implementations

- `xaibo.primitives.modules.llm.OpenAILLM`: Integrates with OpenAI's models (GPT-3.5, GPT-4, etc.)
  - **Python Dependencies**: `openai` dependency group
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model`: Model name (e.g., "gpt-4", "gpt-4.1-nano")
    - `api_key`: OpenAI API key (optional, falls back to environment variable)
    - `base_url`: Base URL for the OpenAI API (default: "https://api.openai.com/v1")
    - `timeout`: Timeout for API requests in seconds (default: 60.0)
    - Additional parameters like `temperature`, `max_tokens`, and `top_p` are passed to the API

- `xaibo.primitives.modules.llm.AnthropicLLM`: Connects to Anthropic's Claude models
  - **Python Dependencies**: `anthropic` dependency group
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model`: Model name (e.g., "claude-3-opus-20240229", "claude-3-sonnet")
    - `api_key`: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
    - `base_url`: Base URL for the Anthropic API
    - `timeout`: Timeout for API requests in seconds (default: 60.0)
    - Additional parameters like `temperature` and `max_tokens` are passed to the API

- `xaibo.primitives.modules.llm.GoogleLLM`: Supports Google's Gemini models
  - **Python Dependencies**: `google` dependency group
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model`: Model name (e.g., "gemini-2.0-flash-001", "gemini-pro", "gemini-ultra")
    - `api_key`: Google API key
    - `vertexai`: Whether to use Vertex AI (default: False)
    - `project`: Project ID for Vertex AI
    - `location`: Location for Vertex AI (default: "us-central1")
    - Parameters like `temperature` and `max_tokens` are passed through options

- `xaibo.primitives.modules.llm.BedrockLLM`: Interfaces with AWS Bedrock models
  - **Python Dependencies**: `bedrock` dependency group
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model`: Bedrock model ID (default: "anthropic.claude-v2")
    - `region_name`: AWS region (default: "us-east-1")
    - `aws_access_key_id`: AWS access key (optional, will use default credentials if not provided)
    - `aws_secret_access_key`: AWS secret key (optional, will use default credentials if not provided)
    - `timeout`: Timeout for API requests in seconds (default: 60.0)
    - Parameters like `temperature` and `max_tokens` are passed through options

- `xaibo.primitives.modules.llm.LLMCombinator`: Combines multiple LLMs for advanced workflows
  - **Python Dependencies**: None
  - **Constructor Dependencies**: List of LLM instances
  - **Config options**:
    - `prompts`: List of specialized prompts, one for each LLM

- `xaibo.primitives.modules.llm.MockLLM`: Provides test responses for development and testing
  - **Python Dependencies**: None
  - **Constructor Dependencies**: None
  - **Config options**:
    - `responses`: Predefined responses to return in the LLMResponse format
    - `streaming_delay`: Simulated response delay in milliseconds (default: 0)
    - `streaming_chunk_size`: Number of characters per chunk when streaming (default: 3)

### Memory Implementations

- `xaibo.primitives.modules.memory.VectorMemory`: General-purpose memory system using vector embeddings
  - **Python Dependencies**: None
  - **Constructor Dependencies**: Chunker, embedder, and vector_index
  - **Config options**:
    - `memory_file_path`: Path to the pickle file for storing memories

- `xaibo.primitives.modules.memory.NumpyVectorIndex`: Simple vector index using NumPy for storage and retrieval
  - **Python Dependencies**: `numpy` (core dependency)
  - **Constructor Dependencies**: None
  - **Config options**:
    - `storage_dir`: Directory path for storing vector and attribute files

- `xaibo.primitives.modules.memory.TokenChunker`: Splits text based on token counts for optimal embedding
  - **Python Dependencies**: `local` dependency group (for `tiktoken`)
  - **Constructor Dependencies**: None
  - **Config options**:
    - `window_size`: Maximum number of tokens per chunk (default: 512)
    - `window_overlap`: Number of tokens to overlap between chunks (default: 50)
    - `encoding_name`: Name of the tiktoken encoding to use (default: "cl100k_base")

- `xaibo.primitives.modules.memory.SentenceTransformerEmbedder`: Uses Sentence Transformers for text embeddings
  - **Python Dependencies**: `local` dependency group (for `sentence-transformers`)
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model_name`: Name of the sentence-transformer model to use (default: "all-MiniLM-L6-v2")
    - `model_kwargs`: Optional dictionary of keyword arguments to pass to SentenceTransformer constructor (e.g., cache_folder, device, etc.)

- `xaibo.primitives.modules.memory.HuggingFaceEmbedder`: Leverages Hugging Face models for embeddings
  - **Python Dependencies**: `local` dependency group (for `transformers`)
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model_name`: Name of the Hugging Face model to use (default: "sentence-transformers/all-MiniLM-L6-v2")
    - `device`: Device to run model on (default: "cuda" if available, else "cpu")
    - `max_length`: Maximum sequence length for tokenizer (default: 512)
    - `pooling_strategy`: How to pool token embeddings (default: "mean") - Options: "mean", "cls", "max"
    - Audio-specific options: `audio_sampling_rate`, `audio_max_length`, `audio_return_tensors`

- `xaibo.primitives.modules.memory.OpenAIEmbedder`: Utilizes OpenAI's embedding models
  - **Python Dependencies**: `openai` dependency group
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model`: Model name (e.g., "text-embedding-ada-002")
    - `api_key`: OpenAI API key (optional, falls back to environment variable)
    - `base_url`: Base URL for the OpenAI API (default: "https://api.openai.com/v1")
    - `timeout`: Timeout for API requests in seconds (default: 60.0)
    - Additional parameters like `dimensions` and `encoding_format` are passed to the API

### Tool Implementations

- `xaibo.primitives.modules.tools.PythonToolProvider`: Converts Python functions into tools using the `@tool` decorator
  - **Python Dependencies**: `docstring_parser` (core dependency)
  - **Constructor Dependencies**: None
  - **Config options**:
    - `tool_packages`: List of Python package paths containing tool functions
    - `tool_functions`: Optional list of function objects to use as tools
  - Usage:
    ```python
    @tool
    def current_time():
        """Returns the current time"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    ```

- `xaibo.primitives.modules.tools.MCPToolProvider`: Connects to MCP (Model Context Protocol) servers to provide their tools
  - **Python Dependencies**: `aiohttp`, `websockets` (core dependencies)
  - **Constructor Dependencies**: None
  - **Config options**:
    - `servers`: List of MCP server configurations (required)
    - `timeout`: Optional timeout for server operations in seconds (default: 30.0)
    - Server configuration structure:
      - `name`: Unique identifier for the server (required)
      - `transport`: Transport type - "stdio", "sse", or "websocket" (required)
      - For `stdio` transport:
        - `command`: List of command and arguments to start the server process (default: [])
        - `args`: Additional arguments (default: [])
        - `env`: Environment variables for the process (default: {})
      - For `sse` and `websocket` transports:
        - `url`: Server URL (default: "")
        - `headers`: HTTP headers for authentication/configuration (default: {})
  - **Features**:
    - Supports multiple MCP servers simultaneously
    - Tools are namespaced with server name (e.g., "server_name.tool_name")
    - Automatic connection management and protocol communication
    - Caches tool definitions for performance
    - Handles different transport mechanisms (stdio, SSE, WebSocket)
  - Usage:
    ```yaml
    # Agent configuration with MCP tool provider
    modules:
      - id: mcp-tools
        module: xaibo.primitives.modules.tools.MCPToolProvider
        config:
          timeout: 60.0
          servers:
            # Stdio server (local process)
            - name: filesystem
              transport: stdio
              command: ["python", "-m", "mcp_server_filesystem"]
              args: ["--root", "/workspace"]
              env:
                LOG_LEVEL: "INFO"
            # SSE server (HTTP-based)
            - name: web_search
              transport: sse
              url: "https://api.example.com/mcp"
              headers:
                Authorization: "Bearer your-api-key"
                Content-Type: "application/json"
            # WebSocket server
            - name: database
              transport: websocket
              url: "ws://localhost:8080/mcp"
              headers:
                X-API-Key: "your-websocket-key"
    ```

These implementations can be mixed and matched to create agents with different capabilities, and you can create your own implementations by following the protocol interfaces.

</details>

<details>
<summary><strong>Web Server and API Adapters</strong> - Server configuration and API compatibility</summary>

Xaibo includes built-in adapters for easy integration with existing tools. 
But you can also create your own API Adapters. Below you can see how a fully custom API
setup could look like.

### OpenAI API Compatibility

Use Xaibo with any client that supports the OpenAI Chat Completions API:
```python
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter

# Initialize Xaibo and register your agents
xaibo = Xaibo()
xaibo.register_agent(my_agent_config)

# Create a web server with the OpenAI adapter
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[OpenAiApiAdapter(xaibo)]
)

# Start the server
server.run(host="0.0.0.0", port=8000)
```

### OpenAI Responses API Adapter

The OpenAI Responses API adapter provides an implementation of OpenAI's Responses API, which differs from the standard Chat Completions API by offering stateful conversation management, response storage, and enhanced streaming capabilities. This adapter enables more sophisticated conversational workflows with persistent state and response tracking.

#### What is the OpenAI Responses API Adapter?

The OpenAI Responses API adapter implements the [OpenAI Responses API specification](https://platform.openai.com/docs/api-reference/responses), providing:

- **Stateful Conversations**: Maintains conversation history across multiple requests using [`previous_response_id`](src/xaibo/server/adapters/openai_responses.py:300)
- **Response Storage**: Persistent storage of responses, input items, and conversation history in SQLite database
- **Streaming Support**: Real-time streaming responses with detailed event sequences
- **Response Management**: Create, retrieve, delete, and cancel responses
- **Input Item Tracking**: Store and retrieve input items associated with each response
- **Background Processing**: Support for background response processing with cancellation capabilities

#### Key Features

- **Conversation Continuity**: Link responses together using [`previous_response_id`](src/xaibo/server/adapters/openai_responses.py:300) to maintain conversation state
- **Flexible Input Formats**: Support for both simple text strings and complex array-based input structures
- **Comprehensive Storage**: SQLite database stores responses, input items, and conversation history
- **Event-Driven Streaming**: Detailed streaming events including [`response.created`](src/xaibo/server/adapters/openai_responses.py:377), [`response.output_text.delta`](src/xaibo/server/adapters/openai_responses.py:404), and [`response.completed`](src/xaibo/server/adapters/openai_responses.py:572)
- **Response Lifecycle Management**: Full CRUD operations on stored responses
- **Metadata Support**: Attach custom metadata to responses for tracking and organization

#### Available Endpoints

The adapter provides the following REST endpoints under the `/openai` prefix:

- **POST `/openai/responses`**: Create a new response (streaming or non-streaming)
- **GET `/openai/responses/{response_id}`**: Retrieve a stored response
- **DELETE `/openai/responses/{response_id}`**: Delete a response and its associated data
- **POST `/openai/responses/{response_id}/cancel`**: Cancel a background response
- **GET `/openai/responses/{response_id}/input_items`**: List input items for a response

#### Usage Examples

##### Command Line Usage

Start the Xaibo server with the OpenAI Responses adapter:

```bash
# Start server with OpenAI Responses adapter
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiResponsesApiAdapter \
  --host 127.0.0.1 \
  --port 8000
```

##### Programmatic Usage

```python
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai_responses import OpenAiResponsesApiAdapter

# Initialize Xaibo and register your agents
xaibo = Xaibo()
xaibo.register_agent(my_agent_config)

# Create a web server with the OpenAI Responses adapter
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[OpenAiResponsesApiAdapter(xaibo, responses_dir="./responses")]
)

# Start the server
server.start()
```

##### API Usage Examples

**Create a simple response:**

```bash
curl -X POST http://127.0.0.1:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-agent",
    "input": "Hello, how are you today?"
  }'
```

**Create a streaming response:**

```bash
curl -X POST http://127.0.0.1:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-agent",
    "input": "Tell me a story",
    "stream": true
  }'
```

**Continue a conversation:**

```bash
curl -X POST http://127.0.0.1:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-agent",
    "input": "What did I just ask you?",
    "previous_response_id": "resp_abc123"
  }'
```

**Create a response with metadata:**

```bash
curl -X POST http://127.0.0.1:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-agent",
    "input": "Analyze this data",
    "metadata": {
      "user_id": "user123",
      "session_id": "session456"
    },
    "instructions": "You are a data analysis expert."
  }'
```

**Retrieve a response:**

```bash
curl -X GET http://127.0.0.1:8000/openai/responses/resp_abc123
```

**Get input items for a response:**

```bash
curl -X GET http://127.0.0.1:8000/openai/responses/resp_abc123/input_items
```

#### Configuration Options

The [`OpenAiResponsesApiAdapter`](src/xaibo/server/adapters/openai_responses.py:22) constructor accepts the following parameters:

- **`xaibo`**: The Xaibo instance containing registered agents
- **`streaming_timeout`**: Timeout in seconds for streaming responses (default: 10)
- **`responses_dir`**: Directory path for storing response database and files (default: "./responses")

#### Response Object Structure

Responses follow the OpenAI Responses API format:

```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1640995200,
  "status": "completed",
  "model": "my-agent",
  "output": [
    {
      "type": "message",
      "id": "msg_def456",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Hello! I'm doing well, thank you for asking.",
          "annotations": []
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 12,
    "output_tokens": 15,
    "total_tokens": 27
  },
  "metadata": {},
  "previous_response_id": null
}
```

#### Streaming Events

When [`stream: true`](src/xaibo/server/adapters/openai_responses.py:357) is specified, the adapter sends Server-Sent Events:

- **`response.created`**: Response object created
- **`response.in_progress`**: Response processing started
- **`response.output_item.added`**: New output item added
- **`response.content_part.added`**: Content part added to output
- **`response.output_text.delta`**: Incremental text content
- **`response.content_part.done`**: Content part completed
- **`response.output_text.done`**: Text output completed
- **`response.output_item.done`**: Output item completed
- **`response.completed`**: Response fully completed

#### Important Notes

- **Database Storage**: The adapter uses SQLite for persistent storage in the specified [`responses_dir`](src/xaibo/server/adapters/openai_responses.py:26)
- **Conversation State**: Use [`previous_response_id`](src/xaibo/server/adapters/openai_responses.py:300) to maintain conversation continuity across requests
- **Agent Mapping**: The [`model`](src/xaibo/server/adapters/openai_responses.py:290) parameter maps to registered Xaibo agent IDs
- **Entry Points**: Agents with multiple entry points can be accessed using `agent_id/entry_point` format
- **Background Responses**: Only responses created with [`background: true`](src/xaibo/server/adapters/openai_responses.py:351) can be cancelled

### MCP (Model Context Protocol) Adapter

The MCP adapter exposes Xaibo agents as MCP tools, allowing them to be used by any MCP-compatible client. This enables seamless integration with MCP-enabled applications and development environments.

#### What is the MCP Adapter?

The MCP adapter implements the [Model Context Protocol](https://modelcontextprotocol.io/) specification, which provides a standardized way for AI applications to access external tools and resources. When enabled, the MCP adapter:

- Exposes each registered Xaibo agent as an MCP tool
- Handles JSON-RPC 2.0 communication protocol
- Supports agent entry points for specialized functionality
- Provides proper error handling and response formatting
- Maintains compatibility with MCP client implementations

#### How to Use the MCP Adapter

##### Command Line Usage

Start the Xaibo server with the MCP adapter enabled:

```bash
# Start server with MCP adapter
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 127.0.0.1 \
  --port 8000

# You can also combine it with other adapters
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 127.0.0.1 \
  --port 8000
```

##### Programmatic Usage

```python
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.mcp import McpApiAdapter

# Initialize Xaibo and register your agents
xaibo = Xaibo()
xaibo.register_agent(my_agent_config)

# Create a web server with the MCP adapter
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=["xaibo.server.adapters.McpApiAdapter"]
)

# Start the server
server.start()
```

##### Using Multiple Adapters

You can run both OpenAI and MCP adapters simultaneously:

```python
from xaibo import Xaibo
from xaibo.server import XaiboWebServer

# Initialize Xaibo and register your agents
xaibo = Xaibo()
xaibo.register_agent(my_agent_config)

# Create a web server with both adapters
server = XaiboWebServer(
    xaibo=xaibo,
    adapters=[
        "xaibo.server.adapters.OpenAiApiAdapter",
        "xaibo.server.adapters.McpApiAdapter"
    ]
)

server.start()
```

#### API Endpoints

When the MCP adapter is enabled, it provides the following endpoint:

- **POST `/mcp`**: Main MCP JSON-RPC 2.0 endpoint for all protocol communication

#### MCP Protocol Methods

The adapter supports these MCP protocol methods:

- `initialize`: Establishes connection and exchanges capabilities
- `notifications/initialized`: Confirms initialization completion
- `tools/list`: Returns available Xaibo agents as MCP tools
- `tools/call`: Executes a specific agent with provided arguments

#### Tool Schema

Each Xaibo agent is exposed as an MCP tool with the following schema:

```json
{
  "name": "agent_id",
  "description": "Execute Xaibo agent 'agent_id'",
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
```

For agents with multiple entry points, tools are named as `agent_id.entry_point`.

#### Example Usage with MCP Client

Here's how you might interact with the MCP adapter using a JSON-RPC client:

```bash
# Initialize the MCP connection
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {
        "name": "my-client",
        "version": "1.0.0"
      }
    }
  }'

# List available tools (agents)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Call a specific agent
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "my-agent",
      "arguments": {
        "message": "Hello, what can you help me with?"
      }
    }
  }'
```

#### Integration with Development Environments

The MCP adapter enables Xaibo agents to be used directly within MCP-compatible development environments and AI assistants. This allows developers to:

- Access Xaibo agents as tools within their IDE
- Integrate agents into AI-powered development workflows
- Use agents for code generation, analysis, and automation tasks
- Leverage specialized agents for domain-specific operations

#### Error Handling

The MCP adapter provides comprehensive error handling with standard JSON-RPC 2.0 error codes:

- `-32700`: Parse error (malformed JSON)
- `-32600`: Invalid request (missing required fields)
- `-32601`: Method not found (unsupported MCP method)
- `-32602`: Invalid parameters (missing agent or arguments)
- `-32603`: Internal error (agent execution failure)

#### Configuration Notes

- The MCP adapter runs on the `/mcp` path prefix by default
- All responses use HTTP status 200 with JSON-RPC error handling
- Agent responses are converted to MCP content format automatically
- File attachments are represented as text descriptions in the current implementation

</details>

## Development

### Roadmap

Xaibo is actively developing:
- Enhanced visual configuration UI
- Visual tool definition with Xircuits
- More API adapters beyond OpenAI standard
- Multi-user aware agents

The core principles and APIs are stable for production use.

### Contributing

#### Running Tests
Tests are implemented using pytest. If you are using PyCharm to run them, you 
will need to configure it to also show logging output. That way some failures
will be a lot easier to debug.

Go to File > Settings > Advanced Settings > Python and check the option 
`Pytest: do not add "--no-header --no-summary -q"`.

## Get Involved

- GitHub: [github.com/xpressai/xaibo](https://github.com/xpressai/xaibo)
- Discord: https://discord.gg/uASMzSSVKe
- Contact: hello@xpress.ai
