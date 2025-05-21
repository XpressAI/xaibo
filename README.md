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
This sets up a recommended project structure with an example agent and starts a server with a debug UI and OpenAI-compatible API.

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
- Test case generation from real interactions

Run it with:

```bash
uv run xaibo dev
```

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