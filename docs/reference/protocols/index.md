# Protocols Overview

Xaibo's protocol system defines standardized interfaces that enable modular, testable, and extensible agent architectures. Protocols establish contracts between components without coupling them to specific implementations.

## Protocol Architecture

### Protocol Definition

Protocols in Xaibo are Python Protocol classes that define abstract interfaces:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ExampleProtocol(Protocol):
    """Protocol for example functionality"""
    
    async def example_method(self, param: str) -> str:
        """Example method documentation"""
        ...
```

### Key Features

- **Runtime Checkable**: All protocols use `@runtime_checkable` for isinstance checks
- **Async by Default**: Most protocol methods are async for non-blocking operations
- **Type Annotated**: Complete type hints for parameters and return values
- **Documentation**: Comprehensive docstrings for all methods

## Core Protocols

### Message Handler Protocols

**Source**: [`src/xaibo/core/protocols/message_handlers.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py)

| Protocol | Purpose |
|----------|---------|
| `TextMessageHandlerProtocol` | Handle text-based user input |
| `ImageMessageHandlerProtocol` | Process image messages |
| `AudioMessageHandlerProtocol` | Handle audio input |
| `VideoMessageHandlerProtocol` | Process video messages |

### Core Service Protocols

| Protocol | Purpose | Reference |
|----------|---------|-----------|
| `LLMProtocol` | Language model integration | [Specification](llm.md) |
| `ToolProviderProtocol` | Tool execution and management | [Specification](tools.md) |
| `MemoryProtocol` | Memory storage and retrieval | [Specification](memory.md) |
| `ResponseProtocol` | Response formatting and delivery | [Specification](memory.md) |
| `ConversationProtocol` | Dialog history management | [Source](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/conversation.py) |

## Protocol Implementation

### Implementing a Protocol

```python
from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMResponse

class CustomLLM:
    """Custom LLM implementation"""
    
    def __init__(self, config: dict):
        self.config = config
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        # Implementation here
        pass
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        # Streaming implementation here
        yield "response chunk"
```

### Protocol Registration

Modules can declare protocol support in two ways:

#### Explicit Declaration

```yaml
modules:
  - module: my.custom.LLM
    id: custom-llm
    provides: [LLMProtocol]
    uses: [MemoryProtocol]
```

#### Automatic Detection

Xaibo automatically detects protocols through:

1. **Inheritance**: Classes inheriting from protocol classes
2. **Provides Method**: Classes with a `provides()` class method
3. **Duck Typing**: Classes implementing protocol methods

## Protocol Composition

### Dependency Injection

Protocols enable clean dependency injection:

```python
class Orchestrator:
    def __init__(self, llm: LLMProtocol, tools: ToolProviderProtocol):
        self.llm = llm
        self.tools = tools
    
    async def process(self, message: str) -> str:
        # Use injected dependencies
        response = await self.llm.generate([{"role": "user", "content": message}])
        return response.content
```

### Exchange Configuration

The exchange system wires protocol dependencies:

```yaml
exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: openai-llm
  
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: [python-tools, mcp-tools]  # Multiple providers
```

## Protocol Validation

### Runtime Checks

```python
from xaibo.core.protocols.llm import LLMProtocol

# Validate implementation
if isinstance(my_llm, LLMProtocol):
    # Safe to use as LLM
    response = await my_llm.generate(messages)
```

### Type Checking

Protocols work with static type checkers:

```python
def use_llm(llm: LLMProtocol) -> None:
    # Type checker validates protocol compliance
    pass
```

## Testing with Protocols

### Mock Implementations

```python
class MockLLM:
    def __init__(self, responses: List[str]):
        self.responses = responses
        self.call_count = 0
    
    async def generate(self, messages, options=None):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return LLMResponse(content=response)
    
    async def generate_stream(self, messages, options=None):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        for char in response:
            yield char

# Use in tests
mock_llm = MockLLM(["Test response"])
assert isinstance(mock_llm, LLMProtocol)  # True
```

## Protocol Extension

### Custom Protocols

Define domain-specific protocols:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DatabaseProtocol(Protocol):
    """Protocol for database operations"""
    
    async def query(self, sql: str) -> List[dict]:
        """Execute SQL query"""
        ...
    
    async def insert(self, table: str, data: dict) -> str:
        """Insert data and return ID"""
        ...
```

### Protocol Inheritance

Extend existing protocols:

```python
@runtime_checkable
class AdvancedLLMProtocol(LLMProtocol):
    """Extended LLM protocol with additional capabilities"""
    
    async def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment score"""
        ...
    
    async def summarize(self, text: str, max_length: int) -> str:
        """Generate summary"""
        ...
```

## Best Practices

### Protocol Design

1. **Single Responsibility**: Each protocol should have a focused purpose
2. **Async Methods**: Use async for I/O operations
3. **Type Annotations**: Provide complete type hints
4. **Documentation**: Include comprehensive docstrings
5. **Error Handling**: Define expected exceptions

### Implementation Guidelines

1. **Protocol Compliance**: Implement all required methods
2. **Error Propagation**: Let protocol-defined exceptions bubble up
3. **Resource Management**: Use async context managers when appropriate
4. **Configuration**: Accept configuration through constructor
5. **Testing**: Provide mock implementations for testing

### Exchange Configuration

1. **Explicit Wiring**: Use explicit exchange configs for complex dependencies
2. **List Dependencies**: Use lists for multiple providers of same protocol
3. **Entry Points**: Configure entry points for message handling
4. **Validation**: Ensure all dependencies are satisfied

## Common Patterns

### Decorator Pattern

```python
class LoggingLLM:
    """Add logging to any LLM implementation"""
    
    def __init__(self, llm: LLMProtocol, logger):
        self.llm = llm
        self.logger = logger
    
    async def generate(self, messages, options=None):
        self.logger.info(f"Generating response for {len(messages)} messages")
        response = await self.llm.generate(messages, options)
        self.logger.info(f"Generated {len(response.content)} characters")
        return response
```

### Composite Pattern

```python
class CompositeTool:
    """Combine multiple tool providers"""
    
    def __init__(self, providers: List[ToolProviderProtocol]):
        self.providers = providers
    
    async def list_tools(self):
        all_tools = []
        for provider in self.providers:
            tools = await provider.list_tools()
            all_tools.extend(tools)
        return all_tools