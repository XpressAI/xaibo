# Orchestrator Modules Reference

Orchestrator modules coordinate agent behavior by managing interactions between LLMs, tools, and memory systems. They implement the core agent logic and decision-making processes.

## StressingToolUser

An orchestrator that processes user messages by leveraging an LLM to generate responses and potentially use tools. If tool execution fails, it increases the temperature (stress level) for subsequent LLM calls, simulating cognitive stress.

**Source**: [`src/xaibo/primitives/modules/orchestrator/stressing_tool_user.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/stressing_tool_user.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.StressingToolUser`

**Dependencies**: None

**Protocols**: Provides [`TextMessageHandlerProtocol`](https://github.com/XpressAI/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py), Uses [`LLMProtocol`](../protocols/llm.md), [`ToolProviderProtocol`](../protocols/tools.md), [`ResponseProtocol`](../protocols/response.md), [`ConversationHistoryProtocol`](https://github.com/XpressAI/xaibo/blob/main/src/xaibo/core/protocols/conversation.py)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `response` | `ResponseProtocol` | Protocol for sending responses back to the user |
| `llm` | `LLMProtocol` | Protocol for generating text using a language model |
| `tool_provider` | `ToolProviderProtocol` | Protocol for accessing and executing tools |
| `history` | `ConversationHistoryProtocol` | Conversation history for context |
| `config` | `dict` | Optional configuration dictionary |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt` | `str` | `""` | Initial system prompt for the conversation |
| `max_thoughts` | `int` | `10` | Maximum number of tool usage iterations |

### Methods

#### `handle_text(text: str) -> None`

Processes a user text message, potentially using tools to generate a response.

**Parameters:**

- `text`: The user's input text message

**Behavior:**

1. Initializes a conversation with the system prompt and user message
2. Retrieves available tools from the tool provider
3. Iteratively generates responses and executes tools as needed
4. Increases stress level (temperature) if tool execution fails
5. Sends the final response back to the user

**Stress Management:**

- Starts with temperature 0.0
- Increases temperature by 0.1 for each tool execution failure
- Higher temperature simulates cognitive stress in subsequent LLM calls

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.openai.OpenAIProvider
    id: llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.tools.python_tool_provider.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.weather, tools.calendar]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 15
      system_prompt: |
        You are a helpful assistant with access to various tools.
        Always try to use tools when they can help answer questions.
        Think step by step and explain your reasoning.

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: tools
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Behavior

The StressingToolUser follows this process:

1. **Conversation Setup**: Retrieves conversation history and adds system prompt if configured
2. **User Message Processing**: Adds the user's message to the conversation
3. **Tool Discovery**: Retrieves available tools from the tool provider
4. **Iterative Processing**: Up to `max_thoughts` iterations:

     * Generates LLM response with current stress level (temperature)
     * If tools are called and iteration limit not reached:

         - Executes all requested tools
         - Handles tool failures by increasing stress level
         - Adds tool results to conversation

     * If no tools called or max iterations reached, ends processing

5. **Response**: Sends the final assistant message back to the user

### Features

- **Stress Simulation**: Increases LLM temperature on tool failures
- **Tool Integration**: Seamlessly executes multiple tools per iteration
- **Iteration Control**: Prevents infinite loops with `max_thoughts` limit
- **Error Handling**: Gracefully handles tool execution failures
- **Conversation Context**: Maintains full conversation history

### Tool Execution

When tools are called:

- All tool calls in a single LLM response are executed
- Tool results are collected and added to the conversation
- Failed tool executions increase the stress level by 0.1
- Tool execution stops when max thoughts are reached

### Example Usage

```python
from xaibo.primitives.modules.orchestrator.stressing_tool_user import StressingToolUser

# Initialize with dependencies
orchestrator = StressingToolUser(
    response=response_handler,
    llm=llm_provider,
    tool_provider=tool_provider,
    history=conversation_history,
    config={
        'max_thoughts': 10,
        'system_prompt': 'You are a helpful assistant.'
    }
)

# Handle a user message
await orchestrator.handle_text("What's the weather like in Paris?")
```

## Custom Orchestrators

To create custom orchestrators, implement the [`TextMessageHandlerProtocol`](https://github.com/XpressAI/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py):

```python
from xaibo.core.protocols.message_handlers import TextMessageHandlerProtocol

class CustomOrchestrator(TextMessageHandlerProtocol):
    async def handle_text(self, text: str) -> None:
        # Custom orchestration logic
        pass
```