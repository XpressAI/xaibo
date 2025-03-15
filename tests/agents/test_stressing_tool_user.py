import logging

import pytest
import os
from pathlib import Path
from xaibo import AgentConfig, Xaibo
from xaibo.core.models.response import Response


@pytest.mark.asyncio
async def test_stressing_tool_user_instantiation():
    """Test instantiating a stressing tool user agent"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the stressing tool user config
    with open(resources_dir / "yaml" / "stressing_tool_user.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)

    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent("minimal-tool-user")
    
    # Verify agent was created successfully
    assert agent is not None
    assert agent.id == "minimal-tool-user"


@pytest.mark.asyncio
async def test_stressing_tool_user_current_time(caplog):
    """Test stressing tool user with current_time tool"""
    caplog.set_level(logging.DEBUG, 'xaibo.events')

    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the stressing tool user config
    with open(resources_dir / "yaml" / "stressing_tool_user.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent("minimal-tool-user")
    
    # Test with a prompt that should trigger the current_time tool
    response = await agent.handle_text("What time is it right now?")
    
    # Verify response contains time information
    assert isinstance(response, Response)
    assert "time" in response.text.lower()


@pytest.mark.asyncio
async def test_stressing_tool_user_calendar():
    """Test stressing tool user with calendar tool"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the stressing tool user config
    with open(resources_dir / "yaml" / "stressing_tool_user.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent("minimal-tool-user")
    
    # Get today's date in YYYY-MM-DD format
    from datetime import datetime
    today = datetime.today().strftime("%Y-%m-%d")
    
    # Test with a prompt that should trigger the calendar tool
    response = await agent.handle_text(f"What's on my calendar for {today}?")
    
    # Verify response contains calendar information
    assert isinstance(response, Response)
    assert "standup" in response.text.lower() or "focus time" in response.text.lower()


@pytest.mark.asyncio
async def test_stressing_tool_user_error_handling():
    """Test stressing tool user handles tool errors gracefully"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")


    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the stressing tool user config
    with open(resources_dir / "yaml" / "stressing_tool_user.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent("minimal-tool-user")
    
    # Test with a prompt that should trigger the weather tool with Germany (which raises an exception)
    response = await agent.handle_text("What's the weather in Berlin, Germany?")
    
    # Verify agent handled the error and still provided a response
    assert isinstance(response, Response)
    assert response.text is not None
    assert len(response.text) > 0
