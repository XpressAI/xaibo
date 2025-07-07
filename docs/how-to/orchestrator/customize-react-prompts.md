# How to customize ReAct reasoning prompts

This guide shows you how to customize the prompts used by [`ReActOrchestrator`](../../reference/modules/orchestrator.md#reactorchestrator) to control how your agent thinks, acts, and observes during the reasoning process.

## Prerequisites

- Agent configured with ReActOrchestrator
- Understanding of the ReAct pattern (Thought-Action-Observation cycles)
- Basic prompt engineering knowledge

## Understand the default prompts

The ReActOrchestrator uses five types of prompts:

```yaml
# Default prompt structure
config:
  system_prompt: "Base instructions for ReAct behavior"
  thought_prompt: "Generate thoughts about next steps"
  action_prompt: "Take actions or provide final answer"
  observation_prompt: "Analyze tool results"
  error_prompt: "Handle errors: {error}"
  max_iterations_prompt: "Reached limit: {max_iterations}"
```

## Customize the system prompt

Define the overall agent behavior and ReAct pattern:

```yaml
# agents/custom_react_agent.yml
modules:
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      system_prompt: |
        You are a research assistant that follows the ReAct pattern.
        
        RULES:
        1. Always start with THOUGHT to analyze the user's request
        2. Use ACTION to either call tools or provide FINAL_ANSWER
        3. After tool execution, use OBSERVATION to analyze results
        4. Be thorough but concise in your reasoning
        5. Cite sources when using tool data
        
        AVAILABLE PHASES:
        - THOUGHT: Reason about what information you need
        - ACTION: Execute tools or provide final answer
        - OBSERVATION: Analyze tool results and plan next steps
        
        Always explain your reasoning clearly and use tools when they can help.
```

## Customize thought generation

Control how the agent reasons about problems:

```yaml
config:
  thought_prompt: |
    Analyze the current situation carefully:
    
    1. What is the user asking for?
    2. What information do I already have?
    3. What information do I still need?
    4. Which tools could help me get this information?
    5. What's my next best step?
    
    Provide your THOUGHT with clear reasoning about your approach.
```

## Customize action prompts

Guide how the agent decides between tool usage and final answers:

```yaml
config:
  action_prompt: |
    Based on your analysis, choose the most appropriate ACTION:
    
    OPTION 1 - Use a tool if you need more information:
    - Call the most relevant tool with appropriate parameters
    - Only call one tool at a time for better control
    
    OPTION 2 - Provide final answer if you have sufficient information:
    - Use format: FINAL_ANSWER: [your complete response]
    - Include all relevant details and sources
    - Make sure your answer fully addresses the user's question
    
    Choose wisely and explain your choice.
```

## Customize observation analysis

Control how the agent processes tool results:

```yaml
config:
  observation_prompt: |
    Analyze the tool execution results:
    
    1. What did the tool return?
    2. Is the information accurate and relevant?
    3. Does this fully answer the user's question?
    4. Do I need additional information from other tools?
    5. Am I ready to provide a final answer?
    
    Provide your OBSERVATION with clear analysis of what you learned
    and what you plan to do next.
```

## Create domain-specific prompts

Customize prompts for specific use cases:

### Research assistant

```yaml
config:
  system_prompt: |
    You are an academic research assistant using the ReAct pattern.
    Always verify information from multiple sources and cite your sources.
  
  thought_prompt: |
    Consider this research question methodically:
    - What type of information is needed?
    - What are the most reliable sources?
    - How can I verify the information?
    
  action_prompt: |
    Take the most appropriate research action:
    1. Search for academic sources if you need scholarly information
    2. Use fact-checking tools for verification
    3. Provide FINAL_ANSWER with proper citations when complete
  
  observation_prompt: |
    Evaluate the research findings:
    - Is the source credible and recent?
    - Does it support or contradict other findings?
    - Do I have enough evidence for a conclusion?
```

### Customer support agent

```yaml
config:
  system_prompt: |
    You are a helpful customer support agent using ReAct reasoning.
    Always be empathetic and solution-focused.
  
  thought_prompt: |
    Understand the customer's issue:
    - What problem are they experiencing?
    - What information do I need to help them?
    - What tools can assist with this issue?
  
  action_prompt: |
    Take the best action to help the customer:
    1. Use diagnostic tools to understand the issue
    2. Search knowledge base for solutions
    3. Provide FINAL_ANSWER with clear, actionable steps
  
  observation_prompt: |
    Review the diagnostic results:
    - What does this tell us about the problem?
    - Can I provide a solution now?
    - Do I need more information?
```

## Handle errors with custom prompts

Customize error handling for your domain:

```yaml
config:
  error_prompt: |
    An error occurred: {error}
    
    As a professional assistant, I should:
    1. Acknowledge the issue without technical jargon
    2. Explain what I was trying to accomplish
    3. Provide alternative approaches or partial answers
    4. Suggest next steps for the user
    
    Provide a helpful FINAL_ANSWER despite this setback.
  
  max_iterations_prompt: |
    I've reached my analysis limit of {max_iterations} steps.
    
    Let me provide the best answer I can based on my research so far:
    1. Summarize what I've learned
    2. Identify any gaps in information
    3. Provide actionable recommendations
    4. Suggest how the user can get additional help if needed
```

## Test your custom prompts

Create a test configuration to verify prompt behavior:

```yaml
# agents/test_custom_prompts.yml
modules:
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 3  # Limit for testing
      show_reasoning: true  # See prompt effects
      reasoning_temperature: 0.8  # More creative reasoning
      
      # Your custom prompts here
      thought_prompt: |
        Think step by step about this problem...
      
      action_prompt: |
        Choose your next action carefully...
```

Test with various scenarios:

```bash
# Test complex multi-step questions
"Research the environmental impact of electric vehicles and compare with traditional cars"

# Test error handling
"Get weather data for a non-existent location"

# Test iteration limits
"Plan a detailed 2-week itinerary for visiting 15 European cities"
```

## Monitor prompt effectiveness

Track how well your custom prompts work:

1. **Reasoning quality** - Are thoughts logical and well-structured?
2. **Tool usage** - Are tools called appropriately and efficiently?
3. **Error handling** - Does the agent recover gracefully from failures?
4. **Final answers** - Are responses complete and helpful?

## Best practices for prompt customization

### Keep prompts focused

```yaml
# Good - specific and actionable
thought_prompt: |
  Consider what information you need and which tools can help.

# Avoid - too verbose and unfocused
thought_prompt: |
  Think about everything related to this topic, consider all possibilities,
  analyze from multiple angles, and contemplate various approaches...
```

### Use consistent formatting

```yaml
# Maintain consistent structure across prompts
thought_prompt: |
  ANALYZE: What does the user need?
  PLAN: What's your approach?
  
action_prompt: |
  DECIDE: Tool or final answer?
  EXECUTE: Take the chosen action.
  
observation_prompt: |
  REVIEW: What did you learn?
  NEXT: What's your next step?
```

### Include examples when helpful

```yaml
action_prompt: |
  Choose your action:
  
  Example tool call:
  "I need weather data, so I'll call get_weather with location parameter"
  
  Example final answer:
  "FINAL_ANSWER: Based on my research, the answer is..."
```

Custom prompts give you fine-grained control over your agent's reasoning process, allowing you to optimize behavior for specific domains and use cases.

## Related Documentation

- **Tutorial**: [Advanced Orchestration](../../tutorial/advanced-orchestration.md) - Learn to build sophisticated agents with ReAct patterns
- **Explanation**: [ReAct Pattern](../../explanation/concepts/react-pattern.md) - Understanding the reasoning and acting cycle
- **How-to Guides**:
  - [Switch to ReAct Pattern](switch-to-react-pattern.md)
  - [Debug Agent Reasoning](debug-agent-reasoning.md)
  - [Handle Complex Workflows](handle-complex-workflows.md)