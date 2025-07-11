# Advanced Orchestration: Mastering the ReAct Pattern

In this lesson, you'll learn to build intelligent agents that think step-by-step using the ReAct (Reasoning and Acting) pattern. You'll create agents that show their reasoning process, handle complex multi-step tasks, and recover gracefully from errors. By the end, you'll have built a research assistant that demonstrates the power of explicit reasoning.

## What You'll Learn

Through hands-on exercises, you'll discover how to:

- **Understand the ReAct cycle** - See how Thought-Action-Observation creates better reasoning
- **Build a ReAct agent** - Create an agent that shows its thinking process
- **Handle complex workflows** - Chain multiple tools together systematically  
- **Debug agent reasoning** - Use visual indicators to understand agent behavior
- **Customize reasoning behavior** - Tailor prompts for specific use cases

## What You'll Build

You'll create a research assistant agent that can:

- Research topics using multiple information sources
- Show its step-by-step reasoning process
- Handle errors and continue working toward solutions
- Provide comprehensive answers based on gathered information

## Prerequisites

Before starting, make sure you have:

- Completed the [Getting Started](getting-started.md) tutorial
- Basic understanding of agent configuration
- Python 3.10 or higher installed
- An OpenAI API key configured

## Understanding the ReAct Pattern

The ReAct pattern transforms how AI agents approach complex problems. Instead of trying to solve everything at once, agents follow a structured cycle:

1. **THOUGHT**: Reason about what to do next
2. **ACTION**: Execute a tool or provide a final answer  
3. **OBSERVATION**: Analyze results and plan next steps

This creates transparent, debuggable agents that make better decisions.

## Step 1: Create Your Research Assistant Project

Let's start by creating a new project for our research assistant:

```bash
uvx xaibo init research_assistant
cd research_assistant
```

When prompted, select both `webserver` and `openai` functionality.

## Step 2: Build Research Tools

First, let's create tools that our research assistant can use. Create a new file for research tools:

```bash
# Create the research tools file
touch tools/research.py
```

Add these research tools:

```python
# tools/research.py
import requests
from datetime import datetime
from typing import Dict, Any, List
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def search_wikipedia(query: str) -> Dict[str, Any]:
    """Search Wikipedia for information on a topic
    
    Args:
        query: The search term or topic
        
    Returns:
        Dictionary with search results and summary
    """
    try:
        # Wikipedia API search
        search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        response = requests.get(search_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", ""),
                "summary": data.get("extract", "")[:500] + "..." if len(data.get("extract", "")) > 500 else data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "found": True
            }
        else:
            return {"found": False, "error": f"Wikipedia search failed with status {response.status_code}"}
    except Exception as e:
        return {"found": False, "error": f"Search error: {str(e)}"}

@tool
def get_current_date() -> str:
    """Get the current date for context in research
    
    Returns:
        Current date in YYYY-MM-DD format
    """
    return datetime.now().strftime("%Y-%m-%d")

@tool
def analyze_topic_complexity(topic: str) -> Dict[str, Any]:
    """Analyze how complex a research topic might be
    
    Args:
        topic: The research topic to analyze
        
    Returns:
        Analysis of topic complexity and suggested approach
    """
    # Simple heuristic-based analysis
    word_count = len(topic.split())
    has_technical_terms = any(term in topic.lower() for term in 
                             ['quantum', 'molecular', 'algorithm', 'neural', 'genetic', 'biochemical'])
    has_historical_terms = any(term in topic.lower() for term in 
                              ['history', 'ancient', 'medieval', 'century', 'war', 'revolution'])
    
    complexity_score = word_count
    if has_technical_terms:
        complexity_score += 3
    if has_historical_terms:
        complexity_score += 2
        
    if complexity_score <= 3:
        complexity = "Simple"
        approach = "Single source search should be sufficient"
    elif complexity_score <= 6:
        complexity = "Moderate" 
        approach = "Multiple sources recommended, check for recent developments"
    else:
        complexity = "Complex"
        approach = "Comprehensive research needed, multiple perspectives required"
        
    return {
        "complexity": complexity,
        "score": complexity_score,
        "approach": approach,
        "technical_topic": has_technical_terms,
        "historical_topic": has_historical_terms
    }
```

## Step 3: Configure Your ReAct Research Agent

Now let's create an agent configuration that uses the ReAct pattern. Replace the contents of `agents/example.yml`:

```yaml
# agents/research_agent.yml
id: research-agent
description: A research assistant that uses ReAct pattern for systematic investigation
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4o-mini
      temperature: 0.7

  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: research-tools
    config:
      tool_packages: [tools.research]

  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 8
      show_reasoning: true
      reasoning_temperature: 0.7
      system_prompt: |
        You are a research assistant that follows the ReAct pattern for systematic investigation.
        
        Your goal is to provide comprehensive, well-researched answers by:
        1. THINKING about what information you need
        2. TAKING ACTION to gather that information using available tools
        3. OBSERVING the results and deciding what to do next
        
        Continue this cycle until you have enough information to provide a complete answer.
        
        Available tools:
        - search_wikipedia: Search Wikipedia for factual information
        - get_current_date: Get today's date for context
        - analyze_topic_complexity: Understand how complex a topic is
        
        Always start by analyzing the topic complexity to plan your research approach.

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: research-tools
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

## Step 4: Test Your Basic ReAct Agent

Let's start the agent and see the ReAct pattern in action:

```bash
uv run xaibo dev
```

You should see the server start. Now test with a simple research question:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "research-agent",
    "messages": [
      {"role": "user", "content": "What is machine learning?"}
    ]
  }'
```

**What you should see:**

The agent will show its reasoning process with visual indicators:

```
🤔 **THINKING...**
💭 **THOUGHT:** I need to research machine learning. Let me first analyze the complexity of this topic to plan my approach.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** analyze_topic_complexity with args: {"topic": "machine learning"}
✅ **TOOL SUCCESS:** analyze_topic_complexity returned: {"complexity": "Moderate", "technical_topic": true, ...}

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** This is a moderate complexity technical topic. I should search for comprehensive information about machine learning.

🤔 **THINKING...**
💭 **THOUGHT:** Now I'll search Wikipedia for detailed information about machine learning.

⚡ **TAKING ACTION...**
🛠️ **EXECUTING TOOL:** search_wikipedia with args: {"query": "machine learning"}
✅ **TOOL SUCCESS:** search_wikipedia returned: {"title": "Machine learning", "summary": "Machine learning is...", ...}

👁️ **OBSERVING RESULTS...**
🔍 **OBSERVATION:** I have good information about machine learning. I can now provide a comprehensive answer.

🤔 **THINKING...**
💭 **THOUGHT:** I have sufficient information to provide a complete answer about machine learning.

⚡ **TAKING ACTION...**
✅ **FINAL ANSWER:** Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed...
```

**Congratulations!** You've just seen the ReAct pattern in action. Notice how the agent:

1. **Planned its approach** by analyzing topic complexity
2. **Gathered information** systematically using tools
3. **Showed its reasoning** at each step
4. **Made deliberate decisions** about when to stop and provide an answer

## Step 5: Understanding the Thought-Action-Observation Cycle

Let's examine what happened in more detail by looking at the debug UI. Open http://127.0.0.1:9000 in your browser and click on **research-agent**.

You'll see a sequence diagram showing:

- **Thought phases** (🤔) where the agent reasons about next steps
- **Action phases** (⚡) where tools are executed or final answers provided
- **Observation phases** (👁️) where results are analyzed

This visualization helps you understand exactly how your agent thinks and makes decisions.

## Step 6: Handle Complex Multi-Step Research

Now let's test the agent with a more complex question that requires multiple research steps:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "research-agent",
    "messages": [
      {"role": "user", "content": "Compare quantum computing and classical computing, and explain which is better for different types of problems."}
    ]
  }'
```

**What you should observe:**

The agent will follow a more complex reasoning path:

1. **Analyze complexity** - Recognize this as a complex technical topic
2. **Research quantum computing** - Gather information about quantum systems
3. **Research classical computing** - Get information about traditional computers  
4. **Compare and synthesize** - Analyze the information to provide a comprehensive comparison

This demonstrates how ReAct handles complex, multi-step reasoning tasks that require gathering and synthesizing information from multiple sources.

## Step 7: Customize Reasoning Behavior

Let's create a specialized version of our agent for historical research. Create a new agent configuration:

```yaml
# agents/history_researcher.yml
id: history-researcher
description: A specialized research assistant for historical topics
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4o-mini
      temperature: 0.7

  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: research-tools
    config:
      tool_packages: [tools.research]

  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 10
      show_reasoning: true
      reasoning_temperature: 0.8  # Higher temperature for creative historical analysis
      thought_prompt: |
        Consider the historical context and multiple perspectives. What information do you need to provide a balanced historical analysis?
      action_prompt: |
        Take action to gather historical information. Consider:
        1. Primary sources and historical accuracy
        2. Multiple perspectives on historical events
        3. Historical context and timeline
        
        Either use a tool or provide FINAL_ANSWER if you have sufficient information.
      observation_prompt: |
        Analyze the historical information you've gathered. Consider:
        - Is this information historically accurate?
        - Do you need additional perspectives?
        - What historical context is missing?
        
        Decide your next steps for comprehensive historical research.
      system_prompt: |
        You are a historical research assistant that follows the ReAct pattern.
        
        Your specialty is providing balanced, well-researched historical analysis by:
        1. THINKING about historical context and multiple perspectives
        2. TAKING ACTION to gather historical information
        3. OBSERVING results and considering historical accuracy and bias
        
        Always consider multiple perspectives and historical context in your research.

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: research-tools
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

Test the specialized historical researcher:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "history-researcher", 
    "messages": [
      {"role": "user", "content": "What were the main causes of World War I?"}
    ]
  }'
```

Notice how the customized prompts lead to different reasoning patterns focused on historical analysis and multiple perspectives.

## Step 8: Debug Agent Reasoning

Sometimes agents don't behave as expected. Let's create a scenario where we can practice debugging. Add this tool to `tools/research.py`:

```python
@tool
def unreliable_search(query: str) -> Dict[str, Any]:
    """A search tool that sometimes fails (for debugging practice)
    
    Args:
        query: The search query
        
    Returns:
        Search results or error
    """
    import random
    
    # Simulate random failures for debugging practice
    if random.random() < 0.3:  # 30% chance of failure
        return {"error": "Network timeout", "success": False}
    
    return {
        "success": True,
        "results": f"Mock search results for: {query}",
        "source": "unreliable_search"
    }
```

Create a debugging-focused agent configuration:

```yaml
# agents/debug_agent.yml
id: debug-agent
description: An agent for practicing debugging techniques
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4o-mini

  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.research]

  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 6
      show_reasoning: true
      reasoning_temperature: 0.7
      error_prompt: |
        An error occurred: {error}
        
        As a research assistant, consider alternative approaches:
        1. Try a different tool if available
        2. Use information you've already gathered
        3. Provide the best answer possible with available information
        
        Provide a FINAL_ANSWER that acknowledges limitations but still helps the user.

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

Test error handling:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "debug-agent",
    "messages": [
      {"role": "user", "content": "Research renewable energy using the unreliable_search tool"}
    ]
  }'
```

**Debugging observations:**

- Watch how the agent handles tool failures
- Notice the error recovery reasoning process
- See how it adapts when tools don't work as expected
- Observe the final answer quality despite errors

## Step 9: Production-Ready Configuration

For production use, you'll want to hide the reasoning indicators while keeping the benefits of structured thinking. Create a production configuration:

```yaml
# agents/production_researcher.yml
id: production-researcher
description: Production-ready research assistant with hidden reasoning
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4o-mini
      temperature: 0.7

  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: research-tools
    config:
      tool_packages: [tools.research]

  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 8
      show_reasoning: false  # Hide reasoning indicators for clean user experience
      reasoning_temperature: 0.7
      system_prompt: |
        You are a professional research assistant. Use the ReAct pattern internally
        but provide clean, comprehensive answers to users.
        
        Research thoroughly using available tools, then provide well-structured
        final answers without showing your internal reasoning process.

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: research-tools
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

Test the production version:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "production-researcher",
    "messages": [
      {"role": "user", "content": "What is artificial intelligence?"}
    ]
  }'
```

You'll get a comprehensive answer without seeing the reasoning indicators, but the agent still follows the structured ReAct pattern internally.

## Step 10: Advanced Multi-Tool Workflow

Let's create a more sophisticated research workflow. Add this advanced tool to `tools/research.py`:

```python
@tool
def create_research_summary(topic: str, sources: List[str]) -> Dict[str, Any]:
    """Create a structured summary of research findings
    
    Args:
        topic: The research topic
        sources: List of information sources used
        
    Returns:
        Structured research summary
    """
    return {
        "topic": topic,
        "summary_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sources_count": len(sources),
        "sources": sources,
        "research_quality": "comprehensive" if len(sources) >= 2 else "basic",
        "recommendations": [
            "Verify information with additional sources",
            "Consider multiple perspectives",
            "Check for recent developments"
        ]
    }
```

Create an advanced research agent:

```yaml
# agents/advanced_researcher.yml
id: advanced-researcher
description: Advanced research assistant with comprehensive workflow
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4o-mini
      temperature: 0.7

  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: research-tools
    config:
      tool_packages: [tools.research]

  - module: xaibo.primitives.modules.orchestrator.ReActOrchestrator
    id: orchestrator
    config:
      max_iterations: 12
      show_reasoning: true
      reasoning_temperature: 0.7
      system_prompt: |
        You are an advanced research assistant that follows a comprehensive research workflow:
        
        1. Analyze topic complexity to plan your approach
        2. Gather information from multiple sources when possible
        3. Create a research summary to organize findings
        4. Provide a comprehensive final answer
        
        Use all available tools systematically to provide the most complete research possible.

exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: research-tools
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

Test the advanced workflow:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "advanced-researcher",
    "messages": [
      {"role": "user", "content": "Research the impact of climate change on polar ice caps and provide a comprehensive analysis."}
    ]
  }'
```

**What you should observe:**

The agent will follow a sophisticated research workflow:

1. **Analyze complexity** - Recognize this as a complex environmental topic
2. **Plan research approach** - Decide on multiple information gathering steps
3. **Gather information** - Search for relevant information
4. **Create research summary** - Organize findings systematically
5. **Provide comprehensive analysis** - Synthesize all information into a complete answer

## What You've Learned

In this tutorial, you've mastered:

✅ **ReAct Pattern Fundamentals** - Understanding Thought-Action-Observation cycles  
✅ **Building ReAct Agents** - Creating agents that show their reasoning process  
✅ **Tool Integration** - Connecting multiple tools for complex workflows  
✅ **Reasoning Customization** - Tailoring prompts for specific use cases  
✅ **Error Handling** - Building resilient agents that recover from failures  
✅ **Debug Techniques** - Using visual indicators to understand agent behavior  
✅ **Production Configuration** - Deploying agents with clean user experiences  

## Understanding the Benefits

Your ReAct agents demonstrate key advantages over simpler orchestration patterns:

- **Transparency**: You can see exactly how the agent thinks and makes decisions
- **Reliability**: Structured reasoning reduces errors and improves consistency  
- **Debuggability**: Visual indicators make it easy to identify and fix problems
- **Flexibility**: Customizable prompts allow adaptation to different domains
- **Robustness**: Built-in error handling keeps agents working despite failures

## Common Troubleshooting

**Agent gets stuck in reasoning loops:**
- Reduce `max_iterations` to force earlier conclusions
- Lower `reasoning_temperature` for more focused thinking
- Improve tool descriptions to guide better decisions

**Too many LLM calls:**
- Reduce `max_iterations` for simpler tasks
- Use `show_reasoning: false` in production
- Optimize tool selection in system prompts

**Poor reasoning quality:**
- Increase `reasoning_temperature` for more creative thinking
- Customize thought/observation prompts for your domain
- Provide better context in system prompts

## Next Steps

You now have powerful ReAct agents that can handle complex research tasks. Consider exploring:

- **Custom tool development** for domain-specific capabilities
- **Advanced prompt engineering** for specialized reasoning patterns
- **Integration with external APIs** for real-world data access
- **Multi-agent workflows** where ReAct agents collaborate

The ReAct pattern provides a foundation for building transparent, reliable AI agents that users can understand and trust. Your research assistant demonstrates how structured reasoning leads to better outcomes in complex problem-solving scenarios.

Ready to build more sophisticated agents? Explore the [How-to Guides](../how-to/index.md#orchestratorconfiguration) for advanced ReAct techniques and customization options.

## Related Documentation

- **Reference**: [Orchestrator Modules Reference](../reference/modules/orchestrator.md) - Technical details and configuration options for ReActOrchestrator
- **Explanation**: [ReAct Pattern](../explanation/concepts/react-pattern.md) - Deep dive into the reasoning and acting cycle
- **How-to Guides**:
  - [Switch to ReAct Pattern](../how-to/orchestrator/switch-to-react-pattern.md) - Migrate from other orchestrators
  - [Customize ReAct Prompts](../how-to/orchestrator/customize-react-prompts.md) - Tailor reasoning behavior for specific domains
  - [Debug Agent Reasoning](../how-to/orchestrator/debug-agent-reasoning.md) - Troubleshoot and optimize agent behavior
  - [Handle Complex Workflows](../how-to/orchestrator/handle-complex-workflows.md) - Manage sophisticated multi-tool processes