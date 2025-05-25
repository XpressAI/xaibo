# Understanding Protocols: How Xaibo Components Work Together

In this lesson, you'll discover how Xaibo's protocol-based architecture enables the flexibility you've experienced. You'll learn to swap components, understand module communication, and see why this design makes Xaibo so powerful and extensible.

## What You'll Learn

Through hands-on experiments, you'll understand:

- **How protocols define interfaces** between components
- **Why modules can be easily swapped** without breaking your agent
- **How the exchange system** connects modules together
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
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
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

## Step 2: Experiment with Different LLM Models

Let's see how easy it is to change your agent's behavior by swapping the LLM model. Edit your agent configuration:

```bash
# Use your preferred editor
nano agents/example.yml
# or  
code agents/example.yml
```

Change the model from `gpt-4.1-nano` to `gpt-4`:

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4  # Changed from gpt-4.1-nano
```

Restart your server:

```bash
uv run xaibo dev
```

Test the same question with the new model:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in simple terms"}
    ]
  }'
```

Notice how you get a different (likely more detailed) response, but your tools still work exactly the same way. This demonstrates **protocol-based modularity** - you changed the LLM implementation without affecting any other components.

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

Change the configuration to use a mock LLM:

```yaml
id: mock-example
description: An example agent using a mock LLM for testing
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: llm
    config:
      responses:
        - content: "I'm a mock LLM! I'll help you with that."
          tool_calls:
            - function: current_time
              arguments: {}
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
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
      {"role": "user", "content": "Any question at all"}
    ]
  }'
```

You'll see the mock response and it will still call the `current_time` tool! This demonstrates how:

- **Protocols enable testing**: You can test your agent logic without real LLM costs
- **Behavior is predictable**: Mock responses help verify your agent works correctly
- **Tools still work**: The protocol interface ensures compatibility

## Step 5: Understanding the Exchange System

The **exchange system** is what connects modules together. Let's make this explicit in your configuration. Edit your `agents/example.yml`:

```bash
nano agents/example.yml
```

Add an explicit exchange section:

```yaml
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
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
    protocol: ToolsProtocol
    provider: python-tools
```

This makes explicit what Xaibo was doing automatically:

- **Entry point**: Messages go to the orchestrator first
- **LLM connection**: Orchestrator uses the LLM for language understanding
- **Tool connection**: Orchestrator can access tools when needed

## Step 6: Experiment with Multiple Tool Providers

Let's see how the exchange system enables multiple tool providers. First, create a new tool file:

```bash
# Create a new tool file
cat > tools/math_tools.py << 'EOF'
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
EOF
```

Now modify your agent to use both tool providers:

```bash
nano agents/example.yml
```

Update the modules and exchange sections:

```yaml
id: example
description: An example agent that uses multiple tool providers
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - id: basic-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.example]
  - id: math-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.math_tools]
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
  # Connect to multiple tool providers
  - module: orchestrator
    protocol: ToolsProtocol
    provider: [basic-tools, math-tools]  # List of providers!
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

Your agent now has access to tools from both providers! This demonstrates:

- **Multiple providers**: One module can depend on multiple implementations
- **Tool aggregation**: All tools appear as one unified set to the agent
- **Flexible composition**: Easy to add or remove tool sets

## Step 7: Understanding Protocol Benefits

Through your experiments, you've seen how protocols enable:

**🔄 Easy Swapping**

- Changed from GPT-3.5 to GPT-4 without touching other components
- Switched to mock LLM for testing
- All tools continued working unchanged

**🧩 Flexible Composition**  

- Added multiple tool providers
- Connected components through exchanges
- Mixed and matched implementations

**🧪 Better Testing**

- Used mock LLM for predictable responses
- Isolated components for testing
- Verified behavior without external dependencies

**📈 Extensibility**

- Added new tools without changing existing code
- Created new tool providers easily
- Extended functionality through configuration

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

- LLM modules handle language understanding
- Tool modules provide capabilities  
- Orchestrators manage workflow

**Protocol-Based Interfaces**: Modules communicate through standardized protocols

- Clear contracts between components
- Easy to test and mock
- Enables component substitution

**Dependency Injection**: Modules declare what they need, not how to get it

- Flexible wiring through exchanges
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
- **[Reference Documentation](../reference/index.md)**: Detailed API and configuration reference
- **[Examples](https://github.com/xpressai/xaibo/tree/main/examples)**: Real-world agent implementations

Ready to build something amazing with Xaibo? The framework's modular architecture gives you the flexibility to create agents that fit your exact needs!