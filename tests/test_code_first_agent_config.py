import pytest
from xaibo import AgentConfig, Registry
from xaibo.core.config import ModuleConfig, ExchangeConfig
from xaibo.primitives.modules import ResponseHandler
from xaibo.core.protocols import ResponseProtocol, TextMessageHandlerProtocol


def test_code_first_minimal():
    """Test creating a minimal agent config in code, equivalent to echo.yaml"""
    config = AgentConfig(
        id="echo-agent-minimal",
        modules=[
            ModuleConfig(
                module="xaibo-examples.echo.Echo",
                id="echo",
                config={
                    "prefix": "You said: "
                }
            )
        ]
    )
    
    # Verify the config matches what we'd get from YAML
    assert config.id == "echo-agent-minimal"
    assert len(config.modules) == 2  # Echo module + implicit ResponseHandler
    
    echo_module = next(m for m in config.modules if m.id == "echo")
    assert echo_module.module == "xaibo-examples.echo.Echo"
    assert echo_module.config["prefix"] == "You said: "
    
    response_module = next(m for m in config.modules if m.id == "__response__")
    assert response_module.module == "xaibo.primitives.modules.ResponseHandler"
    assert response_module.provides == ["ResponseProtocol"]

def test_code_first_minimal_direct_refs():
    """Test creating a minimal agent config in code using direct class references"""
    config = AgentConfig(
        id="echo-agent-minimal",
        modules=[
            ModuleConfig(
                module=Echo,
                id="echo",
                config={
                    "prefix": "You said: "
                }
            )
        ]
    )
    
    # Verify the config matches what we'd get from YAML
    assert config.id == "echo-agent-minimal"
    assert len(config.modules) == 2  # Echo module + implicit ResponseHandler
    
    echo_module = next(m for m in config.modules if m.id == "echo")
    assert echo_module.module == "test_code_first_agent_config.Echo"
    assert echo_module.config["prefix"] == "You said: "
    
    response_module = next(m for m in config.modules if m.id == "__response__")
    assert response_module.module == "xaibo.primitives.modules.ResponseHandler"
    assert response_module.provides == ["ResponseProtocol"]

def test_code_first_complete():
    """Test creating a complete agent config in code, equivalent to echo_complete.yaml"""
    config = AgentConfig(
        id="echo-agent",
        modules=[
            ModuleConfig(
                module="xaibo-examples.echo.Echo",
                id="echo",
                provides=["TextMessageHandlerProtocol"],
                uses=["ResponseProtocol"],
                config={
                    "prefix": "You said: "
                }
            ),
            ModuleConfig(
                module="xaibo.primitives.modules.ResponseHandler",
                id="__response__",
                provides=["ResponseProtocol"]
            )
        ],
        exchange=[
            ExchangeConfig(
                module="__entry__",
                protocol="TextMessageHandlerProtocol",
                provider="echo"
            ),
            ExchangeConfig(
                module="echo",
                protocol="ResponseProtocol",
                provider="__response__"
            )
        ]
    )
    
    # Verify the config matches what we'd get from YAML
    assert config.id == "echo-agent"
    assert len(config.modules) == 2
    
    echo_module = next(m for m in config.modules if m.id == "echo")
    assert echo_module.module == "xaibo-examples.echo.Echo"
    assert echo_module.provides == ["TextMessageHandlerProtocol"]
    assert echo_module.uses == ["ResponseProtocol"]
    assert echo_module.config["prefix"] == "You said: "
    
    response_module = next(m for m in config.modules if m.id == "__response__")
    assert response_module.module == "xaibo.primitives.modules.ResponseHandler"
    assert response_module.provides == ["ResponseProtocol"]
    
    # Verify exchange configuration
    entry_exchange = next(ex for ex in config.exchange if ex.module == "__entry__")
    assert entry_exchange.protocol == "TextMessageHandlerProtocol"
    assert entry_exchange.provider == "echo"
    
    echo_exchange = next(ex for ex in config.exchange if ex.module == "echo")
    assert echo_exchange.protocol == "ResponseProtocol" 
    assert echo_exchange.provider == "__response__"

def test_code_first_complete_direct_refs():
    """Test creating a complete agent config in code using direct class references"""
    config = AgentConfig(
        id="echo-agent",
        modules=[
            ModuleConfig(
                module=Echo,
                id="echo",
                provides=[TextMessageHandlerProtocol],
                uses=[ResponseProtocol],
                config={
                    "prefix": "You said: "
                }
            ),
            ModuleConfig(
                module=ResponseHandler,
                id="__response__",
                provides=[ResponseProtocol]
            )
        ],
        exchange=[
            ExchangeConfig(
                module="__entry__",
                protocol=TextMessageHandlerProtocol,
                provider="echo"
            ),
            ExchangeConfig(
                module="echo",
                protocol=ResponseProtocol,
                provider="__response__"
            )
        ]
    )
    
    # Verify the config matches what we'd get from YAML
    assert config.id == "echo-agent"
    assert len(config.modules) == 2
    
    echo_module = next(m for m in config.modules if m.id == "echo")
    assert echo_module.module == "test_code_first_agent_config.Echo"
    assert echo_module.provides == ["TextMessageHandlerProtocol"]
    assert echo_module.uses == ["ResponseProtocol"]
    assert echo_module.config["prefix"] == "You said: "
    
    response_module = next(m for m in config.modules if m.id == "__response__")
    assert response_module.module == "xaibo.primitives.modules.response.ResponseHandler"
    assert response_module.provides == ["ResponseProtocol"]
    
    # Verify exchange configuration
    entry_exchange = next(ex for ex in config.exchange if ex.module == "__entry__")
    assert entry_exchange.protocol == "TextMessageHandlerProtocol"
    assert entry_exchange.provider == "echo"
    
    echo_exchange = next(ex for ex in config.exchange if ex.module == "echo")
    assert echo_exchange.protocol == "ResponseProtocol" 
    assert echo_exchange.provider == "__response__"

@pytest.mark.asyncio
async def test_code_first_agent_execution():
    """Test that a code-first agent executes correctly"""
    config = AgentConfig(
        id="echo-agent-test",
        modules=[
            ModuleConfig(
                module="xaibo-examples.echo.Echo",
                id="echo",
                config={
                    "prefix": "You said: "
                }
            )
        ]
    )
    
    registry = Registry()
    registry.register_agent(config)
    
    agent = registry.get_agent("echo-agent-test")
    response = await agent.handle_text("Hello world")
    
    assert response.text == "You said: Hello world"

@pytest.mark.asyncio
async def test_code_first_agent_execution_direct_refs():
    """Test that a code-first agent executes correctly using direct class references"""
    config = AgentConfig(
        id="echo-agent-test",
        modules=[
            ModuleConfig(
                module=Echo,
                id="echo",
                config={
                    "prefix": "You said: "
                }
            )
        ]
    )
    
    registry = Registry()
    registry.register_agent(config)
    
    agent = registry.get_agent("echo-agent-test")
    response = await agent.handle_text("Hello world")
    
    assert response.text == "You said: Hello world"


class Echo(TextMessageHandlerProtocol):
    """A simple echo module that repeats back the received text message with a prefix."""
    
    @classmethod
    def provides(cls):
        return [TextMessageHandlerProtocol]

    def __init__(self, response: ResponseProtocol, config: dict = None):
        """Initialize the Echo module.
        
        Args:
            response: Response handler for sending messages (required)
            config: Configuration dictionary that may contain a 'prefix' key
        """
        self.config: dict = config or {}
        self.prefix: str = self.config.get("prefix", "")
        self.response: ResponseProtocol = response
    
    async def handle_text(self, text: str) -> None:
        """Handle an incoming text message by echoing it back with a prefix.
        
        Args:
            text: The text message to handle
        """
        await self.response.respond_text(f"{self.prefix}{text}")