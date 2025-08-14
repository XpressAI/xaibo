# How to embed xaibo into your application without a server

This guide shows you how to integrate xaibo agents directly into your Python application without running a separate server component.

## Prerequisites

- Python 3.8 or higher
- xaibo installed (`pip install xaibo`)
- An OpenAI API key set as environment variable

## Step 1: Create your agent configuration

Define your agent in a YAML file or create it programmatically:

```yaml
# agent_config.yaml
id: my-assistant
description: An assistant for my application
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4o-mini
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: ['my_app.tools']  # Your custom tools package
  - module: xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator
    id: orchestrator
    config:
      system_prompt: |
        You are a helpful assistant embedded in the application.
```

## Step 2: Initialize xaibo and register your agent

```python
from xaibo import AgentConfig, Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.primitives.modules.conversation import SimpleConversation

# Load configuration
with open('agent_config.yaml') as f:
    config = AgentConfig.from_yaml(f.read())

# Create xaibo instance and register agent
xaibo = Xaibo()
xaibo.register_agent(config)
```

## Step 3: Create an agent instance with conversation history

```python
# Create conversation history container
conversation = SimpleConversation()

# Get agent instance with conversation tracking
agent = xaibo.get_agent_with(
    "my-assistant",
    ConfigOverrides(
        instances={'history': conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    )
)
```

## Step 4: Process user input and get responses

```python
async def process_user_message(message: str):
    response = await agent.handle_text(message)
    return response.text

# Example usage
import asyncio

async def main():
    # Process a user message
    result = await process_user_message("What time is it?")
    print(result)
    
    # Continue the conversation
    result = await process_user_message("What about in Tokyo?")
    print(result)

# Run the async function
asyncio.run(main())
```

## Optional: Add event listeners

Monitor agent activity by adding event listeners:

```python
events = []

def collect_events(event):
    events.append(event)
    print(f"Event: {event.type}")

# Create agent with event listener
agent = xaibo.get_agent_with(
    "my-assistant",
    ConfigOverrides(
        instances={'history': conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ),
    [("", collect_events)]  # Empty string captures all events
)
```

## Alternative: Code-first configuration

Instead of YAML, configure your agent entirely in code:

```python
from xaibo import AgentConfig, ModuleConfig

config = AgentConfig(
    id="my-assistant",
    description="An embedded assistant",
    modules=[
        ModuleConfig(
            module="xaibo.primitives.modules.llm.OpenAILLM",
            id="llm",
            config={"model": "gpt-4o-mini"}
        ),
        ModuleConfig(
            module="xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator",
            id="orchestrator",
            config={"system_prompt": "You are a helpful assistant."}
        )
    ]
)
```

## Integration patterns

### Pattern 1: Singleton agent

```python
class AgentManager:
    _instance = None
    _agent = None
    
    @classmethod
    def get_agent(cls):
        if cls._agent is None:
            xaibo = Xaibo()
            xaibo.register_agent(config)
            cls._agent = xaibo.get_agent_with(
                "my-assistant",
                ConfigOverrides(
                    instances={'history': SimpleConversation()},
                    exchange=[ExchangeConfig(
                        protocol='ConversationHistoryProtocol',
                        provider='history'
                    )]
                )
            )
        return cls._agent
```

### Pattern 2: Per-user agents

```python
class UserAgentFactory:
    def __init__(self):
        self.xaibo = Xaibo()
        self.xaibo.register_agent(config)
    
    def create_agent_for_user(self, user_id: str):
        # Each user gets their own conversation history
        conversation = SimpleConversation()
        
        return self.xaibo.get_agent_with(
            "my-assistant",
            ConfigOverrides(
                instances={'history': conversation},
                exchange=[ExchangeConfig(
                    protocol='ConversationHistoryProtocol',
                    provider='history'
                )]
            )
        )
```

## Error handling

Wrap agent calls with appropriate error handling:

```python
from xaibo.core.models.response import Response

async def safe_process_message(agent, message: str):
    try:
        response = await agent.handle_text(message)
        if isinstance(response, Response):
            return response.text
    except Exception as e:
        print(f"Agent error: {e}")
        return "I encountered an error processing your request."
```

## Next steps

- Add custom tools by creating Python functions with proper decorators
- Implement persistent conversation storage
- Add authentication and user management
- Integrate with your application's existing logging system

For more details on creating custom tools, see the [Python tools guide](../tools/python-tools.md).