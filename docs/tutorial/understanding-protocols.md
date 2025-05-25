# Understanding Protocols: How Xaibo Components Work Together

In this lesson, you'll discover how Xaibo's [protocol-based architecture](../explanation/architecture/protocols.md) enables the flexibility you've experienced. You'll learn to swap components, understand module communication, and see why this design makes Xaibo so powerful and extensible.

## What You'll Learn

Through hands-on experiments, you'll understand:

- **How [protocols](../reference/protocols/index.md) define interfaces** between components
- **Why [modules can be easily swapped](../explanation/concepts/modules-vs-protocols.md)** without breaking your agent
- **How the [exchange system](../explanation/concepts/exchange-system.md)** connects modules together
- **How to modify your agent's behavior** by changing configurations

## Step 1: Understanding Your Current Agent

Let's examine your agent configuration to understand what's happening:

```bash
cat agents/example.yml
```

You'll see:
```yaml
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.
```

Each module implements specific **protocols**:

- **LLM module**: Implements [`LLMProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/llm.py)
- **Tool provider**: Implements [`ToolProviderProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/tools.py)
- **Orchestrator**: Implements [`TextMessageHandlerProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py)

Now let's run your agent to ensure you have a working system and see the current output:

```bash
uv run xaibo dev
```

Test your agent with a simple request:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What time is it?"}
    ]
  }'
```

You should see your agent respond using the `current_time` tool. This confirms your system is working correctly.

## Step 2: Switch from OpenAI to Anthropic

Let's see how easy it is to change your agent's behavior by swapping LLM providers entirely. This demonstrates the power of protocol-based architecture - despite OpenAI and Anthropic having completely different APIs, the change is trivial. For more details on switching providers, see our [LLM provider switching guide](../how-to/llm/switch-providers.md).

**First, you'll need to acquire an Anthropic API key** and set it up. You can either set it as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

Or add it to your `.env` file:

```bash
# Use your preferred editor
nano .env
# or
code .env
```

Add this line to your `.env` file:
```
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

Now edit your agent configuration:

```bash
# Use your preferred editor
nano agents/example.yml
# or
code agents/example.yml
```

Change from OpenAI to Anthropic:

```yaml
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM  # Changed from OpenAILLM
    id: llm
    config:
      model: claude-3-5-sonnet-20241022  # Changed from gpt-4.1-nano
```

Restart your server:

```bash
uv run xaibo dev
```

Test the same question with the new provider:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What time is it?"}
    ]
  }'
```

Notice how you get a different response style (Claude tends to be more structured), but your tools still work exactly the same way. This demonstrates **[protocol-based modularity](../explanation/design/modularity.md)** - you switched between completely different LLM providers with different APIs, yet no other components needed to change. The protocol interface made this swap trivial.

## Step 3: Understanding Protocol Interfaces

Let's look at what makes this modularity possible. Protocols define **interfaces** that modules must implement. Here's what the [`LLMProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/llm.py) looks like conceptually:

```python
# This is a simplified view of the LLMProtocol
class LLMProtocol:
    def generate_response(self, messages, tools=None):
        """Generate a response to messages, optionally using tools"""
        pass
```

Any module that implements this protocol can be used as an LLM, whether it's:

- OpenAI GPT models
- Anthropic Claude  
- Google Gemini
- Local models
- Mock implementations for testing

## Step 4: Experiment with a Mock LLM

Let's see this in action by switching to a mock LLM for testing. Create a new agent configuration:

```bash
cp agents/example.yml agents/mock-example.yml
```

Edit the new file:

```bash
nano agents/mock-example.yml
```

Change the configuration to use a mock LLM with proper response sequence:

```yaml
id: mock-example
description: An example agent using a mock LLM for testing
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: llm
    config:
      responses:
        # First response: Make a tool call
        - content: "I'll check the current time for you."
          tool_calls:
            - id: "call_1"
              name: "current_time"
              arguments: {}
        # Second response: Respond after tool execution
        - content: "Based on the tool result, I can see the current time. The mock LLM is working perfectly with tools!"
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.
```

Restart the server:

```bash
uv run xaibo dev
```

Test the mock agent:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mock-example",
    "messages": [
      {"role": "user", "content": "What time is it?"}
    ]
  }'
```

You'll see the mock response sequence: first it calls the `current_time` tool, then provides a final response! This demonstrates how:

- **Protocols enable testing**: You can test your agent logic without real LLM costs
- **Behavior is predictable**: Mock responses help verify your agent works correctly
- **Tools still work**: The protocol interface ensures compatibility

## Step 5: Understanding the Exchange System

The **[exchange system](../explanation/concepts/exchange-system.md)** is what connects modules together. Let's make this explicit in your configuration. Edit your `agents/example.yml`:

```bash
nano agents/example.yml
```

Add an explicit exchange section:

```yaml
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      model: claude-3-5-sonnet-20241022
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.

# Explicit exchange configuration
exchange:
  # Set the entry point for text messages
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
  # Connect orchestrator to LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  # Connect orchestrator to tools
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: python-tools
```

<!-- TODO: Add screenshot of the configuration file showing the exchange system -->

This makes explicit what Xaibo was doing automatically, but doesn't change the behavior:

- **Entry point**: Messages go to the orchestrator first
- **LLM connection**: Orchestrator uses the LLM for language understanding
- **Tool connection**: Orchestrator can access tools when needed

## Step 6: Experiment with Multiple Tool Providers Using Tool Collector

Let's see how the exchange system enables multiple tool providers using the [`ToolCollector`](../reference/modules/tools.md#toolcollector). First, create a new tool file:

Create `tools/math_tools.py`:

```python
from xaibo.primitives.modules.tools.python_tool_provider import tool
import math

@tool
def square_root(number: float):
    """Calculate the square root of a number
    
    :param number: The number to calculate square root for
    """
    if number < 0:
        return "Error: Cannot calculate square root of negative number"
    return f"√{number} = {math.sqrt(number)}"

@tool
def power(base: float, exponent: float):
    """Calculate base raised to the power of exponent
    
    :param base: The base number
    :param exponent: The exponent
    """
    result = math.pow(base, exponent)
    return f"{base}^{exponent} = {result}"
```

For more information about creating Python tools, see our [Python tools guide](../how-to/tools/python-tools.md).

Now modify your agent to use the tool collector. Copy and paste this configuration:

```yaml
id: example
description: An example agent that uses multiple tool providers
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      model: claude-3-5-sonnet-20241022
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: basic-tools
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: math-tools
    config:
      tool_packages: [tools.math_tools]
  - module: xaibo.primitives.modules.tools.ToolCollector
    id: all-tools
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.

exchange:
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  # Connect the tool collector to multiple providers
  - module: all-tools
    protocol: ToolProviderProtocol
    provider: [basic-tools, math-tools]
  # Connect orchestrator to the aggregated tools
  - module: orchestrator
    protocol: ToolProviderProtocol
    provider: all-tools
```

Restart and test:

```bash
uv run xaibo dev
```

Test the new math tools:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What is the square root of 144 and what is 2 to the power of 8?"}
    ]
  }'
```

Your agent now has access to tools from both providers through the tool collector! This demonstrates:

- **Tool aggregation**: The [`ToolCollector`](../reference/modules/tools.md#toolcollector) combines multiple tool providers
- **Clean architecture**: Single connection point for all tools
- **Easy management**: Add or remove tool providers by updating the collector configuration

## Step 7: Understanding Protocol Benefits

Through your experiments, you've seen how protocols enable:

**🔄 Easy Provider Swapping**

- Switched from OpenAI to Anthropic with completely different APIs
- Changed to mock LLM for testing with predictable responses
- All tools continued working unchanged despite different LLM providers

**🧩 Flexible Composition**

- Used [`ToolCollector`](../reference/modules/tools.md#toolcollector) to aggregate multiple tool providers
- Connected components through explicit [exchange configurations](../explanation/concepts/exchange-system.md)
- Mixed and matched implementations seamlessly

**🧪 Better Testing**

- Used mock LLM with configured response sequences
- Isolated components for [testing](../explanation/design/testability.md) without external API costs
- Verified tool calling behavior with predictable mock responses

**📈 Extensibility**

- Added new math tools without changing existing code
- Created new tool providers and aggregated them easily
- Extended functionality purely through configuration changes

**🏗️ Protocol-Based Architecture**

- Each component implements well-defined [protocols](../reference/protocols/index.md)
- Easy to substitute implementations (OpenAI ↔ Anthropic ↔ Mock)
- Clean separation between interface and implementation

## Step 8: Exploring Other Protocols

Xaibo includes several core protocols you can experiment with:

**[`MemoryProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/memory.py)**: For agent memory and context
```yaml
- module: xaibo.primitives.modules.memory.VectorMemory
  id: memory
```

**[`ConversationProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/conversation.py)**: For managing dialog history
```yaml
- module: xaibo.primitives.modules.conversation.Conversation
  id: conversation
```

**[`ResponseProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/response.py)**: For handling agent responses
```yaml
- module: xaibo.primitives.modules.ResponseHandler
  id: response
```

Each protocol defines a specific interface, enabling you to:

- Choose implementations that fit your needs
- Test with mock implementations
- Extend functionality by implementing new modules

## What You've Learned

In this lesson, you've discovered:

✅ **Protocol-based architecture** enables modular, flexible agents  
✅ **Easy component swapping** without breaking other parts  
✅ **Exchange system** connects modules through well-defined interfaces  
✅ **Multiple providers** can implement the same protocol  
✅ **Testing benefits** from mock implementations  
✅ **Configuration-driven** behavior changes  

## Understanding the Architecture

Your experiments demonstrate Xaibo's core architectural principles:

**Separation of Concerns**: Each module has a specific responsibility

- [LLM modules](../reference/modules/llm.md) handle language understanding
- [Tool modules](../reference/modules/tools.md) provide capabilities
- [Orchestrators](../reference/modules/orchestrator.md) manage workflow

**Protocol-Based Interfaces**: Modules communicate through standardized [protocols](../reference/protocols/index.md)

- Clear contracts between components
- Easy to test and mock
- Enables component substitution

**[Dependency Injection](../explanation/architecture/dependency-injection.md)**: Modules declare what they need, not how to get it

- Flexible wiring through [exchanges](../explanation/concepts/exchange-system.md)
- Easy to reconfigure
- Supports multiple implementations

**Event-Driven Transparency**: All interactions are observable

- Debug UI shows component interactions
- Performance monitoring built-in
- Easy to understand agent behavior

## Real-World Applications

This architecture enables powerful real-world scenarios:

**Development to Production**: Start with mock LLMs for testing, switch to real models for production

**Multi-Model Strategies**: Use different LLMs for different tasks (fast model for simple queries, powerful model for complex reasoning)

**Gradual Enhancement**: Add memory, conversation history, or specialized tools without changing existing components

**A/B Testing**: Compare different LLM models or orchestration strategies by changing configuration

## Congratulations!

You've completed the Xaibo tutorial! You now understand:

- How to create and run Xaibo agents
- How to build custom tools that extend agent capabilities  
- How Xaibo's protocol-based architecture enables flexibility and modularity

## Next Steps

Now that you understand the fundamentals, explore:

- **[Testing Agents](testing-agents.md)**: Learn to test your agents with dependency injection and event capture
- **[How-to Guides](../how-to/index.md)**: Practical solutions for specific tasks

    - [Switch LLM Providers](../how-to/llm/switch-providers.md)
    - [Python Tools](../how-to/tools/python-tools.md)
    - [MCP Tools](../how-to/tools/mcp-tools.md)

- **[Reference Documentation](../reference/index.md)**: Detailed API and configuration reference

    - [Protocols Overview](../reference/protocols/index.md)
    - [Module Reference](../reference/modules/llm.md)

- **[Architecture Explanations](../explanation/index.md)**: Deep dives into design concepts

    - [Protocol Architecture](../explanation/architecture/protocols.md)
    - [Exchange System](../explanation/concepts/exchange-system.md)
    - [Modularity Design](../explanation/design/modularity.md)

- **[Examples](https://github.com/xpressai/xaibo/tree/main/examples)**: Real-world agent implementations

Ready to build something amazing with Xaibo? The framework's modular architecture gives you the flexibility to create agents that fit your exact needs!