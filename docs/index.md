# Xaibo

Xaibo is a modular agent framework designed for building flexible AI systems with clean protocol-based interfaces.

## Introduction

Xaibo uses a protocol-driven architecture that allows components to interact through well-defined interfaces. This approach enables:

- **Modularity**: Easily swap components without changing other parts of the system
- **Extensibility**: Add new capabilities by implementing existing protocols or defining new ones  
- **Testability**: Mock dependencies for isolated testing

## Quick Start

Get started with Xaibo in just a few commands:

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

### Interacting with Your Agent

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

### Debug UI

The development server provides a debug UI that visualizes the agent's operations:

<div style="display: flex; gap: 10px; margin: 20px 0;">
  <div style="flex: 1;">
    <img src="images/sequence-diagram.png" alt="Xaibo Debug UI - Sequence Diagram Overview" width="100%">
    <p><em>Sequence Diagram Overview</em></p>
  </div>
  <div style="flex: 1;">
    <img src="images/detail-view.png" alt="Xaibo Debug UI - Detail View" width="100%">
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

#### Example Agent Configuration

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

#### Example Tool Implementation

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

## Documentation Sections

### Getting Started
- [Installation Guide](installation.md) - Detailed installation instructions and dependency management
- [Tutorial](tutorial.md) - Step-by-step guide to building your first agent
- [Examples](examples.md) - Real-world examples and use cases

### Reference
- [Configuration Reference](reference/configuration.md) - Complete configuration options
- [Protocol Reference](reference/protocols.md) - All available protocols and their interfaces
- [Module Reference](reference/modules.md) - Built-in modules and their configurations
- [API Reference](reference/api.md) - Web server and API adapter documentation

### How-To Guides
- [Creating Custom Modules](how-to/custom-modules.md) - Build your own protocol implementations
- [Setting Up Memory](how-to/memory-setup.md) - Configure vector memory and embeddings
- [Tool Integration](how-to/tool-integration.md) - Add custom tools and MCP servers
- [Deployment](how-to/deployment.md) - Production deployment strategies

### Explanation
- [Architecture Overview](explanation/architecture.md) - Deep dive into Xaibo's design principles
- [Protocol System](explanation/protocols.md) - Understanding the protocol-based architecture
- [Event System](explanation/events.md) - How the transparent proxy system works
- [Dependency Injection](explanation/dependency-injection.md) - The exchange system explained

## Installation

Install Xaibo with the dependency groups you need:

```bash
# Core package
pip install xaibo

# With specific LLM providers
pip install xaibo[openai,anthropic]

# With web server and UI
pip install xaibo[webserver]

# With local embeddings and transformers
pip install xaibo[local]

# All features
pip install xaibo[webserver,openai,anthropic,google,bedrock,local]
```

## API Compatibility

### OpenAI API

Xaibo provides full compatibility with the OpenAI Chat Completions API, allowing you to use existing OpenAI clients and tools:

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

### Model Context Protocol (MCP)

Xaibo agents can be exposed as MCP tools for integration with MCP-compatible development environments:

```bash
# Start server with MCP adapter
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.McpApiAdapter \
  --host 127.0.0.1 \
  --port 8000
```

## Development and Contributing

Xaibo is actively developing with a focus on:
- Enhanced visual configuration UI
- Visual tool definition with Xircuits
- More API adapters beyond OpenAI standard
- Multi-user aware agents

The core principles and APIs are stable for production use.

### Running Tests

Tests are implemented using pytest. For detailed test output in PyCharm:

Go to File > Settings > Advanced Settings > Python and check the option 
`Pytest: do not add "--no-header --no-summary -q"`.

## Get Involved

- **GitHub**: [https://github.com/xpressai/xaibo](https://github.com/xpressai/xaibo)
- **Discord**: [https://discord.gg/uASMzSSVKe](https://discord.gg/uASMzSSVKe)
- **Contact**: hello@xpress.ai

## Source Code

Explore the Xaibo source code on GitHub:

- [Core Framework](https://github.com/xpressai/xaibo/tree/main/src/xaibo/core) - Agent, configuration, and exchange system
- [Protocol Definitions](https://github.com/xpressai/xaibo/tree/main/src/xaibo/core/protocols) - All protocol interfaces
- [Primitive Modules](https://github.com/xpressai/xaibo/tree/main/src/xaibo/primitives/modules) - Built-in implementations
- [Server Adapters](https://github.com/xpressai/xaibo/tree/main/src/xaibo/server/adapters) - API compatibility layers
- [Examples](https://github.com/xpressai/xaibo/tree/main/examples) - Real-world usage examples