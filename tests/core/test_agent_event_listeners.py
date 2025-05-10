import pytest
from pathlib import Path
from xaibo import AgentConfig, Registry
from xaibo.core.models.events import Event


@pytest.mark.asyncio
async def test_agent_event_listeners():
    """Test event listeners attached to an agent instance"""
    events = []
    
    def event_handler(event: Event):
        events.append(event)
    
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load config and create agent
    with open(resources_dir / "yaml" / "echo.yaml") as f:
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
    
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load configs for two agents
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config1 = AgentConfig.from_yaml(content)
        
    with open(resources_dir / "yaml" / "echo_complete.yaml") as f:
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
    
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load config and create agent
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config)
    
    # Register event listener with prefix filter
    registry.register_event_listener("xaibo_examples.echo", event_handler)
    
    # Get agent and handle message
    agent = registry.get_agent("echo-agent-minimal")
    await agent.handle_text("Hello world")


    # Should only have events matching prefix
    assert len(events) > 0
    assert all(e.event_name.startswith("xaibo_examples.echo") for e in events)

@pytest.mark.asyncio
async def test_additional_event_listeners():
    """Test adding additional event listeners when getting an agent"""
    events = []
    additional_events = []
    
    def event_handler(event: Event):
        events.append(event)
    
    def additional_handler(event: Event):
        additional_events.append(event)
    
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load config and create agent
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config)
    
    # Register global event listener
    registry.register_event_listener("", event_handler)
    
    # Get agent with additional event listener
    additional_listeners = [("", additional_handler)]
    agent = registry.get_agent_with("echo-agent-minimal", None, additional_listeners)
    
    # Handle message
    await agent.handle_text("Hello world")
    
    # Both handlers should have received events
    assert len(events) > 0
    assert len(additional_events) > 0
    
    # Both should have the same events
    assert len(events) == len(additional_events)

@pytest.mark.asyncio
async def test_additional_event_listeners_with_prefix():
    """Test adding additional event listeners with prefix filtering"""
    global_events = []
    echo_events = []
    
    def global_handler(event: Event):
        global_events.append(event)
    
    def echo_handler(event: Event):
        echo_events.append(event)
    
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load config and create agent
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config)
    
    # Get agent with additional event listeners with different prefixes
    additional_listeners = [
        ("", global_handler),
        ("xaibo_examples.echo", echo_handler),
    ]
    
    agent = registry.get_agent_with("echo-agent-minimal", None, additional_listeners)
    
    # Handle message
    await agent.handle_text("Hello world")
    
    # All handlers should have received events
    assert len(global_events) > 0
    assert len(echo_events) > 0
    
    # Global handler should have all events
    assert len(global_events) >= len(echo_events)
    
    # Echo handler should only have echo events
    assert all(e.event_name.startswith("xaibo_examples.echo") for e in echo_events)