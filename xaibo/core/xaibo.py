from typing import Union, Callable

from .protocols import Event
from .registry import Registry
from .agent import Agent
from .config import AgentConfig


class Xaibo:
    """The primary entry point for interacting with the xaibo framework.

    The Xaibo class provides a high-level interface for managing agents, registering event listeners,
    and instantiating agents with custom configurations. It acts as the main point of interaction
    for applications using the xaibo framework.
    """

    def __init__(self):
        """Initialize a new Xaibo instance with an empty registry."""
        self.registry = Registry()

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

    def get_agent_with(self, agent_id: str, overrides: dict[Union[str|type], any]) -> Agent:
        """Create and return an agent instance with custom dependency bindings.

        This method allows more control over agent instantiation by specifying custom
        implementations for the agent's dependencies. This is useful for testing,
        mocking, or providing specialized implementations.

        Args:
            agent_id (str): The ID of the agent configuration to use
            overrides (dict[Union[str, Type], any]): Custom bindings to override defaults

        Returns:
            Agent: A new agent instance with the specified dependency bindings
        """
        return self.registry.get_agent_with(agent_id, overrides)
