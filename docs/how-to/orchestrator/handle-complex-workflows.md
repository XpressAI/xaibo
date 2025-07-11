# How to handle complex multi-tool workflows

This guide shows you how to configure [`ReActOrchestrator`](../../reference/modules/orchestrator.md#reactorchestrator) to efficiently manage complex workflows that require multiple tools, sequential operations, and sophisticated reasoning.

## Prerequisites

- Agent configured with ReActOrchestrator
- Multiple tools available in your tool provider
- Understanding of ReAct reasoning cycles
- Complex use cases requiring multi-step processes

## Configure for complex workflows

Optimize your orchestrator for handling sophisticated multi-tool scenarios:

```yaml
# agents/complex_workflow_agent.yml
modules:
  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 20  # Increased for complex workflows
      show_reasoning: true  # Monitor complex reasoning
      reasoning_temperature: 0.6  # Balanced creativity and focus
      
      system_prompt: |
        You are an expert assistant capable of handling complex multi-step tasks.
        
        WORKFLOW PRINCIPLES:
        1. Break complex tasks into logical steps
        2. Use tools sequentially when dependencies exist
        3. Validate results before proceeding to next steps
        4. Maintain context across multiple tool executions
        5. Provide comprehensive final answers
        
        TOOL USAGE STRATEGY:
        - Plan your tool sequence before starting
        - Execute one tool at a time for better control
        - Verify each result before proceeding
        - Handle errors gracefully and continue when possible
```

## Handle sequential tool dependencies

Configure the agent to manage workflows where tools depend on each other's results:

```yaml
config:
  thought_prompt: |
    Plan your approach for this complex task:
    
    1. What are the main steps needed?
    2. Which tools are required for each step?
    3. What dependencies exist between steps?
    4. What information from previous steps do I need to carry forward?
    
    Create a logical sequence and start with the first step.
  
  action_prompt: |
    Execute the next step in your planned sequence:
    
    - If this is a dependent step, use results from previous tools
    - Call only ONE tool at a time for complex workflows
    - Use specific, accurate parameters based on previous results
    - If you have completed all steps, provide FINAL_ANSWER with comprehensive results
  
  observation_prompt: |
    Analyze the results and plan your next step:
    
    1. Was this tool execution successful?
    2. What information did I gain?
    3. How does this affect my next steps?
    4. Do I need to modify my plan based on these results?
    5. What's the next logical step in my sequence?
```

## Example: Research and booking workflow

Handle a complex travel planning scenario:

**User query:** "Plan a 3-day business trip to London next month, including flights from NYC, hotel recommendations, and weather forecast"

**Expected workflow:**
```
🤔 **THINKING...**
💭 **THOUGHT:** This requires multiple steps: 1) Check weather for planning, 2) Find flights, 3) Get hotel recommendations. I'll start with weather since it affects clothing and activity planning.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** get_weather_forecast with args: {"location": "London", "days": 30}
✅ **TOOL SUCCESS:** Weather shows mild temperatures, some rain expected

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** London weather will be 15-18°C with occasional rain. This helps with packing advice. Now I need flight information.

🤔 **THINKING...**
💭 **THOUGHT:** Now I'll search for flights from NYC to London for next month.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** search_flights with args: {"from": "NYC", "to": "London", "departure": "next month", "duration": "3 days"}
✅ **TOOL SUCCESS:** Found several flight options with prices

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** I have flight options. Now I need hotel recommendations to complete the travel plan.

🤔 **THINKING...**
💭 **THOUGHT:** Finally, I'll get hotel recommendations for the business trip.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** find_hotels with args: {"location": "London", "type": "business", "duration": "3 days"}
✅ **TOOL SUCCESS:** Found business-friendly hotels with amenities

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** I now have all components: weather, flights, and hotels. I can provide a comprehensive travel plan.

⚡ **TAKING ACTION...**
✅ **FINAL ANSWER:** Here's your complete London business trip plan:

WEATHER: Expect 15-18°C with occasional rain - pack layers and a waterproof jacket.

FLIGHTS: [flight details with prices and times]

HOTELS: [hotel recommendations with business amenities]

PACKING TIPS: Business attire, umbrella, comfortable walking shoes for mild, wet weather.
```

## Handle parallel information gathering

For workflows where tools can be executed independently:

```yaml
config:
  system_prompt: |
    For complex tasks with independent information needs:
    1. Identify which information can be gathered in parallel
    2. Execute independent tools first
    3. Combine results for comprehensive analysis
    4. Use dependent tools only after prerequisites are met
```

**Example workflow:** "Compare living costs between San Francisco, New York, and Austin"

```
💭 **THOUGHT:** I need cost data for three cities. These are independent queries, so I'll gather data for each city sequentially.

🛠️ **EXECUTING TOOL:** get_cost_of_living with args: {"city": "San Francisco"}
✅ **TOOL SUCCESS:** SF cost data retrieved

🛠️ **EXECUTING TOOL:** get_cost_of_living with args: {"city": "New York"}  
✅ **TOOL SUCCESS:** NYC cost data retrieved

🛠️ **EXECUTING TOOL:** get_cost_of_living with args: {"city": "Austin"}
✅ **TOOL SUCCESS:** Austin cost data retrieved

🔍 **OBSERVATION:** I have cost data for all three cities. Now I can provide a comprehensive comparison.

✅ **FINAL_ANSWER:** Cost of Living Comparison:
[Detailed comparison with housing, food, transportation costs for all three cities]
```

## Manage workflow state and context

Keep track of information across multiple tool executions:

```yaml
config:
  observation_prompt: |
    Analyze results and maintain workflow context:
    
    CURRENT RESULTS: What did this tool provide?
    ACCUMULATED DATA: What information do I have so far?
    REMAINING STEPS: What still needs to be done?
    CONTEXT PRESERVATION: What data must I remember for next steps?
    
    Plan the next action while maintaining all relevant context.
```

## Handle workflow errors gracefully

Configure robust error handling for complex workflows:

```yaml
config:
  error_prompt: |
    Workflow error occurred: {error}
    
    RECOVERY STRATEGY:
    1. Assess what steps were completed successfully
    2. Identify alternative approaches for the failed step
    3. Determine if partial results are still valuable
    4. Continue with remaining steps if possible
    5. Provide the best possible answer with available data
    
    Don't let one failure derail the entire workflow.
```

**Example error recovery:**
```
❌ **TOOL ERROR:** flight_search failed: API rate limit exceeded
🔍 **OBSERVATION:** Flight search failed, but I have weather and hotel data. I can provide partial results and suggest alternatives.

✅ **FINAL_ANSWER:** I've gathered most of your London trip information:

WEATHER: [weather details]
HOTELS: [hotel recommendations]
FLIGHTS: Unable to search flights due to API limits. I recommend checking directly with airlines or travel booking sites.

Would you like me to help with other aspects of your trip planning?
```

## Optimize iteration limits

Set appropriate limits based on workflow complexity:

```yaml
# For simple workflows (2-4 tools)
config:
  max_iterations: 8

# For moderate workflows (5-8 tools)  
config:
  max_iterations: 15

# For complex workflows (9+ tools)
config:
  max_iterations: 25
```

## Create workflow templates

Define reusable patterns for common complex workflows:

### Research workflow template

```yaml
config:
  system_prompt: |
    RESEARCH WORKFLOW PATTERN:
    1. GATHER: Collect information from multiple sources
    2. VERIFY: Cross-check facts and validate data
    3. ANALYZE: Compare and synthesize findings
    4. CONCLUDE: Provide comprehensive, well-sourced answer
```

### Planning workflow template

```yaml
config:
  system_prompt: |
    PLANNING WORKFLOW PATTERN:
    1. ASSESS: Understand requirements and constraints
    2. RESEARCH: Gather relevant information and options
    3. EVALUATE: Compare alternatives and trade-offs
    4. RECOMMEND: Provide actionable plan with rationale
```

### Problem-solving workflow template

```yaml
config:
  system_prompt: |
    PROBLEM-SOLVING WORKFLOW PATTERN:
    1. DIAGNOSE: Identify the root cause
    2. EXPLORE: Research potential solutions
    3. TEST: Validate approaches when possible
    4. SOLVE: Provide step-by-step solution
```

## Monitor complex workflow performance

Track these metrics for optimization:

- **Completion rate** - Percentage of workflows that reach final answer
- **Tool efficiency** - Average tools used per successful workflow
- **Error recovery** - How well the agent handles failures
- **Context preservation** - Whether information is maintained across steps

## Test complex workflows

Create comprehensive test scenarios:

```yaml
# Test scenario 1: Multi-domain research
test_query: "Research the environmental impact, economic benefits, and technical challenges of solar energy adoption in residential areas"

# Test scenario 2: Sequential planning
test_query: "Plan a product launch including market research, competitive analysis, pricing strategy, and marketing timeline"

# Test scenario 3: Error resilience
test_query: "Create a comprehensive travel itinerary with intentionally failing tools to test recovery"
```

Complex workflows require careful orchestration, robust error handling, and clear reasoning patterns. The ReActOrchestrator's structured approach makes it ideal for managing sophisticated multi-tool processes while maintaining transparency and control.

## Related Documentation

- **Tutorial**: [Advanced Orchestration](../../tutorial/advanced-orchestration.md) - Learn to build sophisticated agents with ReAct patterns
- **Explanation**: [ReAct Pattern](../../explanation/concepts/react-pattern.md) - Understanding the reasoning and acting cycle
- **How-to Guides**:
  - [Switch to ReAct Pattern](switch-to-react-pattern.md)
  - [Customize ReAct Prompts](customize-react-prompts.md)
  - [Debug Agent Reasoning](debug-agent-reasoning.md)