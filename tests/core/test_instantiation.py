import pytest
from pathlib import Path
from xaibo import AgentConfig, Registry, ConfigOverrides, ModuleConfig, ExchangeConfig
from xaibo.core import Exchange

from xaibo.core.models import Response, EventType


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

        async def get_response(self) -> Response:
            return Response(self.last_response)
    
    mock_response = MockResponse()

    # Get agent with mock response handler
    agent = registry.get_agent_with("echo-agent-minimal", ConfigOverrides(
        instances={
            '__response__': mock_response
        }
    ))
    
    # Test text handling
    test_message = "Hello world"
    await agent.handle_text(test_message)
    
    # Verify echo response
    assert mock_response.last_response == "You said: " + test_message

# Create a dependency module
class DependencyModule:
    def __init__(self, config=None):
        pass

    async def do_something(self):
        return "dependency called"

# Create a module that requires a specific field name
class ModuleWithNamedDependency:
    def __init__(self, specific_dependency: DependencyModule, config=None):
        self.dependency = specific_dependency

    async def get_dependency(self):
        return self.dependency

@pytest.mark.asyncio
async def test_instantiate_with_field_name_exchange():
    """Test instantiating an agent with field_name in ExchangeConfig"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Add modules to config
    config.modules.append(ModuleConfig(
        module=f"{ModuleWithNamedDependency.__module__}.ModuleWithNamedDependency",
        id="named_dependency_module"
    ))
    
    config.modules.append(ModuleConfig(
        module=f"{DependencyModule.__module__}.DependencyModule",
        id="dependency_module"
    ))
    
    # Add exchange config with field_name
    config.exchange.append(ExchangeConfig(
        module="named_dependency_module",
        field_name="specific_dependency",
        protocol="DependencyModule",
        provider="dependency_module"
    ))
    
    # Register and get agent
    registry = Registry()
    registry.register_agent(config)
    agent = registry.get_agent("echo-agent-minimal")
    
    # Get the module and test the dependency injection
    module = agent.exchange.get_module("named_dependency_module", "test")
    dependency_result = await module.get_dependency()
    dependency_method_result = await dependency_result.do_something()
    
    assert dependency_method_result == "dependency called"

@pytest.mark.asyncio
async def test_instantiate_with_debug_listener():
    """Test instantiating an agent with a debug event listener"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create a registry with debug listener
    registry = Registry()
    
    # Create a simple event collector
    collected_events = []
    def collect_event(event):
        collected_events.append(event)
    
    # Register the agent with event listener
    registry.register_agent(config)
    
    # Get agent instance
    agent = registry.get_agent_with("echo-agent-minimal", None, additional_event_listeners=[("", collect_event)])
    
    # Test text handling
    response = await agent.handle_text("Hello world")
    
    # Verify events were collected
    assert len(collected_events) > 0
    
    # Verify we have both CALL and RESULT events
    call_events = [e for e in collected_events if e.event_type == EventType.CALL]
    result_events = [e for e in collected_events if e.event_type == EventType.RESULT]
    
    assert len(call_events) > 0
    assert len(result_events) > 0
    
    # Verify we captured the handle_text call
    handle_text_calls = [e for e in call_events if e.method_name == "handle_text"]
    assert len(handle_text_calls) > 0
    assert handle_text_calls[0].arguments["args"][0] == "Hello world"



# Create a simple dependency module
class DependencyModuleWithId:
    def __init__(self, config=None):
        self.id = config.get("id", "default")
        
    async def get_id(self):
        return self.id

# Create a simple module that requires a list of dependencies
class ListDependencyModule:
    def __init__(self, dependencies: list[DependencyModuleWithId], config=None):
        self.dependencies = dependencies
        
    async def get_dependencies(self):
        return self.dependencies

@pytest.mark.asyncio
async def test_list_type_dependency():
    """Test instantiating a module with a list type dependency"""
    
    # Create configuration with multiple dependencies
    config = AgentConfig(
        id="list-dependency-test",
        modules=[
            ModuleConfig(
                id="list_module",
                module=f"{ListDependencyModule.__module__}.ListDependencyModule"
            ),
            ModuleConfig(
                id="dep1",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep1"}
            ),
            ModuleConfig(
                id="dep2",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep2"}
            ),
            ModuleConfig(
                id="dep3",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep3"}
            )
        ],
        exchange=[
            # Configure the list_module to use multiple dependencies
            ExchangeConfig(
                module="list_module",
                protocol="list",
                field_name="dependencies",
                provider=["dep1", "dep2", "dep3"]
            ),
            # Set the entry module
            ExchangeConfig(
                module="__entry__",
                protocol="ListDependencyModule",
                provider="list_module"
            )
        ]
    )
    
    # Create exchange with the config
    exchange = Exchange(config=config)
    
    # Get the module and test the list dependency injection
    module = exchange.get_module("list_module", "test")
    dependencies = await module.get_dependencies()
    
    # Verify we have all three dependencies
    assert len(dependencies) == 3
    
    # Verify each dependency has the correct ID
    dependency_ids = [await dep.get_id() for dep in dependencies]
    assert "dep1" in dependency_ids
    assert "dep2" in dependency_ids
    assert "dep3" in dependency_ids

@pytest.mark.asyncio
async def test_list_dependency_with_repeated_config():
    """Test that list dependencies work with repeated config for the same protocol."""
    # Create a config with list dependencies but no field_name
    config = AgentConfig(
        id='test_agent',
        modules=[
            ModuleConfig(
                id="list_module",
                module=f"{ListDependencyModule.__module__}.ListDependencyModule"
            ),
            ModuleConfig(
                id="dep1",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep1"}
            ),
            ModuleConfig(
                id="dep2",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep2"}
            )
        ],
        exchange=[
            # Configure the list_module to use multiple dependencies without field_name
            ExchangeConfig(
                module="list_module",
                protocol="DependencyModuleWithId",
                provider="dep1"
            ),
            ExchangeConfig(
                module="list_module",
                protocol="DependencyModuleWithId",
                provider="dep2"
            ),
            # Set the entry module
            ExchangeConfig(
                module="__entry__",
                protocol="ListDependencyModule",
                provider="list_module"
            )
        ]
    )
    
    # Create exchange with the config
    exchange = Exchange(config=config)
    
    # Get the module and test the list dependency injection
    module = exchange.get_module("list_module", "test")
    dependencies = await module.get_dependencies()
    
    # Verify we have both dependencies
    assert len(dependencies) == 2
    
    # Verify each dependency has the correct ID
    dependency_ids = [await dep.get_id() for dep in dependencies]
    assert "dep1" in dependency_ids
    assert "dep2" in dependency_ids

@pytest.mark.asyncio
async def test_list_dependency_without_field_name():
    """Test that list dependencies work without specifying a field_name."""
    # Create a config with list dependencies but no field_name
    config = AgentConfig(
        id='test_agent',
        modules=[
            ModuleConfig(
                id="list_module",
                module=f"{ListDependencyModule.__module__}.ListDependencyModule"
            ),
            ModuleConfig(
                id="dep1",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep1"}
            ),
            ModuleConfig(
                id="dep2",
                module=f"{DependencyModuleWithId.__module__}.DependencyModuleWithId",
                config={"id": "dep2"}
            )
        ],
        exchange=[
            # Configure the list_module to use multiple dependencies without field_name
            ExchangeConfig(
                module="list_module",
                protocol="DependencyModuleWithId",
                provider=["dep1", "dep2"]
            ),
            # Set the entry module
            ExchangeConfig(
                module="__entry__",
                protocol="ListDependencyModule",
                provider="list_module"
            )
        ]
    )

    # Create exchange with the config
    exchange = Exchange(config=config)

    # Get the module and test the list dependency injection
    module = exchange.get_module("list_module", "test")
    dependencies = await module.get_dependencies()

    # Verify we have both dependencies
    assert len(dependencies) == 2

    # Verify each dependency has the correct ID
    dependency_ids = [await dep.get_id() for dep in dependencies]
    assert "dep1" in dependency_ids
    assert "dep2" in dependency_ids
