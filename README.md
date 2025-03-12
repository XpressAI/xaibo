# Xaibo

Xaibo is a modular agent framework designed for building flexible AI systems with clean protocol-based interfaces.

## Overview

Xaibo uses a protocol-driven architecture that allows components to interact through well-defined interfaces. This approach enables:

- **Modularity**: Easily swap components without changing other parts of the system
- **Extensibility**: Add new capabilities by implementing existing protocols or defining new ones  
- **Testability**: Mock dependencies for isolated testing

## Quick Start

Create a simple echo agent in YAML:

```yaml
id: echo-agent-minimal
modules:
  - module: xaibo_examples.echo.Echo
    id: echo
    config:
        prefix: "You said: "
```

Or create the same agent in code:

```python
from xaibo import AgentConfig, Xaibo
from xaibo.core import ModuleConfig
from xaibo_examples.echo import Echo

config = AgentConfig(
    id="echo-agent-minimal",
    modules=[
        ModuleConfig(
            module=Echo,
            id="echo",
            config={
                "prefix": "You said: "
            }
        )
    ]
)

xaibo = Xaibo()
xaibo.register_agent(config)

agent = xaibo.get_agent("echo-agent-minimal")
response = await agent.handle_text("Hello world")
# response.text == "You said: Hello world"
```

## Key Features

- **Protocol-Based Architecture**: Components interact through well-defined protocol interfaces
- **Flexible Configuration**: Configure agents using YAML or code-first approach
- **Event System**: Built-in event system for monitoring and debugging agent behavior
- **Dependency Injection**: Easily mock dependencies for testing or swap implementations
- **Minimal Boilerplate**: Sensible defaults with automatic wiring of components

## Advanced Usage

For more complex agents, you can explicitly define protocols and wire up components:

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
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: echo
  - module: echo
    protocol: ResponseProtocol
    provider: __response__
```

## Web Server and API Adapters

Xaibo includes a built-in web server with API adapters for easy integration with existing tools and frameworks.

### Running the Server from CLI

Xaibo provides a convenient command-line interface to start the web server:

    # Start the server with default settings
    python -m xaibo.server.web
    
    # Specify port and host
    python -m xaibo.server.web --port 3000 --host 127.0.0.1
    
    # Load agents from a directory
    python -m xaibo.server.web --agent-dir ./my_agents
    
    # Enable specific adapters (e.g. openai api compatibility, see below)
    python -m xaibo.server.web --adapter xaibo.server.adapters.OpenAiApiAdapter
    
    # Get help with all available options
    python -m xaibo.server --help

The CLI automatically loads agent configurations from YAML files in the specified directory, making it easy to deploy your agents as a service without writing any code.


### OpenAI API Compatibility

The OpenAI API adapter allows you to use Xaibo agents with any client that supports the OpenAI Chat Completions API:

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

Once running, you can connect to your Xaibo agents using any OpenAI-compatible client by pointing it to your server's endpoint. The adapter exposes standard OpenAI API endpoints:

- `GET /openai/models` - Lists all registered agents as available models
- `POST /openai/chat/completions` - Handles chat completion requests

This makes it easy to integrate Xaibo with existing tools and UIs that support the OpenAI API.


# Contributing

## Running Tests
Tests are implemented using pytest. If you are using PyCharm to run them, you 
will need to configure it to also show logging output. That way some failures
will be a lot easier to debug.

Go to File > Settings > Advanced Settings > Python and check the option 
`Pytest: do not add "--no-header --no-summary -q"`.