import pytest
from pathlib import Path
from xaibo import AgentConfig, Registry
from xaibo.core.protocols import ResponseProtocol


@pytest.mark.asyncio
async def test_instantiate_complete_echo():
    """Test instantiating an echo agent from complete config"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the complete echo config
    with open(resources_dir / "yaml" / "echo_complete.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    registry = Registry()
    registry.register_agent(config)
    
    # Get agent instance
    agent = registry.get_agent("echo-agent")

    # Test text handling
    response = await agent.handle_text("Hello world")
    assert response.text == "You said: Hello world"

@pytest.mark.asyncio
async def test_instantiate_minimal_echo():
    """Test instantiating an echo agent from minimal config"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    # Load the minimal echo config
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    registry = Registry()
    registry.register_agent(config)
    
    # Get agent instance
    agent = registry.get_agent("echo-agent-minimal")
    
    # Test text handling
    response = await agent.handle_text("Hello world")
    assert response.text == "You said: Hello world"

@pytest.mark.asyncio
async def test_instantiate_with_overrides():
    """Test instantiating an echo agent with custom bindings"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    registry = Registry()
    registry.register_agent(config)

    # Create mock response handler
    class MockResponse:
        async def respond_text(self, text: str) -> None:
            self.last_response = text
    
    mock_response = MockResponse()
    
    # Get agent with mock response handler
    agent = registry.get_agent_with("echo-agent-minimal", {
        ResponseProtocol: mock_response
    })
    
    # Test text handling
    test_message = "Hello world"
    await agent.handle_text(test_message)
    
    # Verify echo response
    assert mock_response.last_response == "You said: " + test_message


@pytest.mark.asyncio
async def test_instantiate_with_string_overrides():
    """Test instantiating an echo agent with custom bindings"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)

    registry = Registry()
    registry.register_agent(config)

    # Create mock response handler
    class MockResponse:
        async def respond_text(self, text: str) -> None:
            self.last_response = text

    mock_response = MockResponse()

    # Get agent with mock response handler
    agent = registry.get_agent_with("echo-agent-minimal", {
        "ResponseProtocol": mock_response
    })

    # Test text handling
    test_message = "Hello world"
    await agent.handle_text(test_message)

    # Verify echo response
    assert mock_response.last_response == "You said: " + test_message