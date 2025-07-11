# How to switch from other orchestrators to ReAct pattern

This guide shows you how to migrate from [`SimpleToolOrchestrator`](../../reference/modules/orchestrator.md#simpletoolorchestrator) or other orchestrators to the [`ReActOrchestrator`](../../reference/modules/orchestrator.md#reactorchestrator) for more structured reasoning and better debugging capabilities.

## Prerequisites

- Existing agent configuration with an orchestrator module
- Basic understanding of YAML configuration
- Familiarity with your current orchestrator's behavior

## Replace SimpleToolOrchestrator with ReActOrchestrator

Update your agent configuration to use the ReAct pattern:

```yaml
# agents/react_agent.yml
id: react-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      temperature: 0.7

  - module: xaibo.primitives.modules.tools.python_tool_provider.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.weather, tools.calendar]

  # Replace this line:
  # - module: xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator
  # With this:
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 10
      show_reasoning: true
      reasoning_temperature: 0.7

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

## Configure equivalent behavior

Map your existing configuration to ReAct parameters:

### From SimpleToolOrchestrator

```yaml
# Old SimpleToolOrchestrator config
- module: xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator
  id: orchestrator
  config:
    max_thoughts: 15
    system_prompt: |
      You are a helpful assistant with access to tools.
      Think step by step and explain your reasoning.
```

```yaml
# New ReActOrchestrator config
- module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
  id: orchestrator
  config:
    max_iterations: 15  # Same as max_thoughts
    show_reasoning: true  # Enable to see step-by-step thinking
    system_prompt: |
      You are a helpful assistant that follows the ReAct pattern.
      Think step by step, use tools when needed, and explain your reasoning.
```

### Configuration mapping

| SimpleToolOrchestrator | ReActOrchestrator | Notes |
|-------------------|-------------------|-------|
| `max_thoughts` | `max_iterations` | Same iteration limit concept |
| `system_prompt` | `system_prompt` | Direct equivalent |
| Temperature stress | `reasoning_temperature` | More controlled temperature management |

## Test the migration

Run your agent with a complex query to verify the ReAct pattern:

```bash
# Start your agent
xaibo run agents/react_agent.yml

# Test with a multi-step question
"What's the weather in Paris and what should I pack for a 3-day trip?"
```

Expected ReAct output with `show_reasoning: true`:

```
🤔 **THINKING...**
💭 **THOUGHT:** I need to get weather information for Paris first, then provide packing recommendations based on the conditions.

⚡ **TAKING ACTION...**
🔧 **ACTION:** I'll check the weather in Paris.
🛠️ **EXECUTING TOOL:** get_weather with args: {"location": "Paris"}
✅ **TOOL SUCCESS:** get_weather returned: {"location": "Paris", "temperature": 18, "condition": "rainy"}

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** The weather shows it's 18°C and rainy in Paris. Now I can provide appropriate packing suggestions.

🤔 **THINKING...**
💭 **THOUGHT:** I have the weather information. I can now provide a final answer with packing recommendations.

⚡ **TAKING ACTION...**
✅ **FINAL ANSWER:** Based on the weather in Paris (18°C and rainy), pack layers including a waterproof jacket, umbrella, comfortable walking shoes, and warm clothes for the cool temperature.
```

## Disable visual reasoning for production

For production environments, disable reasoning indicators:

```yaml
- module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
  id: orchestrator
  config:
    max_iterations: 10
    show_reasoning: false  # Clean output for users
    reasoning_temperature: 0.7
```

## Handle migration issues

### Performance differences

ReActOrchestrator may use more LLM calls due to explicit reasoning phases:

```yaml
# Optimize for fewer iterations
config:
  max_iterations: 5  # Reduce from default 10
  reasoning_temperature: 0.5  # Lower temperature for faster decisions
```

### Tool execution changes

ReActOrchestrator executes tools differently than SimpleToolOrchestrator:

- Tools are called during ACTION phase only
- Each tool execution triggers an OBSERVATION phase
- No automatic temperature increase on tool failures

### Response format changes

Users will see structured reasoning with ReAct vs. direct responses:

```yaml
# For user-facing applications, consider:
config:
  show_reasoning: false  # Hide internal reasoning
  system_prompt: |
    Provide direct, helpful answers. Use the ReAct pattern internally
    but present clean final answers to users.
```

## Verify successful migration

Check that your agent:

1. **Maintains functionality** - Same tool usage and response quality
2. **Shows structured reasoning** - Clear thought-action-observation cycles
3. **Handles errors gracefully** - Continues reasoning after tool failures
4. **Respects iteration limits** - Stops at max_iterations with summary

The ReAct pattern provides more transparent and debuggable agent behavior while maintaining the same core functionality as other orchestrators.

## Related Documentation

- **Tutorial**: [Advanced Orchestration](../../tutorial/advanced-orchestration.md) - Learn to build sophisticated agents with ReAct patterns
- **Explanation**: [ReAct Pattern](../../explanation/concepts/react-pattern.md) - Understanding the reasoning and acting cycle
- **How-to Guides**:
  - [Customize ReAct Prompts](customize-react-prompts.md)
  - [Debug Agent Reasoning](debug-agent-reasoning.md)
  - [Handle Complex Workflows](handle-complex-workflows.md)