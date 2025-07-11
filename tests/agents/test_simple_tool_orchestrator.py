import logging

import pytest
import os
from pathlib import Path


from xaibo import AgentConfig, Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.core.models.response import Response
from xaibo.primitives.modules.conversation import SimpleConversation


@pytest.fixture
def empty_conversation():
    return SimpleConversation()

@pytest.mark.asyncio
async def test_simple_tool_orchestrator_instantiation(empty_conversation):
    """Test instantiating a simple tool orchestrator agent"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the simple tool orchestrator config
    with open(resources_dir / "yaml" / "simple_tool_orchestrator.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)

    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent_with("minimal-tool-user", ConfigOverrides(
        instances={'history': empty_conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ))
    
    # Verify agent was created successfully
    assert agent is not None
    assert agent.id == "minimal-tool-user"


@pytest.mark.asyncio
async def test_simple_tool_orchestrator_current_time(caplog, empty_conversation):
    """Test simple tool orchestrator with current_time tool"""
    caplog.set_level(logging.DEBUG, 'xaibo.events')

    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the simple tool orchestrator config
    with open(resources_dir / "yaml" / "simple_tool_orchestrator.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent_with("minimal-tool-user", ConfigOverrides(
        instances={'history': empty_conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ))
    # Test with a prompt that should trigger the current_time tool
    response = await agent.handle_text("What time is it right now?")
    
    # Verify response contains time information
    assert isinstance(response, Response)
    assert "time" in response.text.lower()


@pytest.mark.asyncio
async def test_simple_tool_orchestrator_calendar(empty_conversation):
    """Test simple tool orchestrator with calendar tool"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the simple tool orchestrator config
    with open(resources_dir / "yaml" / "simple_tool_orchestrator.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent_with("minimal-tool-user", ConfigOverrides(
        instances={'history': empty_conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ))
    # Get today's date in YYYY-MM-DD format
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    
    # Test with a prompt that should trigger the calendar tool
    response = await agent.handle_text(f"What's on my calendar for {today}?")
    
    # Verify response contains calendar information
    assert isinstance(response, Response)
    assert "standup" in response.text.lower() or "focus time" in response.text.lower()


@pytest.mark.asyncio
async def test_simple_tool_orchestrator_time_and_calendar(empty_conversation):
    """Test simple tool orchestrator with time and calendar tool"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"

    # Load the simple tool orchestrator config
    with open(resources_dir / "yaml" / "simple_tool_orchestrator.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)

    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)

    events = []
    def collect_events(event):
        events.append(event)

    # Get agent instance
    agent = xaibo.get_agent_with("minimal-tool-user", ConfigOverrides(
        instances={'history': empty_conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ), [
        ("", collect_events)
    ])

    # Test with a prompt that should trigger the calendar tool
    response = await agent.handle_text(f"What's on my calendar for today?")

    # Verify response contains calendar information
    assert isinstance(response, Response)
    assert "standup" in response.text.lower() or "focus time" in response.text.lower()

@pytest.mark.asyncio
async def test_simple_tool_orchestrator_error_handling(empty_conversation):
    """Test simple tool orchestrator handles tool errors gracefully"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")


    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the simple tool orchestrator config
    with open(resources_dir / "yaml" / "simple_tool_orchestrator.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent_with("minimal-tool-user", ConfigOverrides(
        instances={'history': empty_conversation},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ))
    # Test with a prompt that should trigger the weather tool with Germany (which raises an exception)
    response = await agent.handle_text("What's the weather in Berlin, Germany?")
    
    # Verify agent handled the error and still provided a response
    assert isinstance(response, Response)
    assert response.text is not None
    assert len(response.text) > 0
