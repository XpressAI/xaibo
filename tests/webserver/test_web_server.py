import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI

from xaibo import Xaibo
from xaibo.server.web import XaiboWebServer, get_class_by_path
from xaibo.server.adapters.openai import OpenAiApiAdapter
from xaibo.server.adapters.mcp import McpApiAdapter


class MockAdapter:
    """Mock adapter for testing"""
    def __init__(self, xaibo, **kwargs):
        self.xaibo = xaibo
        self.kwargs = kwargs
        
    def adapt(self, app):
        pass


class MockOpenAiAdapter:
    """Mock OpenAI adapter for testing"""
    def __init__(self, xaibo, api_key=None, **kwargs):
        self.xaibo = xaibo
        self.api_key = api_key
        self.kwargs = kwargs
        
    def adapt(self, app):
        pass


class MockMcpAdapter:
    """Mock MCP adapter for testing"""
    def __init__(self, xaibo, api_key=None, **kwargs):
        self.xaibo = xaibo
        self.api_key = api_key
        self.kwargs = kwargs
        
    def adapt(self, app):
        pass


@pytest.fixture
def xaibo_instance():
    """Create a test Xaibo instance"""
    return Xaibo()


@pytest.fixture
def temp_agent_dir(tmp_path):
    """Create a temporary agent directory"""
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir()
    return str(agent_dir)


def test_get_class_by_path():
    """Test the get_class_by_path utility function"""
    # Test with a real class
    cls = get_class_by_path("xaibo.server.adapters.openai.OpenAiApiAdapter")
    assert cls == OpenAiApiAdapter
    
    cls = get_class_by_path("xaibo.server.adapters.mcp.McpApiAdapter")
    assert cls == McpApiAdapter


def test_web_server_initialization_no_api_keys(xaibo_instance, temp_agent_dir):
    """Test web server initialization without API keys"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_get_class.return_value = MockAdapter
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=["test.adapter.MockAdapter"],
            agent_dir=temp_agent_dir,
            host="127.0.0.1",
            port=8000,
            debug=False,
            openai_api_key=None,
            mcp_api_key=None
        )
        
        assert server.xaibo == xaibo_instance
        assert server.host == "127.0.0.1"
        assert server.port == 8000
        assert server.openai_api_key is None
        assert server.mcp_api_key is None
        assert isinstance(server.app, FastAPI)


def test_web_server_initialization_with_api_keys(xaibo_instance, temp_agent_dir):
    """Test web server initialization with API keys"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_get_class.return_value = MockAdapter
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=["test.adapter.MockAdapter"],
            agent_dir=temp_agent_dir,
            host="0.0.0.0",
            port=9000,
            debug=False,
            openai_api_key="test-openai-key",
            mcp_api_key="test-mcp-key"
        )
        
        assert server.openai_api_key == "test-openai-key"
        assert server.mcp_api_key == "test-mcp-key"
        assert server.host == "0.0.0.0"
        assert server.port == 9000


def test_web_server_openai_adapter_instantiation(xaibo_instance, temp_agent_dir):
    """Test that OpenAI adapter receives the correct API key"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance
        mock_adapter_class.__name__ = "OpenAiApiAdapter"
        mock_get_class.return_value = mock_adapter_class
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=["xaibo.server.adapters.openai.OpenAiApiAdapter"],
            agent_dir=temp_agent_dir,
            openai_api_key="test-openai-key-123"
        )
        
        # Verify the adapter was instantiated with the correct API key
        mock_adapter_class.assert_called_once_with(xaibo_instance, api_key="test-openai-key-123")
        mock_adapter_instance.adapt.assert_called_once_with(server.app)


def test_web_server_mcp_adapter_instantiation(xaibo_instance, temp_agent_dir):
    """Test that MCP adapter receives the correct API key"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance
        mock_adapter_class.__name__ = "McpApiAdapter"
        mock_get_class.return_value = mock_adapter_class
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=["xaibo.server.adapters.mcp.McpApiAdapter"],
            agent_dir=temp_agent_dir,
            mcp_api_key="test-mcp-key-456"
        )
        
        # Verify the adapter was instantiated with the correct API key
        mock_adapter_class.assert_called_once_with(xaibo_instance, api_key="test-mcp-key-456")
        mock_adapter_instance.adapt.assert_called_once_with(server.app)


def test_web_server_other_adapter_instantiation(xaibo_instance, temp_agent_dir):
    """Test that other adapters don't receive API keys"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance
        mock_adapter_class.__name__ = "SomeOtherAdapter"
        mock_get_class.return_value = mock_adapter_class
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=["some.other.SomeOtherAdapter"],
            agent_dir=temp_agent_dir,
            openai_api_key="test-openai-key",
            mcp_api_key="test-mcp-key"
        )
        
        # Verify the adapter was instantiated without API keys
        mock_adapter_class.assert_called_once_with(xaibo_instance)
        mock_adapter_instance.adapt.assert_called_once_with(server.app)


def test_web_server_multiple_adapters_with_api_keys(xaibo_instance, temp_agent_dir):
    """Test that multiple adapters receive their respective API keys"""
    adapters_and_classes = [
        ("xaibo.server.adapters.openai.OpenAiApiAdapter", "OpenAiApiAdapter"),
        ("xaibo.server.adapters.mcp.McpApiAdapter", "McpApiAdapter"),
        ("some.other.SomeOtherAdapter", "SomeOtherAdapter")
    ]
    
    mock_classes = {}
    mock_instances = {}
    
    def mock_get_class_side_effect(path):
        for adapter_path, class_name in adapters_and_classes:
            if path == adapter_path:
                if class_name not in mock_classes:
                    mock_class = Mock()
                    mock_instance = Mock()
                    mock_class.return_value = mock_instance
                    mock_class.__name__ = class_name
                    mock_classes[class_name] = mock_class
                    mock_instances[class_name] = mock_instance
                return mock_classes[class_name]
        return Mock()
    
    with patch('xaibo.server.web.get_class_by_path', side_effect=mock_get_class_side_effect):
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=[path for path, _ in adapters_and_classes],
            agent_dir=temp_agent_dir,
            openai_api_key="test-openai-key",
            mcp_api_key="test-mcp-key"
        )
        
        # Verify OpenAI adapter got the OpenAI API key
        mock_classes["OpenAiApiAdapter"].assert_called_once_with(xaibo_instance, api_key="test-openai-key")
        
        # Verify MCP adapter got the MCP API key
        mock_classes["McpApiAdapter"].assert_called_once_with(xaibo_instance, api_key="test-mcp-key")
        
        # Verify other adapter didn't get any API key
        mock_classes["SomeOtherAdapter"].assert_called_once_with(xaibo_instance)
        
        # Verify all adapters were adapted
        for instance in mock_instances.values():
            instance.adapt.assert_called_once_with(server.app)


def test_web_server_backward_compatibility_no_api_keys(xaibo_instance, temp_agent_dir):
    """Test backward compatibility when no API keys are provided"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_openai_class = Mock()
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_class.__name__ = "OpenAiApiAdapter"
        
        mock_mcp_class = Mock()
        mock_mcp_instance = Mock()
        mock_mcp_class.return_value = mock_mcp_instance
        mock_mcp_class.__name__ = "McpApiAdapter"
        
        def side_effect(path):
            if "openai" in path.lower():
                return mock_openai_class
            elif "mcp" in path.lower():
                return mock_mcp_class
            return Mock()
        
        mock_get_class.side_effect = side_effect
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=[
                "xaibo.server.adapters.openai.OpenAiApiAdapter",
                "xaibo.server.adapters.mcp.McpApiAdapter"
            ],
            agent_dir=temp_agent_dir,
            openai_api_key=None,
            mcp_api_key=None
        )
        
        # Verify adapters were instantiated with None API keys (backward compatibility)
        mock_openai_class.assert_called_once_with(xaibo_instance, api_key=None)
        mock_mcp_class.assert_called_once_with(xaibo_instance, api_key=None)


def test_web_server_debug_mode_adds_ui_adapter(xaibo_instance, temp_agent_dir):
    """Test that debug mode adds the UI adapter"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class, \
         patch('xaibo.server.adapters.ui.UIDebugTraceEventListener') as mock_listener:
        
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance
        mock_adapter_class.__name__ = "MockAdapter"
        mock_get_class.return_value = mock_adapter_class
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=["test.MockAdapter"],
            agent_dir=temp_agent_dir,
            debug=True
        )
        
        # Verify that the UI adapter was added to the adapters list
        # The debug mode should add "xaibo.server.adapters.UiApiAdapter"
        assert mock_get_class.call_count == 2  # Original adapter + UI adapter
        
        # Verify event listener was registered
        mock_listener.assert_called_once()


def test_command_line_argument_parsing():
    """Test command line argument parsing for API keys"""
    import argparse
    
    # Test that the argument parser accepts the API key arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-dir", dest="agent_dir", default="./agents", action="store")
    parser.add_argument("--adapter", dest="adapters", default=[], action="append")
    parser.add_argument("--host", dest="host", default="127.0.0.1", action="store")
    parser.add_argument("--port", dest="port", default=8000, type=int, action="store")
    parser.add_argument("--debug-ui", dest="debug", default=False, type=bool, action="store")
    parser.add_argument("--openai-api-key", dest="openai_api_key", default=None, action="store")
    parser.add_argument("--mcp-api-key", dest="mcp_api_key", default=None, action="store")
    
    # Test parsing with API keys
    args = parser.parse_args([
        "--openai-api-key", "test-openai-key",
        "--mcp-api-key", "test-mcp-key",
        "--adapter", "xaibo.server.adapters.openai.OpenAiApiAdapter"
    ])
    
    assert args.openai_api_key == "test-openai-key"
    assert args.mcp_api_key == "test-mcp-key"
    assert args.adapters == ["xaibo.server.adapters.openai.OpenAiApiAdapter"]
    assert args.agent_dir == "./agents"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.debug is False
    
    # Test parsing without API keys (should default to None)
    args = parser.parse_args([])
    assert args.openai_api_key is None
    assert args.mcp_api_key is None


def test_web_server_integration_with_real_adapters(xaibo_instance, temp_agent_dir):
    """Integration test with real adapter classes"""
    # Test that the server can instantiate real adapters with API keys
    server = XaiboWebServer(
        xaibo=xaibo_instance,
        adapters=[
            "xaibo.server.adapters.openai.OpenAiApiAdapter",
            "xaibo.server.adapters.mcp.McpApiAdapter"
        ],
        agent_dir=temp_agent_dir,
        openai_api_key="integration-openai-key",
        mcp_api_key="integration-mcp-key"
    )
    
    # Verify the server was created successfully
    assert server.openai_api_key == "integration-openai-key"
    assert server.mcp_api_key == "integration-mcp-key"
    assert isinstance(server.app, FastAPI)


def test_web_server_mixed_scenario_one_adapter_with_key_one_without(xaibo_instance, temp_agent_dir):
    """Test mixed scenario where one adapter has API key and one doesn't"""
    with patch('xaibo.server.web.get_class_by_path') as mock_get_class:
        mock_openai_class = Mock()
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_class.__name__ = "OpenAiApiAdapter"
        
        mock_other_class = Mock()
        mock_other_instance = Mock()
        mock_other_class.return_value = mock_other_instance
        mock_other_class.__name__ = "SomeOtherAdapter"
        
        def side_effect(path):
            if "openai" in path.lower():
                return mock_openai_class
            else:
                return mock_other_class
        
        mock_get_class.side_effect = side_effect
        
        server = XaiboWebServer(
            xaibo=xaibo_instance,
            adapters=[
                "xaibo.server.adapters.openai.OpenAiApiAdapter",
                "some.other.SomeOtherAdapter"
            ],
            agent_dir=temp_agent_dir,
            openai_api_key="test-openai-key",
            mcp_api_key=None  # No MCP key provided
        )
        
        # Verify OpenAI adapter got the API key
        mock_openai_class.assert_called_once_with(xaibo_instance, api_key="test-openai-key")
        
        # Verify other adapter didn't get any API key
        mock_other_class.assert_called_once_with(xaibo_instance)
        
        # Verify both adapters were adapted
        mock_openai_instance.adapt.assert_called_once_with(server.app)
        mock_other_instance.adapt.assert_called_once_with(server.app)