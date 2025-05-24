# Orchestrator Modules Reference

Orchestrator modules coordinate agent behavior by managing interactions between LLMs, tools, and memory systems. They implement the core agent logic and decision-making processes.

## StressingToolUser

An orchestrator that actively uses available tools to accomplish tasks through iterative reasoning.

**Source**: [`src/xaibo/primitives/modules/orchestrator/stressing_tool_user.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/stressing_tool_user.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.StressingToolUser`

**Dependencies**: None

**Protocols**: Provides `TextMessageHandlerProtocol`, Uses [`LLMProtocol`](../protocols/llm.md), [`ToolProviderProtocol`](../protocols/tools.md), [`ResponseProtocol`](../protocols/response.md)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | Language model for reasoning and responses |
| `tools` | `ToolProviderProtocol` | Tool provider for executing actions |
| `response` | `ResponseProtocol` | Response handler for sending outputs |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_thoughts` | `int` | `10` | Maximum number of reasoning iterations |
| `system_prompt` | `str` | Default prompt | System prompt for the LLM |
| `tool_use_prompt` | `str` | Default prompt | Prompt encouraging tool usage |
| `thinking_prompt` | `str` | Default prompt | Prompt for reasoning steps |
| `response_prompt` | `str` | Default prompt | Prompt for final responses |
| `max_tool_calls_per_iteration` | `int` | `5` | Maximum tool calls per reasoning step |
| `temperature` | `float` | `0.7` | LLM temperature for reasoning |
| `max_tokens` | `int` | `2048` | Maximum tokens per LLM call |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.weather, tools.calendar]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 15
      temperature: 0.8
      max_tokens: 4096
      system_prompt: |
        You are a helpful assistant with access to various tools.
        Always try to use tools when they can help answer questions.
        Think step by step and explain your reasoning.
      tool_use_prompt: |
        You have access to tools. Use them whenever they can help.
        Available tools will be provided in the function definitions.
      thinking_prompt: |
        Think about what you need to do next. Consider:
        1. What information do you need?
        2. What tools might help?
        3. What's the best approach?
      response_prompt: |
        Provide a helpful and complete response based on your analysis.

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

1. **Initial Analysis**: Analyzes the user's request
2. **Tool Discovery**: Identifies available tools
3. **Iterative Reasoning**: Performs reasoning loops:
   - Thinks about what to do next
   - Calls relevant tools
   - Analyzes tool results
   - Decides whether to continue or respond
4. **Final Response**: Provides a comprehensive answer

### Features

- **Tool-First Approach**: Actively seeks to use tools
- **Iterative Reasoning**: Multiple reasoning steps
- **Adaptive Behavior**: Adjusts strategy based on available tools
- **Error Recovery**: Handles tool failures gracefully
- **Thought Limiting**: Prevents infinite reasoning loops

### Example Interaction

```
User: "What's the weather like in Paris and what time is it there?"

Orchestrator reasoning:
1. Identifies need for weather and time information
2. Discovers get_weather and get_time tools
3. Calls get_weather("Paris")
4. Calls get_time("Paris")
5. Synthesizes results into coherent response

Response: "In Paris, it's currently 22°C and partly cloudy. The local time is 3:45 PM."
```

## ConversationOrchestrator

Manages multi-turn conversations with memory and context awareness.

**Source**: [`src/xaibo/primitives/modules/orchestrator/conversation_orchestrator.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/conversation_orchestrator.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.ConversationOrchestrator`

**Dependencies**: None

**Protocols**: Provides `TextMessageHandlerProtocol`, Uses [`LLMProtocol`](../protocols/llm.md), [`MemoryProtocol`](../protocols/memory.md), [`ResponseProtocol`](../protocols/response.md)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | Language model for responses |
| `memory` | `MemoryProtocol` | Memory system for conversation history |
| `response` | `ResponseProtocol` | Response handler |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt` | `str` | Default prompt | System prompt for conversations |
| `max_context_length` | `int` | `4000` | Maximum tokens in conversation context |
| `memory_search_k` | `int` | `5` | Number of relevant memories to retrieve |
| `memory_threshold` | `float` | `0.7` | Minimum similarity for memory inclusion |
| `conversation_summary_interval` | `int` | `10` | Messages between conversation summaries |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
  
  - module: xaibo.primitives.modules.orchestrator.ConversationOrchestrator
    id: orchestrator
    config:
      max_context_length: 8000
      memory_search_k: 10
      memory_threshold: 0.6
      conversation_summary_interval: 15
      system_prompt: |
        You are a knowledgeable assistant that remembers previous conversations.
        Use your memory to provide contextual and personalized responses.

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Features

- **Conversation Memory**: Stores and retrieves conversation history
- **Context Management**: Maintains optimal context length
- **Relevant Recall**: Retrieves relevant past conversations
- **Summarization**: Automatically summarizes long conversations
- **Personalization**: Adapts responses based on user history

## PlanningOrchestrator

Implements goal-oriented planning and execution.

**Source**: [`src/xaibo/primitives/modules/orchestrator/planning_orchestrator.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/planning_orchestrator.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.PlanningOrchestrator`

**Dependencies**: None

**Protocols**: Provides `TextMessageHandlerProtocol`, Uses [`LLMProtocol`](../protocols/llm.md), [`ToolProviderProtocol`](../protocols/tools.md), [`MemoryProtocol`](../protocols/memory.md), [`ResponseProtocol`](../protocols/response.md)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | Language model for planning and execution |
| `tools` | `ToolProviderProtocol` | Available tools for plan execution |
| `memory` | `MemoryProtocol` | Memory for storing plans and results |
| `response` | `ResponseProtocol` | Response handler |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_planning_steps` | `int` | `20` | Maximum steps in a plan |
| `max_execution_attempts` | `int` | `3` | Maximum attempts per step |
| `planning_temperature` | `float` | `0.3` | Temperature for planning |
| `execution_temperature` | `float` | `0.1` | Temperature for execution |
| `replanning_threshold` | `float` | `0.5` | When to trigger replanning |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.project_management, tools.communication]
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
  
  - module: xaibo.primitives.modules.orchestrator.PlanningOrchestrator
    id: orchestrator
    config:
      max_planning_steps: 25
      max_execution_attempts: 5
      planning_temperature: 0.2
      execution_temperature: 0.0

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: tools
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Planning Process

1. **Goal Analysis**: Breaks down complex goals into sub-goals
2. **Plan Generation**: Creates step-by-step execution plan
3. **Resource Assessment**: Identifies required tools and information
4. **Execution**: Executes plan steps sequentially
5. **Monitoring**: Tracks progress and success metrics
6. **Adaptation**: Replans when steps fail or conditions change

### Features

- **Hierarchical Planning**: Supports nested goals and sub-plans
- **Dynamic Replanning**: Adapts plans based on execution results
- **Resource Management**: Tracks tool usage and availability
- **Progress Tracking**: Monitors plan execution progress
- **Failure Recovery**: Handles step failures with replanning

## ReflectiveOrchestrator

Implements self-reflection and continuous improvement.

**Source**: [`src/xaibo/primitives/modules/orchestrator/reflective_orchestrator.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/orchestrator/reflective_orchestrator.py)

**Module Path**: `xaibo.primitives.modules.orchestrator.ReflectiveOrchestrator`

**Dependencies**: None

**Protocols**: Provides `TextMessageHandlerProtocol`, Uses [`LLMProtocol`](../protocols/llm.md), [`ToolProviderProtocol`](../protocols/tools.md), [`MemoryProtocol`](../protocols/memory.md), [`ResponseProtocol`](../protocols/response.md)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | Language model for reasoning and reflection |
| `tools` | `ToolProviderProtocol` | Available tools |
| `memory` | `MemoryProtocol` | Memory for storing reflections |
| `response` | `ResponseProtocol` | Response handler |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reflection_interval` | `int` | `5` | Messages between reflection cycles |
| `max_reflection_depth` | `int` | `3` | Maximum levels of self-reflection |
| `improvement_threshold` | `float` | `0.8` | Threshold for considering improvements |
| `reflection_temperature` | `float` | `0.5` | Temperature for reflection |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.analysis, tools.evaluation]
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
  
  - module: xaibo.primitives.modules.orchestrator.ReflectiveOrchestrator
    id: orchestrator
    config:
      reflection_interval: 3
      max_reflection_depth: 5
      improvement_threshold: 0.7
      reflection_temperature: 0.4

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: tools
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Reflection Process

1. **Performance Analysis**: Evaluates recent interactions
2. **Pattern Recognition**: Identifies recurring issues or successes
3. **Strategy Assessment**: Reviews current approaches
4. **Improvement Identification**: Finds areas for enhancement
5. **Strategy Adaptation**: Modifies behavior based on insights
6. **Meta-Reflection**: Reflects on the reflection process itself

### Features

- **Self-Evaluation**: Continuously assesses own performance
- **Pattern Learning**: Learns from interaction patterns
- **Strategy Evolution**: Adapts strategies over time
- **Meta-Cognition**: Reflects on thinking processes
- **Continuous Improvement**: Implements learned improvements

## Common Configuration Patterns

### Basic Tool-Using Agent

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.basic]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: "You are a helpful assistant with access to tools."

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

### Conversational Agent with Memory

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
  
  - module: xaibo.primitives.modules.orchestrator.ConversationOrchestrator
    id: orchestrator
    config:
      max_context_length: 6000
      memory_search_k: 8

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Advanced Planning Agent

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python_tools
    config:
      tool_packages: [tools.project, tools.communication]
  
  - module: xaibo.primitives.modules.tools.MCPToolProvider
    id: mcp_tools
    config:
      servers:
        - name: calendar
          transport: stdio
          command: ["python", "-m", "mcp_server_calendar"]
  
  - module: xaibo.primitives.modules.tools.ToolCollector
    id: tools
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
  
  - module: xaibo.primitives.modules.orchestrator.PlanningOrchestrator
    id: orchestrator
    config:
      max_planning_steps: 30
      planning_temperature: 0.2

exchange:
  - module: tools
    protocol: ToolProviderProtocol
    provider: [python_tools, mcp_tools]
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: tools
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Self-Improving Agent

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.analysis, tools.metrics]
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
  
  - module: xaibo.primitives.modules.orchestrator.ReflectiveOrchestrator
    id: orchestrator
    config:
      reflection_interval: 5
      max_reflection_depth: 4
      improvement_threshold: 0.75

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: tools
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

## Performance Considerations

### Reasoning Efficiency

1. **Thought Limits**: Set appropriate max_thoughts to prevent infinite loops
2. **Temperature Tuning**: Use lower temperatures for focused reasoning
3. **Context Management**: Monitor token usage in reasoning chains
4. **Early Termination**: Implement conditions for early reasoning termination

### Memory Usage

1. **Context Pruning**: Regularly prune conversation context
2. **Memory Cleanup**: Clean up old or irrelevant memories
3. **Batch Operations**: Process multiple operations together
4. **Lazy Loading**: Load memories and tools on demand

### Tool Integration

1. **Tool Caching**: Cache tool results when appropriate
2. **Parallel Execution**: Execute independent tools in parallel
3. **Error Handling**: Implement robust error handling for tools
4. **Resource Limits**: Set limits on tool execution time and resources

## Monitoring and Debugging

### Reasoning Traces

```python
# Enable detailed reasoning traces
orchestrator_config = {
    "debug_mode": True,
    "trace_reasoning": True,
    "log_tool_calls": True
}
```

### Performance Metrics

```python
# Monitor orchestrator performance
metrics = await orchestrator.get_metrics()
print(f"Average reasoning steps: {metrics['avg_reasoning_steps']}")
print(f"Tool usage rate: {metrics['tool_usage_rate']}")
print(f"Success rate: {metrics['success_rate']}")
```

### Error Analysis

```python
# Analyze common failure patterns
error_analysis = await orchestrator.analyze_errors()
print(f"Common errors: {error_analysis['common_errors']}")
print(f"Tool failures: {error_analysis['tool_failures']}")
print(f"Reasoning failures: {error_analysis['reasoning_failures']}")
```

## Best Practices

### Orchestrator Design

1. **Clear Objectives**: Define clear goals for each orchestrator type
2. **Modular Design**: Keep orchestrators focused on specific behaviors
3. **Error Recovery**: Implement robust error recovery mechanisms
4. **Resource Management**: Monitor and limit resource usage
5. **Testing**: Thoroughly test orchestrator behavior

### Prompt Engineering

1. **Clear Instructions**: Provide clear, specific instructions
2. **Examples**: Include examples of desired behavior
3. **Constraints**: Set clear constraints and limitations
4. **Context**: Provide sufficient context for decision-making
5. **Iteration**: Iteratively refine prompts based on behavior

### Integration

1. **Protocol Compliance**: Ensure all dependencies are properly configured
2. **Exchange Configuration**: Set up proper dependency injection
3. **Error Propagation**: Handle errors from dependencies gracefully
4. **Performance Monitoring**: Monitor performance across all components
5. **Scalability**: Design for scalability and concurrent usage