from pathlib import Path
from xaibo import AgentConfig

def test_auto_config_text_handler():
    """Test that text handler is automatically configured when unambiguous"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
        
    # Verify text handler exchange was added
    text_handler_exchanges = [ex for ex in config.exchange 
                            if ex.module == "__entry__" 
                            and ex.protocol == "TextMessageHandlerProtocol"]
    
    assert len(text_handler_exchanges) == 1
    text_exchange = text_handler_exchanges[0]
    
    # Echo module should be the provider
    assert text_exchange.provider == "echo"

def test_auto_config_response():
    """Test that response module is automatically added"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
        
    # Verify response module was added
    response_modules = [m for m in config.modules if m.id == "__response__"]
    assert len(response_modules) == 1
    
    response = response_modules[0]
    assert response.module == "xaibo.primitives.modules.ResponseHandler"
    assert response.provides == ["ResponseProtocol"]

def test_auto_config_uses_field():
    """Test that uses field is correctly populated for modules that require protocols"""
    # Find the resources directory relative to this test file
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources"
    
    with open(resources_dir / "yaml" / "echo.yaml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
        
    # Find the echo module
    echo_modules = [m for m in config.modules if m.id == "echo"]
    assert len(echo_modules) == 1
    
    echo_module = echo_modules[0]
    
    # Verify that the ResponseProtocol is in the uses field
    assert echo_module.uses is not None
    assert "ResponseProtocol" in echo_module.uses
    
    # Verify exchange configuration was added for the echo module
    response_exchanges = [ex for ex in config.exchange 
                         if ex.module == "echo" 
                         and ex.protocol == "ResponseProtocol"]
    
    assert len(response_exchanges) == 1
    assert response_exchanges[0].provider == "__response__"
