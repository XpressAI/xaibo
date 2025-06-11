
import logging

import pytest
import os
from pathlib import Path
from xaibo import AgentConfig, Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.primitives.modules.conversation import SimpleConversation

from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_example_agent():
     # Load the stressing tool user config
    with open(r"./agents/example.yml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent_with("example", ConfigOverrides(
        instances={'history': SimpleConversation()},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ))
    
    # Test with a prompt that should trigger the current_time tool
    response = await agent.handle_text("What time is it right now?")
    
    # Verify response contains time information
    assert "time" in response.text.lower()
