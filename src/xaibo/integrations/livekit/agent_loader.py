import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from watchfiles import awatch

from xaibo.core.xaibo import Xaibo
from xaibo.core.config import AgentConfig

from .llm import XaiboLLM
from .log import logger


class XaiboAgentLoader:
    """
    LiveKit-Xaibo integration helper that enables direct use of Xaibo agents 
    in LiveKit applications with YAML loading and debugging.
    
    This class provides a simple interface for LiveKit applications to load
    Xaibo agents from YAML configuration files and get configured XaiboLLM
    instances that work seamlessly with LiveKit's agent framework.
    """

    def __init__(self) -> None:
        """Initialize the XaiboAgentLoader with a new Xaibo instance."""
        self._xaibo = Xaibo()
        self._configs: Dict[str, AgentConfig] = {}
        self._debug_enabled = False
        self._debug_dir: Optional[str] = None
        self._watcher_task: Optional[asyncio.Task] = None
        self._watching_directory: Optional[str] = None

    def load_agents_from_directory(self, directory: str) -> None:
        """
        Load all agent configurations from a directory.
        
        This method recursively scans the specified directory for YAML files
        containing agent configurations and registers them with the Xaibo instance.
        
        Args:
            directory: Path to directory containing YAML agent configurations
            
        Raises:
            ValueError: If any YAML files cannot be parsed as valid agent configs
            FileNotFoundError: If the directory does not exist
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Agent directory not found: {directory}")
        
        logger.info(f"Loading agents from directory: {directory}")
        
        try:
            # Load all agent configurations from the directory
            new_configs = AgentConfig.load_directory(directory)
            
            # Unregister removed agents
            for path in set(self._configs.keys()) - set(new_configs.keys()):
                old_config = self._configs[path]
                self._xaibo.unregister_agent(old_config.id)
                logger.info(f"Unregistered agent: {old_config.id}")
            
            # Register new/changed agents
            for path, config in new_configs.items():
                if path not in self._configs or self._configs[path] != config:
                    self._xaibo.register_agent(config)
                    logger.info(f"Registered agent: {config.id} from {path}")
            
            self._configs = new_configs
            logger.info(f"Successfully loaded {len(self._configs)} agent configurations")
            
        except Exception as e:
            logger.error(f"Failed to load agents from directory {directory}: {e}")
            raise

    def get_llm(self, agent_id: str) -> XaiboLLM:
        """
        Get a configured XaiboLLM instance for the specified agent.
        
        Args:
            agent_id: The ID of the agent to get an LLM instance for
            
        Returns:
            XaiboLLM: A configured LLM instance ready for use with LiveKit
            
        Raises:
            ValueError: If the agent ID is not found in loaded configurations
        """
        if agent_id not in self.list_agents():
            available_agents = ", ".join(self.list_agents())
            raise ValueError(
                f"Agent '{agent_id}' not found. Available agents: {available_agents}"
            )
        
        logger.debug(f"Creating XaiboLLM instance for agent: {agent_id}")
        return XaiboLLM(xaibo=self._xaibo, agent_id=agent_id)

    def list_agents(self) -> List[str]:
        """
        List all available agent IDs.
        
        Returns:
            List[str]: List of agent IDs that have been loaded
        """
        return self._xaibo.list_agents()

    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent metadata and configuration details.
        
        Args:
            agent_id: The ID of the agent to get information for
            
        Returns:
            Dict containing agent metadata including id, description, modules, etc.
            
        Raises:
            ValueError: If the agent ID is not found
        """
        if agent_id not in self.list_agents():
            available_agents = ", ".join(self.list_agents())
            raise ValueError(
                f"Agent '{agent_id}' not found. Available agents: {available_agents}"
            )
        
        config = self._xaibo.get_agent_config(agent_id)
        
        return {
            "id": config.id,
            "description": config.description,
            "modules": [
                {
                    "id": module.id,
                    "module": module.module,
                    "scope": module.scope.value,
                    "provides": module.provides,
                    "uses": module.uses,
                    "config": module.config,
                }
                for module in config.modules
            ],
            "exchange": [
                {
                    "module": exchange.module,
                    "field_name": exchange.field_name,
                    "protocol": exchange.protocol,
                    "provider": exchange.provider,
                }
                for exchange in (config.exchange or [])
            ],
        }

    def enable_debug_logging(self, debug_dir: str = "./debug") -> None:
        """
        Enable Xaibo's debug logging system.
        
        This enables the same debugging capabilities as the Xaibo web server,
        writing debug traces to the specified directory.
        
        Args:
            debug_dir: Directory to write debug traces to (default: "./debug")
        """
        self._debug_enabled = True
        self._debug_dir = debug_dir
        
        # Ensure debug directory exists
        Path(debug_dir).mkdir(parents=True, exist_ok=True)
        
        # Register the debug event listener
        try:
            from xaibo.server.adapters.ui import UIDebugTraceEventListener
            
            debug_listener = UIDebugTraceEventListener(Path(debug_dir))
            self._xaibo.register_event_listener("", debug_listener.handle_event)
            
            logger.info(f"Debug logging enabled. Traces will be written to: {debug_dir}")
            
        except ImportError as e:
            logger.error(f"Failed to enable debug logging: {e}")
            raise ValueError(
                "Debug logging requires the Xaibo UI debug adapter. "
                "Make sure the xaibo package is installed with UI dependencies."
            )

    def enable_file_watching(self, directory: str) -> None:
        """
        Enable automatic reloading of agent configurations when files change.
        
        This starts a background task that watches the specified directory for
        changes and automatically reloads agent configurations when YAML files
        are modified, added, or removed.
        
        Args:
            directory: Directory to watch for configuration changes
            
        Raises:
            RuntimeError: If file watching is already enabled for a different directory
        """
        if self._watcher_task and not self._watcher_task.done():
            if self._watching_directory != directory:
                raise RuntimeError(
                    f"File watching is already enabled for directory: {self._watching_directory}. "
                    f"Disable it first before watching a different directory."
                )
            logger.warning(f"File watching is already enabled for directory: {directory}")
            return
        
        self._watching_directory = directory
        self._watcher_task = asyncio.create_task(self._watch_config_files(directory))
        logger.info(f"File watching enabled for directory: {directory}")

    def disable_file_watching(self) -> None:
        """
        Disable automatic file watching if it's currently enabled.
        """
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()
            logger.info(f"File watching disabled for directory: {self._watching_directory}")
        
        self._watcher_task = None
        self._watching_directory = None

    async def _watch_config_files(self, directory: str) -> None:
        """
        Internal method to watch for configuration file changes.
        
        Args:
            directory: Directory to watch for changes
        """
        try:
            async for changes in awatch(directory, force_polling=True):
                logger.debug(f"Configuration file changes detected: {changes}")
                try:
                    self.load_agents_from_directory(directory)
                except Exception as e:
                    logger.error(f"Failed to reload configurations after file change: {e}")
        except asyncio.CancelledError:
            logger.debug("File watching task cancelled")
        except Exception as e:
            logger.error(f"Error in file watching task: {e}")

    def get_xaibo_instance(self) -> Xaibo:
        """
        Get the underlying Xaibo instance.
        
        This provides access to the raw Xaibo instance for advanced use cases
        that require direct interaction with the Xaibo framework.
        
        Returns:
            Xaibo: The underlying Xaibo instance
        """
        return self._xaibo

    def is_debug_enabled(self) -> bool:
        """
        Check if debug logging is currently enabled.
        
        Returns:
            bool: True if debug logging is enabled, False otherwise
        """
        return self._debug_enabled

    def get_debug_directory(self) -> Optional[str]:
        """
        Get the current debug directory if debug logging is enabled.
        
        Returns:
            Optional[str]: The debug directory path, or None if debug logging is disabled
        """
        return self._debug_dir if self._debug_enabled else None

    def __del__(self) -> None:
        """Cleanup method to ensure file watching is properly disabled."""
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()