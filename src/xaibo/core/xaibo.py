from typing import Union, Callable
import os

from .models import Event
from .registry import Registry
from .agent import Agent
from .config import AgentConfig, ConfigOverrides


class Xaibo:
    """The primary entry point for interacting with the xaibo framework.

    The Xaibo class provides a high-level interface for managing agents, registering event listeners,
    and instantiating agents with custom configurations. It acts as the main point of interaction
    for applications using the xaibo framework.
    """

    def __init__(self):
        """Initialize a new Xaibo instance with an empty registry."""
        self.registry = Registry()
        
        # Register debug event listener if XAIBO_DEBUG environment variable is set
        if os.environ.get("XAIBO_DEBUG"):
            from xaibo.primitives.event_listeners.debug_event_listener import register_debug_listener
            register_debug_listener(self.registry)

        self.register_server_module('__xaibo__', self)

    def register_server_module(self, id:str, module: object):
        self.registry.register_server_module(id, module)

    def unregister_server_module(self, id):
        self.registry.unregister_server_module(id)

    def register_agent(self, agent_config: AgentConfig) -> None:
        """Register a new agent configuration.

        This method allows registering agent configurations that can later be instantiated
        into running agents using get_agent() or get_agent_with().

        Args:
            agent_config (AgentConfig): The configuration to register
        """
        self.registry.register_agent(agent_config)

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent configuration.

        Args:
            agent_id (str): The ID of the agent configuration to unregister
        """
        self.registry.unregister_agent(agent_id)

    def list_agents(self) -> list[str]:
        """Get a list of IDs for all registered agent configurations.

        Returns:
            list[str]: List of agent configuration IDs
        """
        return self.registry.list_agents()

    def register_event_listener(self, prefix: str, handler: Callable[[Event], None], agent_id: str | None = None):
        """Register an event listener to monitor agent and module events.

        Event listeners provide visibility into the internal workings of agents and modules.
        They can be used for debugging, monitoring, logging, or implementing custom behaviors.

        Args:
            prefix (str): Event prefix to listen for. Empty string means all events.
                         Otherwise, should be in format: {package}.{class}.{method_name}.{call|result}
            handler (Callable[[Event], None]): Function to handle events. Receives Event object with properties:
                              - event_name: Full event name
                              - event_type: EventType.CALL or EventType.RESULT
                              - module_class: Module class name
                              - method_name: Method name
                              - time: Event timestamp
                              - call_id: Unique ID for this method call
                              - arguments: Method arguments (for CALL events)
                              - result: Method result (for RESULT events)
            agent_id (str | None): Optional agent ID to filter events for
        """
        self.registry.register_event_listener(prefix, handler, agent_id=agent_id)

    def get_agent(self, agent_id: str) -> Agent:
        """Create and return an agent instance with default bindings.

        This is the primary way to instantiate agents for use in an application.
        The agent configuration must have been previously registered using register_agent().

        Args:
            agent_id (str): The ID of the agent configuration to use

        Returns:
            Agent: A new agent instance ready for use
        """
        return self.registry.get_agent(agent_id)

    def get_agent_with(self, agent_id: str, override_config: ConfigOverrides, additional_event_listeners: list[tuple[str, callable]] = None) -> Agent:
        """Create and return an agent instance with custom dependency bindings.

        This method allows more control over agent instantiation by specifying custom
        implementations for the agent's dependencies and registering additional event listeners.
        This is useful for testing, mocking, providing specialized implementations, or adding
        temporary monitoring.

        Args:
            agent_id (str): The ID of the agent configuration to use
            override_config (ConfigOverrides): Custom bindings to override defaults
            additional_event_listeners (list[tuple[str, callable]], optional): Additional event listeners to register.
                Each tuple contains (prefix, handler). Defaults to None.

        Returns:
            Agent: A new agent instance with the specified dependency bindings and event listeners
        """
        return self.registry.get_agent_with(agent_id, override_config, additional_event_listeners)
    
    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """Get the configuration for a registered agent.

        Args:
            agent_id (str): The ID of the agent configuration to retrieve

        Returns:
            AgentConfig: The configuration for the specified agent
        """
        return self.registry.get_agent_config(agent_id)