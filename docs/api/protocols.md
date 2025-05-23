# Protocol Interfaces

Xaibo's protocol-based architecture defines clear interfaces that components must implement. These protocols create boundaries between different parts of the system and enable dependency injection.

## Core Protocols

### LLMProtocol

The [`LLMProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/llm.py) defines how to interact with language models.

```python
from xaibo.core.protocols.llm import LLMProtocol

class MyLLM(LLMProtocol):
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        # Implementation here
        pass
```

**Methods:**
- `generate(messages, **kwargs)` - Generate a response from the language model
- `stream_generate(messages, **kwargs)` - Stream responses from the language model

### ToolsProtocol

The [`ToolsProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/tools.py) standardizes tool integration.

```python
from xaibo.core.protocols.tools import ToolsProtocol

class MyToolProvider(ToolsProtocol):
    def get_tools(self) -> List[Tool]:
        # Return available tools
        pass
    
    async def call_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        # Execute the tool
        pass
```

**Methods:**
- `get_tools()` - Return list of available tools
- `call_tool(tool_name, arguments)` - Execute a specific tool

### MemoryProtocol

The [`MemoryProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/memory.py) defines how agents store and retrieve information.

```python
from xaibo.core.protocols.memory import MemoryProtocol

class MyMemory(MemoryProtocol):
    async def store(self, content: str, metadata: dict = None) -> str:
        # Store content and return ID
        pass
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]:
        # Retrieve relevant memories
        pass
```

**Methods:**
- `store(content, metadata)` - Store content in memory
- `retrieve(query, limit)` - Retrieve relevant memories
- `delete(memory_id)` - Delete specific memory

### ResponseProtocol

The [`ResponseProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/response.py) specifies how agents provide responses.

```python
from xaibo.core.protocols.response import ResponseProtocol

class MyResponseHandler(ResponseProtocol):
    async def send_response(self, response: Response) -> None:
        # Send response to user
        pass
```

### ConversationProtocol

The [`ConversationProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/conversation.py) manages dialog history.

```python
from xaibo.core.protocols.conversation import ConversationProtocol

class MyConversation(ConversationProtocol):
    def add_message(self, message: Message) -> None:
        # Add message to conversation
        pass
    
    def get_messages(self) -> List[Message]:
        # Get conversation history
        pass
```

### MessageHandlersProtocol

The [`MessageHandlersProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py) defines how to process different input types.

```python
from xaibo.core.protocols.message_handlers import TextMessageHandlerProtocol

class MyMessageHandler(TextMessageHandlerProtocol):
    async def handle_text_message(self, message: str) -> Response:
        # Process text message
        pass