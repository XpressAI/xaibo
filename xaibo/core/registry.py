from typing import Callable, Union, Type

from .agent import Agent
from .config import AgentConfig
from .exchange import Exchange
from .protocols.events import Event


class Registry:
    """A registry for managing agent configurations and instantiating agents.

    The Registry class provides functionality to register agent configurations and create
    agent instances based on those configurations.
    """

    def __init__(self):
        """Initialize a new Registry instance with an empty configuration dictionary."""
        self.known_agent_configs: dict[str, AgentConfig] = dict()
        self.event_listeners: list[tuple[str, str | None, callable]] = []

    def register_agent(self, agent_config: AgentConfig) -> None:
        """Register a new agent configuration.

        Args:
            agent_config (AgentConfig): The configuration to register
        """
        self.known_agent_configs[agent_config.id] = agent_config

    def get_agent(self, id: str) -> Agent:
        """Get an agent instance with default bindings.

        Args:
            id (str): The ID of the agent configuration to use

        Returns:
            Agent: A new agent instance
        """
        return self.get_agent_with(id, {})
    
    def get_agent_with(self, id: str, override_bindings: dict[Union[str, Type], any]) -> Agent:
        """Get an agent instance with custom bindings.

        Args:
            id (str): The ID of the agent configuration to use
            override_bindings (dict[Union[str, Type], any]): Custom bindings to override defaults

        Returns:
            Agent: A new agent instance with the specified bindings
        """
        if id not in self.known_agent_configs:
            raise KeyError(f"No agent configuration found for id: {id}")
        config = self.known_agent_configs[id]
        exchange = Exchange()
        
        # Filter event listeners for this agent
        agent_listeners = [
            (prefix, handler) for prefix, agent_filter, handler in self.event_listeners 
            if agent_filter is None or agent_filter == id
        ]
        
        module_instances = exchange.instantiate_modules(
            config, 
            override_bindings,
            event_listeners=agent_listeners
        )
        return Agent(id=id, modules=module_instances)

    def register_event_listener(self, prefix: str, handler: Callable[[Event], None], agent_id: str | None = None) -> None:
        """Register an event listener for module events.

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
        self.event_listeners.append((prefix, agent_id, handler))