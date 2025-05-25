# Agent Configuration Reference

Agent configurations define the structure and behavior of Xaibo agents through YAML files. This reference provides complete specifications for all configuration options.

## AgentConfig

The root configuration object for defining an agent.

**Source**: [`src/xaibo/core/config.py:56`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L56)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier for the agent |
| `description` | `str` | No | Human-readable description of the agent's purpose |
| `modules` | `List[ModuleConfig]` | Yes | List of module configurations that comprise the agent |
| `exchange` | `List[ExchangeConfig]` | No | Explicit dependency wiring between modules |

### Methods

---

#### `load_directory(directory: str) -> Dict[str, AgentConfig]`

Load all agent configurations from a directory recursively.

**Parameters:**

- `directory` (str, required): Path to directory containing YAML agent configurations

**Returns:**

- `Dict[str, AgentConfig]`: Dictionary mapping file paths to AgentConfig instances

**Raises:**

- `ValueError`: If any YAML files cannot be parsed as valid agent configs

---

#### `from_yaml(yaml_str: str) -> AgentConfig`

Load an AgentConfig from a YAML string.

**Parameters:**

- `yaml_str` (str, required): YAML string containing agent configuration

**Returns:**

- `AgentConfig`: Parsed agent configuration

---

#### `to_yaml() -> str`

Convert this AgentConfig to YAML string format.

**Returns:**

- `str`: YAML string representation of this config

---

## ModuleConfig

Configuration for individual modules within an agent.

**Source**: [`src/xaibo/core/config.py:11`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L11)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `module` | `Union[str, Type]` | Yes | Python import path to the module class |
| `id` | `str` | Yes | Unique identifier for this module instance |
| `scope` | `Scope` | No | Module scope (default: `Scope.Instance`) |
| `provides` | `List[Union[str, Type]]` | No | List of protocols this module provides |
| `uses` | `List[Union[str, Type]]` | No | List of protocols this module requires |
| `config` | `Dict` | No | Module-specific configuration parameters |

### Scope Enumeration

**Source**: [`src/xaibo/core/config.py:7`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L7)

| Value | Description |
|-------|-------------|
| `Scope.Instance` | Module instance is created per agent |
| `Scope.Agent` | Module instance is shared across agent instances |

### Example

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    scope: instance
    provides: [LLMProtocol]
    config:
      model: gpt-4
      temperature: 0.7
      max_tokens: 2048
```

## ExchangeConfig

Configuration for dependency injection between modules.

**Source**: [`src/xaibo/core/config.py:36`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L36)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `module` | `str` | No* | ID of the module that requires the dependency |
| `field_name` | `str` | No | Parameter name in the module's constructor |
| `protocol` | `Union[str, Type]` | Yes | Protocol interface that defines the dependency |
| `provider` | `Union[str, List[str]]` | Yes | Module ID(s) that provide the implementation |

*Required except when used with ConfigOverrides

### Special Module IDs

| Module ID | Description |
|-----------|-------------|
| `__entry__` | Entry point for handling incoming messages |
| `__response__` | Response handler for outgoing messages |

### Example

```yaml
exchange:
  # Connect orchestrator to LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  
  # Set entry point for text messages
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
  
  # Multiple providers for a single protocol
  - module: tool_collector
    protocol: ToolProviderProtocol
    provider: [python-tools, mcp-tools]
```

## ConfigOverrides

Runtime configuration overrides for testing and dynamic configuration.

**Source**: [`src/xaibo/core/config.py:51`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L51)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instances` | `Dict[str, object]` | No | Pre-instantiated objects to inject by module ID |
| `exchange` | `List[ExchangeConfig]` | No | Additional exchange configurations |

### Example

```python
from xaibo.core.config import ConfigOverrides, ExchangeConfig

# Override with mock LLM for testing
overrides = ConfigOverrides(
    instances={
        "llm": MockLLM(responses=["Test response"])
    },
    exchange=[
        ExchangeConfig(
            protocol="LLMProtocol",
            provider="llm"
        )
    ]
)
```

## Implicit Configuration

Xaibo automatically infers configuration when unambiguous:

### Automatic Response Module

If no module provides `ResponseProtocol`, Xaibo adds:

```yaml
modules:
  - module: xaibo.primitives.modules.ResponseHandler
    id: __response__
    provides: [ResponseProtocol]
```

### Automatic Exchange Configuration

When exactly one module provides a protocol that another module requires, Xaibo creates the exchange automatically.

### Automatic Entry Points

When exactly one module provides a message handler protocol, Xaibo sets it as the entry point for that message type.

## Complete Example

```yaml
id: example-agent
description: An example agent with LLM and tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      temperature: 0.7
      max_tokens: 2048
      timeout: 60.0
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]
  
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp-tools
    config:
      timeout: 30.0
      servers:
        - name: filesystem
          transport: stdio
          command: ["python", "-m", "mcp_server_filesystem"]
          args: ["--root", "/workspace"]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to tools.

exchange:
  # Explicit wiring
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: [python-tools, mcp-tools]
  
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

## Validation Rules

1. **Unique Module IDs**: All module IDs within an agent must be unique
2. **Valid Module Paths**: Module paths must reference importable Python classes
3. **Protocol Consistency**: Protocols referenced in exchange must be provided by some module
4. **Dependency Resolution**: All required dependencies must have providers
5. **Entry Point Requirements**: At least one entry point must be configured for message handling