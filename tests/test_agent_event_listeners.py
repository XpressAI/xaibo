import pytest
from xaibo import AgentConfig, Registry
from xaibo.core.protocols.events import Event, EventType

@pytest.mark.asyncio
async def test_agent_event_listeners():
    """Test event listeners attached to an agent instance"""
    events = []
    
    def event_handler(event: Event):
        events.append(event)
        
    # Load config and create agent
    with open("resources/yaml/echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config)
    
    # Register event listener
    registry.register_event_listener("", event_handler)
    
    # Get agent and handle message
    agent = registry.get_agent("echo-agent-minimal")
    await agent.handle_text("Hello world")

    # Should have generated events for the echo module
    assert len(events) > 0
    assert any(e.module_class == "Echo" for e in events)

@pytest.mark.asyncio
async def test_agent_event_filtering():
    """Test filtering events by agent ID"""
    events = []
    
    def event_handler(event: Event):
        events.append(event)
        
    # Load configs for two agents
    with open("resources/yaml/echo.yaml") as f:
        content = f.read()
        config1 = AgentConfig.from_yaml(content)
        
    with open("resources/yaml/echo_complete.yaml") as f:
        content = f.read()
        config2 = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config1)
    registry.register_agent(config2)
    
    # Register event listener for first agent only
    registry.register_event_listener("", event_handler, agent_id="echo-agent-minimal")
    
    # Get both agents
    agent1 = registry.get_agent("echo-agent-minimal")
    agent2 = registry.get_agent("echo-agent")
    
    # Handle messages with both
    await agent1.handle_text("Hello")  # Should generate events
    await agent2.handle_text("World")  # Should not generate events

    # Should only have events from first agent
    assert len(events) > 0
    assert all(e.agent_id == "echo-agent-minimal" for e in events)

@pytest.mark.asyncio
async def test_agent_event_prefix_filtering():
    """Test filtering events by prefix"""
    events = []
    
    def event_handler(event: Event):
        events.append(event)
        
    # Load config and create agent
    with open("resources/yaml/echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config)
    
    # Register event listener with prefix filter
    registry.register_event_listener("xaibo-examples.echo", event_handler)
    
    # Get agent and handle message
    agent = registry.get_agent("echo-agent-minimal")
    await agent.handle_text("Hello world")


    # Should only have events matching prefix
    assert len(events) > 0
    assert all(e.event_name.startswith("xaibo-examples.echo") for e in events)
