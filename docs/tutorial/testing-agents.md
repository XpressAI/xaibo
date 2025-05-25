# Testing Agents with the Xaibo Framework

## What You'll Learn

In this tutorial, you'll learn to test AI agents by building a simple echo bot and progressively adding testing capabilities. By the end, you'll understand how to:

- Replace agent components with test doubles using [`ConfigOverrides`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L51)
- Capture and verify agent behavior using events
- Test real agent scenarios with confidence

## Why This Matters

Testing AI agents is challenging because they depend on external services like LLM APIs that are slow, expensive, and unpredictable. Xaibo solves this through **dependency injection** - you can replace any component with a test version that behaves exactly how you need.

## Prerequisites

- Basic Python and pytest knowledge
- Xaibo framework installed
- Understanding of [agent configuration](./getting-started.md)

## Step 1: Create a Simple Echo Agent

Let's start with the simplest possible agent - one that echoes back what you say with a prefix.

Create `echo_agent.yaml`:

```yaml
id: echo-test-agent
modules:
  - module: xaibo_examples.echo.Echo
    id: echo
    config:
      prefix: "You said: "
```

This agent has one module that implements [`TextMessageHandlerProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/message_handlers.py) and depends on [`ResponseProtocol`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/response.py) to send responses.

## Step 2: Test the Agent Normally

First, let's see how the agent works without any testing modifications:

```python
import pytest
from pathlib import Path
from xaibo import Registry, AgentConfig

@pytest.mark.asyncio
async def test_echo_agent_basic():
    """Test the echo agent with default components"""
    
    # Load the agent configuration
    config_path = Path(__file__).parent / "echo_agent.yaml"
    with open(config_path) as f:
        config = AgentConfig.from_yaml(f.read())
    
    # Create registry and register agent
    registry = Registry()
    registry.register_agent(config)
    
    # Get agent instance
    agent = registry.get_agent("echo-test-agent")
    
    # Test it
    response = await agent.handle_text("Hello world")
    assert response.text == "You said: Hello world"
```

This works, but it uses the real response handler. Let's learn to control it.

## Step 3: Replace Components with Mocks

The key insight is that we can replace any component with our own implementation. Let's replace the response handler with one we can inspect:

```python
from xaibo import ConfigOverrides
from xaibo.core.models import Response

@pytest.mark.asyncio
async def test_echo_agent_with_mock():
    """Test the echo agent with a controllable response handler"""
    
    # Create a mock response handler we can inspect
    class MockResponse:
        def __init__(self):
            self.last_response = None
        
        async def respond_text(self, text: str) -> None:
            self.last_response = text
        
        async def get_response(self) -> Response:
            return Response(self.last_response)
    
    mock_response = MockResponse()
    
    # Load agent with our mock
    registry = Registry()
    registry.register_agent(config)
    
    agent = registry.get_agent_with("echo-test-agent", ConfigOverrides(
        instances={'__response__': mock_response}
    ))
    
    # Test it
    await agent.handle_text("Hello world")
    
    # Now we can verify what the agent tried to send
    assert mock_response.last_response == "You said: Hello world"
```

**Key concept**: [`ConfigOverrides`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L51) lets you replace any module by its ID. The `__response__` module is automatically added to every agent.

## Step 4: Capture What Actually Happened

Sometimes you want to see exactly what methods were called and in what order. Xaibo captures this automatically through events:

```python
from xaibo.core.models import EventType

@pytest.mark.asyncio
async def test_echo_agent_with_events():
    """Test the echo agent and capture all interactions"""
    
    # Collect all events
    collected_events = []
    def collect_event(event):
        collected_events.append(event)
    
    registry = Registry()
    registry.register_agent(config)
    
    # Add event listener when getting the agent
    agent = registry.get_agent_with(
        "echo-test-agent", 
        None,  # No overrides this time
        additional_event_listeners=[("", collect_event)]  # "" means capture all
    )
    
    # Test it
    await agent.handle_text("Hello world")
    
    # Verify we captured the interactions
    call_events = [e for e in collected_events if e.event_type == EventType.CALL]
    
    # Should have captured the handle_text call
    handle_text_calls = [e for e in call_events if e.method_name == "handle_text"]
    assert len(handle_text_calls) > 0
    assert handle_text_calls[0].arguments["args"][0] == "Hello world"
```

**Key concept**: Events show you exactly what happened inside your agent, which is invaluable for understanding complex behaviors.

## Step 5: Test an Agent with an LLM

Now let's test something more realistic - an agent that uses a language model. We'll use [`MockLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/mock.py#L12) to control what the LLM "says":

```python
from xaibo.primitives.modules.llm.mock import MockLLM
from xaibo.core.models.llm import LLMResponse, LLMUsage

@pytest.mark.asyncio
async def test_agent_with_llm():
    """Test an agent that uses an LLM with controlled responses"""
    
    # Create an LLM that gives us exactly the responses we want
    mock_llm = MockLLM({
        "responses": [
            LLMResponse(
                content="I'm a helpful assistant ready to help!",
                usage=LLMUsage(prompt_tokens=10, completion_tokens=8, total_tokens=18)
            ).model_dump()
        ]
    })
    
    # Also mock the response so we can verify what gets sent
    class MockResponse:
        def __init__(self):
            self.responses = []
        
        async def respond_text(self, text: str) -> None:
            self.responses.append(text)
    
    mock_response = MockResponse()
    
    # Replace both the LLM and response handler
    overrides = ConfigOverrides(
        instances={
            'llm': mock_llm,
            '__response__': mock_response
        }
    )
    
    # Assume we have an agent that uses an LLM
    agent = registry.get_agent_with("llm-agent", overrides)
    
    await agent.handle_text("Hello")
    
    # Verify the mock LLM's response made it through
    assert len(mock_response.responses) > 0
    assert "helpful assistant" in mock_response.responses[0]
```

**Key concept**: [`MockLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/mock.py#L12) cycles through configured responses, making conversations predictable and testable.

## Step 6: Test a Complete Conversation

Let's put it all together and test a multi-turn conversation:

```python
@pytest.mark.asyncio
async def test_conversation_flow():
    """Test a complete conversation with multiple exchanges"""
    
    # Set up an LLM with multiple responses
    mock_llm = MockLLM({
        "responses": [
            LLMResponse(content="Hello! How can I help you?").model_dump(),
            LLMResponse(content="I'd be happy to help with that.").model_dump(),
            LLMResponse(content="You're welcome!").model_dump()
        ]
    })
    
    # Track all responses
    class MockResponse:
        def __init__(self):
            self.responses = []
        
        async def respond_text(self, text: str) -> None:
            self.responses.append(text)
    
    mock_response = MockResponse()
    
    # Track all events too
    collected_events = []
    def collect_event(event):
        collected_events.append(event)
    
    overrides = ConfigOverrides(
        instances={
            'llm': mock_llm,
            '__response__': mock_response
        }
    )
    
    agent = registry.get_agent_with(
        "conversational-agent", 
        overrides,
        additional_event_listeners=[("", collect_event)]
    )
    
    # Have a conversation
    await agent.handle_text("Hello")
    await agent.handle_text("I need help")
    await agent.handle_text("Thank you")
    
    # Verify we got three responses
    assert len(mock_response.responses) == 3
    assert "How can I help" in mock_response.responses[0]
    assert "happy to help" in mock_response.responses[1]
    assert "welcome" in mock_response.responses[2]
    
    # Verify the LLM was called three times
    llm_calls = [e for e in collected_events 
                 if e.method_name == "generate" and e.event_type == EventType.CALL]
    assert len(llm_calls) == 3
```

## What You've Learned

You now understand the core pattern for testing Xaibo agents:

1. **Create mock implementations** of the protocols your agent uses
2. **Use [`ConfigOverrides`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/config.py#L51)** to inject your mocks by module ID
3. **Capture events** to verify the exact sequence of interactions
4. **Assert on mock state** to verify your agent behaved correctly

## Key Benefits

This approach gives you:

- **Fast tests** - no real API calls
- **Reliable tests** - controlled, predictable responses  
- **Detailed verification** - see exactly what your agent did
- **Easy debugging** - step through interactions with full visibility

## Next Steps

- Try testing an agent with memory by mocking the memory module
- Test error scenarios by making your mocks throw exceptions
- Explore the [reference documentation](../reference/index.md) for more advanced testing patterns

The key insight is that Xaibo's dependency injection makes every component replaceable, turning complex AI agents into testable, reliable software.