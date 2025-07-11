# How to debug agent reasoning with visual indicators

This guide shows you how to use [`ReActOrchestrator`](../../reference/modules/orchestrator.md#reactorchestrator) visual reasoning indicators to debug agent behavior, identify issues, and optimize performance.

## Prerequisites

- Agent configured with ReActOrchestrator
- Understanding of ReAct phases (Thought-Action-Observation)
- Access to agent logs or console output

## Enable visual reasoning indicators

Configure your agent to show detailed reasoning steps:

```yaml
# agents/debug_agent.yml
modules:
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      show_reasoning: true  # Enable visual indicators
      max_iterations: 10
      reasoning_temperature: 0.7
```

## Understand the visual indicators

The ReActOrchestrator provides real-time feedback with these indicators:

### Thinking phase indicators

```
🤔 **THINKING...**          # Agent is generating thoughts
💭 **THOUGHT:** [reasoning]  # Shows the actual reasoning process
```

### Action phase indicators

```
⚡ **TAKING ACTION...**      # Agent is deciding what to do
🔧 **ACTION:** [decision]    # Shows the chosen action
🛠️ **EXECUTING TOOL:** [name] with args: [params]  # Tool execution
```

### Tool execution results

```
✅ **TOOL SUCCESS:** [tool] returned: [result]     # Successful execution
❌ **TOOL ERROR:** [tool] failed: [error]          # Tool failure
💥 **TOOL EXCEPTION:** [tool] threw: [exception]   # Unexpected error
```

### Observation phase indicators

```
👁️ **OBSERVING RESULTS...**     # Agent is analyzing results
🔍 **OBSERVATION:** [analysis]   # Shows the analysis process
```

### Error and limit indicators

```
⚠️ **ERROR OCCURRED:** [error]           # General error handling
⏰ **MAX ITERATIONS REACHED:** [message] # Hit iteration limit
✅ **FINAL ANSWER:** [response]          # Final response to user
```

## Debug common reasoning issues

### Issue: Agent loops without progress

**Symptoms:**
```
🤔 **THINKING...**
💭 **THOUGHT:** I need to get weather information.

⚡ **TAKING ACTION...**
🔧 **ACTION:** I should check the weather.

🤔 **THINKING...**
💭 **THOUGHT:** I need to get weather information.
```

**Solution:** Improve action prompts to be more specific:

```yaml
config:
  action_prompt: |
    Take a specific action now:
    1. If you need information, call a specific tool with exact parameters
    2. If you have enough information, provide FINAL_ANSWER: [complete response]
    
    Do not repeat previous actions. Choose decisively.
```

### Issue: Tools called with wrong parameters

**Symptoms:**
```
🛠️ **EXECUTING TOOL:** get_weather with args: {"location": "weather in Paris"}
❌ **TOOL ERROR:** get_weather failed: Invalid location format
```

**Solution:** Add parameter guidance to system prompt:

```yaml
config:
  system_prompt: |
    When calling tools, use proper parameter formats:
    - get_weather: Use city names only (e.g., "Paris", not "weather in Paris")
    - calculate: Use mathematical expressions (e.g., "2+2", not "add 2 and 2")
    
    Always check tool documentation before calling.
```

### Issue: Agent gives up too early

**Symptoms:**
```
❌ **TOOL ERROR:** search failed: Rate limit exceeded
⚠️ **ERROR OCCURRED:** Search unavailable
✅ **FINAL ANSWER:** I cannot help due to technical issues.
```

**Solution:** Customize error handling to try alternatives:

```yaml
config:
  error_prompt: |
    Error occurred: {error}
    
    Before giving up:
    1. Can I use a different tool to get similar information?
    2. Do I have partial information that's still useful?
    3. Can I provide general guidance based on my knowledge?
    
    Try alternative approaches or provide the best answer possible.
```

## Debug tool execution problems

### Monitor tool call patterns

Look for these patterns in the visual output:

**Good tool usage:**
```
🛠️ **EXECUTING TOOL:** get_weather with args: {"location": "Paris"}
✅ **TOOL SUCCESS:** get_weather returned: {"temp": 18, "condition": "rainy"}
🔍 **OBSERVATION:** Perfect! I have current weather data for Paris.
```

**Problematic tool usage:**
```
🛠️ **EXECUTING TOOL:** get_weather with args: {"city": "Paris"}  # Wrong parameter name
❌ **TOOL ERROR:** get_weather failed: Missing required parameter 'location'
```

### Create a tool debugging configuration

```yaml
# agents/tool_debug_agent.yml
modules:
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      show_reasoning: true
      max_iterations: 3  # Limit iterations for focused debugging
      reasoning_temperature: 0.3  # Lower temperature for consistent behavior
      
      system_prompt: |
        You are debugging tool usage. For each tool call:
        1. State exactly what information you need
        2. Identify the correct tool and parameters
        3. Explain why you chose those parameters
        4. After execution, verify the results make sense
```

## Debug reasoning temperature effects

Test different temperature settings to optimize reasoning:

### High temperature (0.8-1.0) - Creative but inconsistent

```yaml
config:
  reasoning_temperature: 0.9
```

**Typical output:**
```
💭 **THOUGHT:** There are multiple fascinating approaches to this problem. 
I could explore weather patterns, historical data, or even consider 
meteorological theories...
```

### Low temperature (0.1-0.3) - Focused but potentially rigid

```yaml
config:
  reasoning_temperature: 0.2
```

**Typical output:**
```
💭 **THOUGHT:** I need weather data. I will call get_weather with location parameter.
```

### Balanced temperature (0.5-0.7) - Good for most cases

```yaml
config:
  reasoning_temperature: 0.6
```

## Create debugging test scenarios

### Test scenario 1: Multi-tool workflow

```yaml
# Test complex reasoning with multiple tools
test_query: "What's the weather in Tokyo and how much would a flight from New York cost?"
```

Expected reasoning pattern:
```
🤔 **THINKING...**
💭 **THOUGHT:** I need two pieces of information: weather and flight cost.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** get_weather with args: {"location": "Tokyo"}
✅ **TOOL SUCCESS:** get_weather returned: {"temp": 22, "condition": "sunny"}

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** Got Tokyo weather. Now I need flight pricing.

🤔 **THINKING...**
💭 **THOUGHT:** Now I'll get flight information.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** get_flight_price with args: {"from": "New York", "to": "Tokyo"}
```

### Test scenario 2: Error recovery

```yaml
# Test how agent handles tool failures
test_query: "Get weather for InvalidCityName123"
```

Expected error handling:
```
❌ **TOOL ERROR:** get_weather failed: City not found
🔍 **OBSERVATION:** The city name seems invalid. I should ask for clarification.
✅ **FINAL ANSWER:** I couldn't find weather data for "InvalidCityName123". 
Could you provide a valid city name?
```

## Monitor performance metrics

Track these indicators for optimization:

### Efficiency metrics

- **Iterations to completion** - Lower is generally better
- **Tool success rate** - Higher indicates better parameter usage
- **Reasoning coherence** - Thoughts should logically lead to actions

### Quality metrics

- **Final answer completeness** - Does it fully address the query?
- **Tool usage appropriateness** - Are the right tools called?
- **Error recovery effectiveness** - How well does it handle failures?

## Create a debugging checklist

Use this checklist when debugging agent behavior:

1. **Enable visual indicators** - Set `show_reasoning: true`
2. **Check thought quality** - Are thoughts logical and specific?
3. **Verify tool calls** - Are parameters correct and tools appropriate?
4. **Monitor observations** - Does the agent learn from tool results?
5. **Test error scenarios** - How does it handle failures?
6. **Optimize temperature** - Adjust for your use case
7. **Review iteration patterns** - Look for loops or inefficiencies

## Disable debugging for production

Once debugging is complete, optimize for production:

```yaml
# Production configuration
config:
  show_reasoning: false  # Clean output for users
  max_iterations: 8      # Optimized based on debugging
  reasoning_temperature: 0.6  # Balanced setting from testing
```

Visual reasoning indicators are powerful tools for understanding and optimizing your agent's decision-making process. Use them during development and testing to create more reliable and efficient agents.

## Related Documentation

- **Tutorial**: [Advanced Orchestration](../../tutorial/advanced-orchestration.md) - Learn to build sophisticated agents with ReAct patterns
- **Explanation**: [ReAct Pattern](../../explanation/concepts/react-pattern.md) - Understanding the reasoning and acting cycle
- **How-to Guides**:
  - [Switch to ReAct Pattern](switch-to-react-pattern.md)
  - [Customize ReAct Prompts](customize-react-prompts.md)
  - [Handle Complex Workflows](handle-complex-workflows.md)