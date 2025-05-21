# Xaibo

Xaibo is a modular agent framework designed for building flexible AI systems with clean protocol-based interfaces.

## Overview

Xaibo uses a protocol-driven architecture that allows components to interact through well-defined interfaces. This approach enables:

- **Modularity**: Easily swap components without changing other parts of the system
- **Extensibility**: Add new capabilities by implementing existing protocols or defining new ones  
- **Testability**: Mock dependencies for isolated testing

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
This sets up a recommended project structure with an example agent and starts a server with a debug UI and OpenAI-compatible API. See the [Dependency Groups](#dependency-groups) section for information about installing required dependencies.

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
      model: gpt-3.5-turbo
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

## Development Server

The built-in development server provides:
- OpenAI-compatible API endpoints
- Debug UI showing full agent operations
- Hot-reloading of agent configurations

Run it with:

```bash
uv run xaibo dev
```

## Core Protocols

Xaibo's protocol-based architecture is built around a set of core protocols that define the interfaces for different components:

### LLM Protocol

The `LLMProtocol` in `llm.py` defines how to interact with language models:
- `generate()`: Produces a complete response from the LLM given a list of messages
- `generate_stream()`: Returns an async iterator for streaming responses

### Tools Protocol

The `ToolProviderProtocol` in `tools.py` standardizes tool integration:
- `list_tools()`: Returns available tools with their descriptions and parameters
- `execute_tool()`: Runs a specific tool with provided parameters and returns results

### Memory Protocol

Memory-related protocols in `memory.py` define how agents store and retrieve information:
- `MemoryProtocol`: Core interface for storing, retrieving, and searching memories
- `ChunkingProtocol`: Splits text into appropriate chunks for embedding
- `EmbeddingProtocol`: Converts text, images, or audio into vector embeddings
- `VectorIndexProtocol`: Indexes and searches vector embeddings

### Response Protocol

The `ResponseProtocol` in `response.py` defines how agents provide responses:
- `respond_text()`: Sends text responses
- `respond_image()`, `respond_audio()`, `respond_file()`: Handles different media types
- `respond()`: Sends complex responses with multiple components
- `get_response()`: Retrieves the current response object

### Conversation Protocol

The `ConversationHistoryProtocol` in `conversation.py` manages dialog history:
- `get_history()`: Retrieves the current conversation history
- `add_message()`: Adds a new message to the history
- `clear_history()`: Resets the conversation

### Message Handlers Protocol

Message handler protocols in `message_handlers.py` define how to process different input types:
- `TextMessageHandlerProtocol`: Processes text inputs
- `ImageMessageHandlerProtocol`: Handles image data
- `AudioMessageHandlerProtocol`: Processes audio inputs
- `VideoMessageHandlerProtocol`: Handles video data

These protocols create a flexible, modular system where components can be swapped as long as they implement the required interface.

## Dependency Groups

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

## Exchange Configuration

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
      model: gpt-3.5-turbo
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

The test resources provide several examples of exchange configurations:

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

By understanding and configuring exchanges, you can create flexible and modular agent architectures in Xaibo.

## Protocol Implementations

Xaibo provides several implementations for each protocol to support different use cases:

### LLM Implementations

- `xaibo.primitives.modules.llm.OpenAILLM`: Integrates with OpenAI's models (GPT-3.5, GPT-4, etc.)
  - **Python Dependencies**: `openai` dependency group
  - **Constructor Dependencies**: None
  - **Config options**:
    - `model`: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
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

These implementations can be mixed and matched to create agents with different capabilities, and you can create your own implementations by following the protocol interfaces.

## Web Server and API Adapters

Xaibo includes built-in adapters for easy integration with existing tools. 
But you can also create your own API Adapters. Below you can see how a fully custom API
setup could look like.

### OpenAI API Compatibility

Use Xaibo with any client that supports the OpenAI Chat Completions API:
```
python
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

## Roadmap

Xaibo is actively developing:
- Enhanced visual configuration UI
- Visual tool definition with Circuits
- More API adapters beyond OpenAI standard
- Multi-user aware agents

The core principles and APIs are stable for production use.

## Contributing

### Running Tests
Tests are implemented using pytest. If you are using PyCharm to run them, you 
will need to configure it to also show logging output. That way some failures
will be a lot easier to debug.

Go to File > Settings > Advanced Settings > Python and check the option 
`Pytest: do not add "--no-header --no-summary -q"`.

## Get Involved

- GitHub: [github.com/xpressai/xaibo](https://github.com/xpressai/xaibo)
- Discord: https://discord.gg/uASMzSSVKe
- Contact: hello@xpress.ai
