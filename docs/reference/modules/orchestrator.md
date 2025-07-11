# Orchestrator Modules Reference

Orchestrator modules coordinate agent behavior by managing interactions between LLMs, tools, and memory systems. They implement the core agent logic and decision-making processes.

## SimpleToolOrchestrator

An orchestrator that processes user messages by leveraging an LLM to generate responses and potentially use tools. If tool execution fails, it increases the temperature (stress level) for subsequent LLM calls, simulating cognitive stress.

**Source**: [`src/xaibo/primitives/modules/orchestrator/simple_tool_orchestrator.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/simple_tool_orchestrator.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator`

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
  
  - module: xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator
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

The SimpleToolOrchestrator follows this process:

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
from xaibo.primitives.modules.orchestrator.simple_tool_orchestrator import SimpleToolOrchestrator

# Initialize with dependencies
orchestrator = SimpleToolOrchestrator(
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

## ReActOrchestrator

An orchestrator that implements the ReAct (Reasoning and Acting) pattern with explicit Thought-Action-Observation cycles. The LLM follows a structured reasoning process where it thinks about what to do next, takes actions (using tools or providing final answers), and observes the results before continuing.

### Related Documentation

- **Tutorial**: [Advanced Orchestration](../../tutorial/advanced-orchestration.md) - Learn to build sophisticated agents with ReAct patterns
- **How-to Guides**:
  - [Switch to ReAct Pattern](../../how-to/orchestrator/switch-to-react-pattern.md)
  - [Customize ReAct Prompts](../../how-to/orchestrator/customize-react-prompts.md)
  - [Debug Agent Reasoning](../../how-to/orchestrator/debug-agent-reasoning.md)
  - [Handle Complex Workflows](../../how-to/orchestrator/handle-complex-workflows.md)
- **Explanation**: [ReAct Pattern](../../explanation/concepts/react-pattern.md) - Understanding the reasoning and acting cycle

**Source**: [`src/xaibo/primitives/modules/orchestrator/react_orchestrator.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/react_orchestrator.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.ReActOrchestrator`

**Dependencies**: None

**Protocols**: Provides [`TextMessageHandlerProtocol`](https://github.com/XpressAI/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py), Uses [`LLMProtocol`](../protocols/llm.md), [`ToolProviderProtocol`](../protocols/tools.md), [`ResponseProtocol`](../protocols/response.md), [`ConversationHistoryProtocol`](https://github.com/XpressAI/xaibo/blob/main/src/xaibo/core/protocols/conversation.py)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `response` | `ResponseProtocol` | Protocol for sending responses back to the user |
| `llm` | `LLMProtocol` | Protocol for generating text using a language model |
| `tool_provider` | `ToolProviderProtocol` | Protocol for accessing and executing tools |
| `history` | `ConversationHistoryProtocol` | Conversation history for context |
| `config` | `Optional[Dict[str, Any]]` | Optional configuration dictionary |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt` | `str` | Default ReAct prompt | Base system prompt that guides ReAct pattern behavior |
| `thought_prompt` | `str` | Default thought prompt | Prompt for generating thoughts about next steps |
| `action_prompt` | `str` | Default action prompt | Prompt for taking actions (tools or final answer) |
| `observation_prompt` | `str` | Default observation prompt | Prompt for processing tool results and observations |
| `error_prompt` | `str` | Default error template | Prompt template for handling errors (use `{error}` placeholder) |
| `max_iterations_prompt` | `str` | Default max iterations template | Prompt template for max iterations (use `{max_iterations}` placeholder) |
| `max_iterations` | `int` | `10` | Maximum number of Thought-Action-Observation cycles |
| `show_reasoning` | `bool` | `True` | Whether to show intermediate reasoning steps to users |
| `reasoning_temperature` | `float` | `0.7` | Temperature setting for reasoning generation |

### Methods

#### `handle_text(text: str) -> None`

Processes a user text message using the ReAct pattern with explicit Thought-Action-Observation cycles.

**Parameters:**

- `text`: The user's input text message

**Behavior:**

1. Initializes conversation with system prompt and user message
2. Enters iterative ReAct cycle with three phases:
   - **THOUGHT**: Reasons about what to do next using `reasoning_temperature`
   - **ACTION**: Executes tools or provides final answer with lower temperature (0.3)
   - **OBSERVATION**: Processes tool results and decides next steps
3. Continues cycle until final answer is reached or `max_iterations` limit
4. Handles errors with reasoning-based recovery
5. Provides visual reasoning indicators when `show_reasoning=True`

### ReAct Phases

The orchestrator follows a structured cycle through these phases:

| Phase | Description | Visual Indicator |
|-------|-------------|------------------|
| `THOUGHT` | Generate reasoning about next steps | 🤔 **THINKING...** |
| `ACTION` | Execute tools or provide final answer | ⚡ **TAKING ACTION...** |
| `OBSERVATION` | Analyze tool results and plan next steps | 👁️ **OBSERVING RESULTS...** |
| `FINAL_ANSWER` | Provide complete answer to user | ✅ **FINAL ANSWER:** |

### Visual Reasoning Indicators

When `show_reasoning=True`, the orchestrator provides real-time feedback:

- 🤔 **THINKING...** - Generating thoughts about next steps
- 💭 **THOUGHT:** - Displays the reasoning process
- ⚡ **TAKING ACTION...** - Preparing to execute actions
- 🔧 **ACTION:** - Shows the action being taken
- 🛠️ **EXECUTING TOOL:** - Tool execution with arguments
- ✅ **TOOL SUCCESS:** - Successful tool execution results
- ❌ **TOOL ERROR:** - Tool execution failures
- 💥 **TOOL EXCEPTION:** - Tool execution exceptions
- 👁️ **OBSERVING RESULTS...** - Processing observations
- 🔍 **OBSERVATION:** - Analysis of tool results
- ⚠️ **ERROR OCCURRED:** - Error handling
- ⏰ **MAX ITERATIONS REACHED:** - Iteration limit reached

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
  
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 15
      show_reasoning: true
      reasoning_temperature: 0.8
      system_prompt: |
        You are an AI assistant that follows the ReAct pattern.
        Think step by step, use tools when needed, and provide clear reasoning.
      thought_prompt: |
        Consider the user's request carefully. What information do you need?
        What tools might help? Think through your approach step by step.
      action_prompt: |
        Based on your thoughts, take the most appropriate action:
        1. Use a tool if you need more information
        2. Provide FINAL_ANSWER if you have sufficient information

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

The ReActOrchestrator follows this structured process:

1. **Initialization**: Sets up conversation with system prompt and retrieves conversation history
2. **User Message Processing**: Adds the user's message to the conversation context
3. **Tool Discovery**: Retrieves available tools from the tool provider
4. **ReAct Cycle**: Up to `max_iterations` iterations through:

   **THOUGHT Phase:**
   - Uses `thought_prompt` to guide reasoning generation
   - Applies `reasoning_temperature` for creative thinking
   - No tools available during this phase
   - Shows 🤔 indicator if `show_reasoning=True`

   **ACTION Phase:**
   - Uses `action_prompt` to guide action selection
   - Lower temperature (0.3) for focused decision-making
   - Tools available for execution
   - Detects final answer patterns (`FINAL_ANSWER:`)
   - Shows ⚡ indicator and tool execution details

   **OBSERVATION Phase:**
   - Uses `observation_prompt` to analyze tool results
   - Applies `reasoning_temperature` for analysis
   - No tools available during this phase
   - Shows 👁️ indicator and observation details
   - Returns to THOUGHT phase for next iteration

5. **Error Handling**: Uses `error_prompt` template for reasoning-based error recovery
6. **Iteration Limits**: Uses `max_iterations_prompt` when limit is reached
7. **Response**: Sends the final assistant message back to the user

### Features

- **Explicit Reasoning**: Structured Thought-Action-Observation cycles
- **Visual Feedback**: Real-time reasoning indicators when enabled
- **Configurable Prompts**: Customizable prompts for each phase
- **Temperature Control**: Different temperatures for reasoning vs action phases
- **Error Recovery**: Reasoning-based error handling and recovery
- **Iteration Control**: Prevents infinite loops with configurable limits
- **Tool Integration**: Comprehensive tool execution with detailed feedback
- **Conversation Context**: Maintains full conversation history throughout cycles

### Tool Execution

When tools are called during the ACTION phase:

- All tool calls in a single LLM response are executed sequentially
- Tool results include success/failure status and detailed output
- Failed tool executions are handled gracefully with error messages
- Tool execution details are shown when `show_reasoning=True`
- Results are added to conversation before moving to OBSERVATION phase

### Error Handling

The orchestrator provides robust error handling:

- **Tool Errors**: Individual tool failures don't stop the reasoning process
- **Exception Handling**: Catches and processes unexpected exceptions
- **Reasoning Recovery**: Uses configured error prompts for intelligent recovery
- **Max Iterations**: Gracefully handles iteration limits with summary responses
- **Visual Feedback**: Clear error indicators when `show_reasoning=True`

### Example Usage

```python
from xaibo.primitives.modules.orchestrator.react_orchestrator import ReActOrchestrator

# Initialize with dependencies
orchestrator = ReActOrchestrator(
    response=response_handler,
    llm=llm_provider,
    tool_provider=tool_provider,
    history=conversation_history,
    config={
        'max_iterations': 12,
        'show_reasoning': True,
        'reasoning_temperature': 0.8,
        'system_prompt': 'You are a helpful ReAct assistant.'
    }
)

# Handle a user message
await orchestrator.handle_text("What's the weather like in Paris and what should I pack?")
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