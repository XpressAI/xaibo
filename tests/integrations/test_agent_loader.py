import asyncio
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

from xaibo.integrations.livekit.agent_loader import XaiboAgentLoader
from xaibo.integrations.livekit.llm import XaiboLLM
from xaibo.core.config import AgentConfig
from xaibo.core.xaibo import Xaibo


class TestXaiboAgentLoader:
    """Test suite for XaiboAgentLoader class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.loader = XaiboAgentLoader()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test agent config file
        self.test_agent_yaml = """
id: test-agent
description: Test agent for unit tests
modules:
  - module: xaibo_examples.echo.Echo
    id: echo
    config:
      prefix: "Test: "
"""
        self.test_agent_path = os.path.join(self.temp_dir, "test_agent.yaml")
        with open(self.test_agent_path, "w") as f:
            f.write(self.test_agent_yaml)

    def teardown_method(self):
        """Clean up after each test method."""
        # Disable file watching if enabled
        if hasattr(self.loader, '_watcher_task') and self.loader._watcher_task:
            self.loader.disable_file_watching()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test XaiboAgentLoader initialization."""
        loader = XaiboAgentLoader()
        
        assert isinstance(loader._xaibo, Xaibo)
        assert loader._configs == {}
        assert loader._debug_enabled is False
        assert loader._debug_dir is None
        assert loader._watcher_task is None
        assert loader._watching_directory is None

    def test_load_agents_from_directory_success(self):
        """Test successful loading of agents from directory."""
        self.loader.load_agents_from_directory(self.temp_dir)
        
        # Check that agent was loaded
        agents = self.loader.list_agents()
        assert "test-agent" in agents
        assert len(self.loader._configs) == 1

    def test_load_agents_from_directory_nonexistent(self):
        """Test loading from non-existent directory raises FileNotFoundError."""
        nonexistent_dir = "/path/that/does/not/exist"
        
        with pytest.raises(FileNotFoundError, match="Agent directory not found"):
            self.loader.load_agents_from_directory(nonexistent_dir)

    @patch('xaibo.core.config.AgentConfig.load_directory')
    def test_load_agents_from_directory_yaml_error(self, mock_load_directory):
        """Test handling of YAML parsing errors."""
        mock_load_directory.side_effect = ValueError("Invalid YAML")
        
        with pytest.raises(ValueError, match="Invalid YAML"):
            self.loader.load_agents_from_directory(self.temp_dir)

    def test_load_agents_from_directory_reload(self):
        """Test reloading agents handles additions and removals."""
        # Initial load
        self.loader.load_agents_from_directory(self.temp_dir)
        assert len(self.loader.list_agents()) == 1
        
        # Add another agent
        second_agent_yaml = """
id: second-agent
modules:
  - module: xaibo_examples.echo.Echo
    id: echo2
"""
        second_agent_path = os.path.join(self.temp_dir, "second_agent.yaml")
        with open(second_agent_path, "w") as f:
            f.write(second_agent_yaml)
        
        # Reload
        self.loader.load_agents_from_directory(self.temp_dir)
        agents = self.loader.list_agents()
        assert len(agents) == 2
        assert "test-agent" in agents
        assert "second-agent" in agents
        
        # Remove first agent
        os.remove(self.test_agent_path)
        
        # Reload again
        self.loader.load_agents_from_directory(self.temp_dir)
        agents = self.loader.list_agents()
        assert len(agents) == 1
        assert "second-agent" in agents
        assert "test-agent" not in agents

    def test_get_llm_success(self):
        """Test successful LLM retrieval."""
        self.loader.load_agents_from_directory(self.temp_dir)
        
        llm = self.loader.get_llm("test-agent")
        
        assert isinstance(llm, XaiboLLM)
        assert llm._agent_id == "test-agent"
        assert llm._xaibo is self.loader._xaibo

    def test_get_llm_agent_not_found(self):
        """Test LLM retrieval with non-existent agent."""
        self.loader.load_agents_from_directory(self.temp_dir)
        
        with pytest.raises(ValueError, match="Agent 'nonexistent' not found"):
            self.loader.get_llm("nonexistent")

    def test_list_agents(self):
        """Test listing available agents."""
        # Initially empty
        assert self.loader.list_agents() == []
        
        # After loading
        self.loader.load_agents_from_directory(self.temp_dir)
        agents = self.loader.list_agents()
        assert "test-agent" in agents

    def test_get_agent_info_success(self):
        """Test successful agent info retrieval."""
        self.loader.load_agents_from_directory(self.temp_dir)
        
        info = self.loader.get_agent_info("test-agent")
        
        assert isinstance(info, dict)
        assert info["id"] == "test-agent"
        assert info["description"] == "Test agent for unit tests"
        assert isinstance(info["modules"], list)
        assert len(info["modules"]) >= 1
        # Find the echo module
        echo_module = next((m for m in info["modules"] if m["id"] == "echo"), None)
        assert echo_module is not None
        assert echo_module["module"] == "xaibo_examples.echo.Echo"
        assert isinstance(info["exchange"], list)

    def test_get_agent_info_agent_not_found(self):
        """Test agent info retrieval with non-existent agent."""
        self.loader.load_agents_from_directory(self.temp_dir)
        
        with pytest.raises(ValueError, match="Agent 'nonexistent' not found"):
            self.loader.get_agent_info("nonexistent")

    @patch('xaibo.server.adapters.ui.UIDebugTraceEventListener')
    def test_enable_debug_logging_success(self, mock_debug_listener):
        """Test successful debug logging enablement."""
        debug_dir = os.path.join(self.temp_dir, "debug")
        mock_listener_instance = Mock()
        mock_debug_listener.return_value = mock_listener_instance
        
        self.loader.enable_debug_logging(debug_dir)
        
        assert self.loader._debug_enabled is True
        assert self.loader._debug_dir == debug_dir
        assert os.path.exists(debug_dir)
        
        # Verify debug listener was created and registered
        mock_debug_listener.assert_called_once_with(Path(debug_dir))
        # Note: We can't easily test the event listener registration without mocking deeper

    def test_enable_debug_logging_import_error(self):
        """Test enabling debug logging when UI dependencies are missing."""
        with patch('xaibo.server.adapters.ui.UIDebugTraceEventListener', side_effect=ImportError("No module")):
            with pytest.raises(ValueError, match="Debug logging requires"):
                self.loader.enable_debug_logging()

    def test_is_debug_enabled(self):
        """Test debug status checking."""
        assert self.loader.is_debug_enabled() is False
        
        debug_dir = os.path.join(self.temp_dir, "debug")
        with patch('xaibo.server.adapters.ui.UIDebugTraceEventListener'):
            self.loader.enable_debug_logging(debug_dir)
            assert self.loader.is_debug_enabled() is True

    def test_get_debug_directory(self):
        """Test debug directory retrieval."""
        assert self.loader.get_debug_directory() is None
        
        debug_dir = os.path.join(self.temp_dir, "debug")
        with patch('xaibo.server.adapters.ui.UIDebugTraceEventListener'):
            self.loader.enable_debug_logging(debug_dir)
            assert self.loader.get_debug_directory() == debug_dir

    @pytest.mark.asyncio
    async def test_enable_file_watching_success(self):
        """Test successful file watching enablement."""
        with patch.object(self.loader, '_watch_config_files', new_callable=AsyncMock) as mock_watch:
            self.loader.enable_file_watching(self.temp_dir)
            
            assert self.loader._watching_directory == self.temp_dir
            assert self.loader._watcher_task is not None
            assert not self.loader._watcher_task.done()
            
            # Clean up
            self.loader.disable_file_watching()

    @pytest.mark.asyncio
    async def test_enable_file_watching_already_enabled_same_directory(self):
        """Test enabling file watching when already enabled for same directory."""
        with patch.object(self.loader, '_watch_config_files', new_callable=AsyncMock):
            self.loader.enable_file_watching(self.temp_dir)
            
            # Try to enable again for same directory - should not raise error
            self.loader.enable_file_watching(self.temp_dir)
            
            assert self.loader._watching_directory == self.temp_dir
            
            # Clean up
            self.loader.disable_file_watching()

    @pytest.mark.asyncio
    async def test_enable_file_watching_already_enabled_different_directory(self):
        """Test enabling file watching when already enabled for different directory."""
        other_temp_dir = tempfile.mkdtemp()
        
        try:
            with patch.object(self.loader, '_watch_config_files', new_callable=AsyncMock):
                self.loader.enable_file_watching(self.temp_dir)
                
                # Try to enable for different directory - should raise RuntimeError
                with pytest.raises(RuntimeError, match="File watching is already enabled"):
                    self.loader.enable_file_watching(other_temp_dir)
                
                # Clean up
                self.loader.disable_file_watching()
        finally:
            import shutil
            shutil.rmtree(other_temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_disable_file_watching(self):
        """Test disabling file watching."""
        with patch.object(self.loader, '_watch_config_files', new_callable=AsyncMock):
            self.loader.enable_file_watching(self.temp_dir)
            assert self.loader._watcher_task is not None
            
            self.loader.disable_file_watching()
            
            assert self.loader._watcher_task is None
            assert self.loader._watching_directory is None

    @pytest.mark.asyncio
    async def test_disable_file_watching_when_not_enabled(self):
        """Test disabling file watching when not enabled."""
        # Should not raise any errors
        self.loader.disable_file_watching()
        
        assert self.loader._watcher_task is None
        assert self.loader._watching_directory is None

    @pytest.mark.asyncio
    async def test_watch_config_files_success(self):
        """Test the internal file watching method."""
        mock_changes = [
            {('modified', self.test_agent_path)},
        ]
        
        async def mock_awatch_gen(directory, **kwargs):
            for change in mock_changes:
                yield change
        
        with patch('xaibo.integrations.livekit.agent_loader.awatch', side_effect=mock_awatch_gen):
            with patch.object(self.loader, 'load_agents_from_directory') as mock_load:
                # Run the watcher for a short time
                task = asyncio.create_task(self.loader._watch_config_files(self.temp_dir))
                await asyncio.sleep(0.1)  # Let it process one change
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # Verify that load_agents_from_directory was called
                mock_load.assert_called_with(self.temp_dir)

    @pytest.mark.asyncio
    async def test_watch_config_files_load_error(self):
        """Test file watching handles load errors gracefully."""
        mock_changes = [
            {('modified', self.test_agent_path)},
        ]
        
        async def mock_awatch_gen(directory, **kwargs):
            for change in mock_changes:
                yield change
        
        with patch('xaibo.integrations.livekit.agent_loader.awatch', side_effect=mock_awatch_gen):
            with patch.object(self.loader, 'load_agents_from_directory') as mock_load:
                mock_load.side_effect = Exception("Load failed")
                
                # Run the watcher for a short time
                task = asyncio.create_task(self.loader._watch_config_files(self.temp_dir))
                await asyncio.sleep(0.1)  # Let it process one change
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # Verify that load_agents_from_directory was called despite error
                mock_load.assert_called_with(self.temp_dir)

    @pytest.mark.asyncio
    async def test_watch_config_files_cancelled(self):
        """Test file watching handles cancellation gracefully."""
        with patch('xaibo.integrations.livekit.agent_loader.awatch') as mock_awatch:
            # Mock awatch to raise CancelledError
            async def mock_awatch_gen():
                raise asyncio.CancelledError()
            
            mock_awatch.return_value = mock_awatch_gen()
            
            # Should not raise exception
            await self.loader._watch_config_files(self.temp_dir)

    def test_get_xaibo_instance(self):
        """Test getting the underlying Xaibo instance."""
        xaibo_instance = self.loader.get_xaibo_instance()
        
        assert isinstance(xaibo_instance, Xaibo)
        assert xaibo_instance is self.loader._xaibo

    @pytest.mark.asyncio
    async def test_cleanup_on_del(self):
        """Test cleanup when object is deleted."""
        with patch.object(self.loader, '_watch_config_files', new_callable=AsyncMock):
            self.loader.enable_file_watching(self.temp_dir)
            watcher_task = self.loader._watcher_task
            
            # Simulate deletion
            self.loader.__del__()
            
            # Give a moment for cancellation to take effect
            await asyncio.sleep(0.01)
            
            # Task should be cancelled
            assert watcher_task is not None
            assert watcher_task.cancelled()

    def test_cleanup_on_del_no_watcher(self):
        """Test cleanup when no watcher is active."""
        # Should not raise any errors
        self.loader.__del__()

    @pytest.mark.asyncio
    async def test_integration_full_workflow(self):
        """Test a complete workflow with loading, getting LLM, and cleanup."""
        # Load agents
        self.loader.load_agents_from_directory(self.temp_dir)
        
        # Enable debug logging
        debug_dir = os.path.join(self.temp_dir, "debug")
        with patch('xaibo.server.adapters.ui.UIDebugTraceEventListener'):
            self.loader.enable_debug_logging(debug_dir)
        
        # Enable file watching
        with patch.object(self.loader, '_watch_config_files', new_callable=AsyncMock):
            self.loader.enable_file_watching(self.temp_dir)
        
        # Get agent info
        info = self.loader.get_agent_info("test-agent")
        assert info["id"] == "test-agent"
        
        # Get LLM
        llm = self.loader.get_llm("test-agent")
        assert isinstance(llm, XaiboLLM)
        
        # Check status
        assert self.loader.is_debug_enabled()
        assert self.loader.get_debug_directory() == debug_dir
        assert len(self.loader.list_agents()) == 1
        
        # Cleanup
        self.loader.disable_file_watching()
        assert self.loader._watcher_task is None


@pytest.mark.asyncio
async def test_agent_loader_with_real_config():
    """Integration test using real agent configuration files."""
    # Find the test resources directory
    test_dir = Path(__file__).parent
    resources_dir = test_dir.parent / "resources" / "yaml"
    
    if not resources_dir.exists():
        pytest.skip("Test resources directory not found")
    
    loader = XaiboAgentLoader()
    
    try:
        # Load agents from test resources
        loader.load_agents_from_directory(str(resources_dir))
        
        # Should have loaded the echo agents
        agents = loader.list_agents()
        assert len(agents) > 0
        
        # Test getting LLM for first agent
        first_agent = agents[0]
        llm = loader.get_llm(first_agent)
        assert isinstance(llm, XaiboLLM)
        
        # Test getting agent info
        info = loader.get_agent_info(first_agent)
        assert info["id"] == first_agent
        assert isinstance(info["modules"], list)
        
    finally:
        # Cleanup
        if hasattr(loader, '_watcher_task') and loader._watcher_task:
            loader.disable_file_watching()