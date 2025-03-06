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
  - module: xaibo-examples.echo.Echo
    id: echo
    config:
        prefix: "You said: "
```

Or create the same agent in code:

```python
from xaibo import AgentConfig, Registry
from xaibo.core.config import ModuleConfig

config = AgentConfig(
    id="echo-agent-minimal",
    modules=[
        ModuleConfig(
            module="xaibo-examples.echo.Echo", 
            id="echo",
            config={
                "prefix": "You said: "
            }
        )
    ]
)

registry = Registry()
registry.register_agent(config)

agent = registry.get_agent("echo-agent-minimal")
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
  - module: xaibo-examples.echo.Echo
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
