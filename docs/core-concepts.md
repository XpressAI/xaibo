# Core Concepts

Xaibo is built around several key architectural concepts that provide its flexibility and power. Understanding these concepts is essential for building effective AI agents with the framework.

## Overview

Xaibo's architecture is based on three fundamental concepts:

1. **[Protocols](#protocols)**: Define interfaces that components must implement
2. **[Modules](#modules)**: Building blocks that implement protocols and provide functionality
3. **[Exchanges](#exchanges)**: Connections between modules that define dependency resolution

This design enables clean separation of concerns, easy testing, and flexible composition of AI systems.

---

## Protocols

Protocols define interfaces that components must implement, creating clear boundaries between different parts of the system. They specify what methods a component must provide without dictating how those methods are implemented.

### Core Protocols

Xaibo includes several built-in protocols that cover the essential aspects of AI agent functionality:

#### LLM Protocol
Defines how to interact with language models, regardless of the provider (OpenAI, Anthropic, Google, etc.).

```python
# Example: Any LLM implementation must provide these methods
class LLMProtocol:
    async def generate_response(self, messages: List[Message]) -> LLMResponse:
        """Generate a response from the language model"""
        pass
    
    def supports_streaming(self) -> bool:
        """Whether the LLM supports streaming responses"""
        pass
```

#### Tools Protocol
Standardizes tool integration, allowing agents to use various types of tools consistently.

```python
class ToolsProtocol:
    async def get_available_tools(self) -> List[Tool]:
        """Get list of available tools"""
        pass
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        """Execute a specific tool with given arguments"""
        pass
```

#### Memory Protocol
Defines how agents store and retrieve information, supporting various memory backends.

```python
class MemoryProtocol:
    async def store(self, content: str, metadata: dict = None) -> str:
        """Store content and return a reference ID"""
        pass
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Retrieve relevant content based on query"""
        pass
```

#### Response Protocol
Specifies how agents provide responses back to users or other systems.

```python
class ResponseProtocol:
    async def send_response(self, content: str, metadata: dict = None):
        """Send a response to the user"""
        pass
```

#### Conversation Protocol
Manages dialog history and conversation state.

```python
class ConversationProtocol:
    async def add_message(self, message: Message):
        """Add a message to the conversation history"""
        pass
    
    async def get_history(self, limit: int = None) -> List[Message]:
        """Get conversation history"""
        pass
```

#### Message Handlers Protocol
Defines how to process different input types (text, images, files, etc.).

```python
class TextMessageHandlerProtocol:
    async def handle_text_message(self, message: str) -> Response:
        """Handle incoming text messages"""
        pass
```

### Benefits of Protocol-Based Design

!!! success "Advantages"
    - **Modularity**: Swap implementations without changing dependent code
    - **Testability**: Mock any component by implementing the same protocol
    - **Flexibility**: Mix and match components as long as they fulfill required protocols
    - **Clear Contracts**: Explicit interfaces make system behavior predictable

---

## Modules

Modules are the building blocks of Xaibo agents. Each module implements one or more protocols and can depend on other modules through their protocols.

### Module Categories

#### LLM Modules
Provide language model capabilities from various providers:

- **[`OpenAILLM`](getting-started.md#step-3-understand-the-example-agent)**: OpenAI GPT models (GPT-4, GPT-3.5-turbo)
- **`AnthropicLLM`**: Anthropic Claude models
- **`GoogleLLM`**: Google Gemini models
- **`BedrockLLM`**: AWS Bedrock models
- **`MockLLM`**: Test responses for development

#### Memory Modules
Handle information storage and retrieval:

- **`VectorMemory`**: Vector-based semantic memory
- **`NumpyVectorIndex`**: Simple vector storage using NumPy
- **`TokenChunker`**: Text chunking based on token counts
- **`SentenceTransformerEmbedder`**: Local embeddings using Sentence Transformers
- **`OpenAIEmbedder`**: OpenAI embedding models

#### Tool Modules
Integrate external tools and capabilities:

- **`PythonToolProvider`**: Convert Python functions to tools
- **`MCPToolProvider`**: Connect to MCP (Model Context Protocol) servers
- **`ToolCollector`**: Aggregate tools from multiple providers

#### Orchestrator Modules
Manage agent behavior and decision-making:

- **`StressingToolUser`**: Advanced tool-using orchestrator with reasoning capabilities

### Module Configuration

Modules are configured in YAML files with three main sections:

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM  # Module class path
    id: llm                                          # Unique identifier
    config:                                          # Module-specific configuration
      model: gpt-4
      temperature: 0.7
      max_tokens: 1000
```

#### Configuration Parameters

- **`module`**: Full Python path to the module class
- **`id`**: Unique identifier used for dependency resolution
- **`config`**: Dictionary of module-specific configuration options

### Module Dependencies

Modules can declare dependencies on protocols, which are resolved through the exchange system:

```python
class MyOrchestrator:
    def __init__(self, llm: LLMProtocol, tools: ToolsProtocol):
        self.llm = llm
        self.tools = tools
```

This orchestrator requires modules that implement the `LLMProtocol` and `ToolsProtocol`.

---

## Exchanges

Exchanges are the connections between modules that define how dependencies are resolved. They create a flexible wiring system that enables dependency injection.

### What are Exchanges?

Exchanges specify which module provides an implementation for a protocol that another module requires. This allows:

- Modules to declare what they need without knowing specific implementations
- Easy swapping of implementations without changing dependent modules
- Clear separation of concerns through protocol-based interfaces
- Support for both singleton and list-type dependencies

### Exchange Configuration Structure

An exchange configuration consists of:

- **`module`**: ID of the module that requires a dependency
- **`protocol`**: Protocol interface that defines the dependency
- **`provider`**: ID of the module that provides the implementation
- **`field_name`**: Optional parameter name (useful for multiple dependencies of same type)

### Explicit vs. Implicit Configuration

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

Xaibo can automatically infer exchanges when there's an unambiguous match:

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
      max_thoughts: 10
# No explicit exchange needed - Xaibo infers the connections
```

### Special Exchange Identifiers

- **`__entry__`**: Entry point for handling incoming messages
- **`__response__`**: Default response handler for outgoing messages

### List Dependencies

Modules can depend on multiple implementations of the same protocol:

```yaml
exchange:
  - module: tool_collector
    protocol: ToolsProtocol
    provider: [python_tools, mcp_tools, custom_tools]
```

This is useful for modules that aggregate functionality from multiple sources.

---

## Putting It All Together

Here's how protocols, modules, and exchanges work together in a complete agent:

```yaml title="Complete Agent Example"
id: advanced-agent
description: An agent with memory, tools, and multiple LLMs

modules:
  # LLM for general tasks
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: main_llm
    config:
      model: gpt-4
  
  # Specialized LLM for code tasks
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: code_llm
    config:
      model: claude-3-sonnet-20240229
  
  # Memory system
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: ./agent_memory.pkl
  
  # Tool provider
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.general, tools.code]
  
  # Orchestrator that uses everything
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 15
      system_prompt: |
        You are an advanced AI assistant with access to memory and tools.

exchange:
  # Entry point
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
  
  # Connect orchestrator to main LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: main_llm
  
  # Connect orchestrator to memory
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  
  # Connect orchestrator to tools
  - module: orchestrator
    protocol: ToolsProtocol
    provider: tools
```

### Flow of Execution

1. **Message Arrives**: Routed to the module connected to `__entry__`
2. **Orchestrator Processes**: Uses injected LLM, memory, and tools
3. **Dependencies Resolved**: Exchange configuration determines which implementations to use
4. **Response Generated**: Sent back through the response protocol

---

## Best Practices

### Protocol Design

!!! tip "Protocol Guidelines"
    - Keep protocols focused on a single responsibility
    - Use async methods for I/O operations
    - Include proper type hints for better development experience
    - Document expected behavior clearly

### Module Development

!!! tip "Module Guidelines"
    - Implement protocols completely and correctly
    - Handle errors gracefully with proper exception types
    - Use dependency injection rather than hard-coded dependencies
    - Include comprehensive configuration validation

### Exchange Configuration

!!! tip "Exchange Guidelines"
    - Use explicit exchanges for complex dependency graphs
    - Leverage implicit exchanges for simple, unambiguous cases
    - Group related modules logically
    - Document non-obvious dependency relationships

---

## Next Steps

Now that you understand Xaibo's core concepts:

- **[Features](features.md)**: Explore advanced capabilities like transparent proxies and event systems
- **[Project Structure](project-structure.md)**: Learn how to organize larger Xaibo projects
- **[Getting Started](getting-started.md)**: Review the practical tutorial if you haven't already

Understanding these core concepts will help you build more sophisticated and maintainable AI agents with Xaibo.