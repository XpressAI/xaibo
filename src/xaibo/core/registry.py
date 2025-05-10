from typing import Callable, Union, Type, Optional

from .agent import Agent
from .config import AgentConfig, ConfigOverrides, Scope, ExchangeConfig
from .exchange import Exchange
from xaibo.core.models import Event


class Registry:
    """A registry for managing agent configurations and instantiating agents.

    The Registry class provides functionality to register agent configurations and create
    agent instances based on those configurations.
    """

    def __init__(self):
        """Initialize a new Registry instance with an empty configuration dictionary."""
        self.known_agent_configs: dict[str, AgentConfig] = dict()
        self.event_listeners: list[tuple[str, str | None, callable]] = []
        self.server_module_instances: dict[str, object] = dict()
        self.agent_module_instances: dict[str, dict[str, object]] = dict()

    def register_server_module(self, id:str, module: object):
        self.server_module_instances[id] = module

    def unregister_server_module(self, id):
        if id in self.server_module_instances:
            del self.server_module_instances[id]

    def register_agent(self, agent_config: AgentConfig) -> None:
        """Register a new agent configuration.

        Args:
            agent_config (AgentConfig): The configuration to register
        """
        self.known_agent_configs[agent_config.id] = agent_config
        self.agent_module_instances[agent_config.id] = dict()
        agent_lifecycle_modules = [m.id for m in agent_config.modules if m.scope == Scope.Agent]
        if len(agent_lifecycle_modules) > 0:
            exchange = Exchange(agent_config, specific_modules=agent_lifecycle_modules)
            for module_id in agent_lifecycle_modules:
                self.agent_module_instances[agent_config.id][module_id] = exchange.module_instances[module_id]


    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent configuration.

        Args:
            agent_id (str): The ID of the agent configuration to unregister
        """
        if agent_id in self.known_agent_configs:
            del self.known_agent_configs[agent_id]
            del self.agent_module_instances[agent_id]

    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """Get the configuration for a registered agent.

        Args:
            agent_id (str): The ID of the agent configuration to retrieve

        Returns:
            AgentConfig: The configuration for the specified agent

        Raises:
            KeyError: If no agent configuration is found for the given ID
        """
        if agent_id not in self.known_agent_configs:
            raise KeyError(f"No agent configuration found for id: {agent_id}")
        return self.known_agent_configs[agent_id]

    def list_agents(self) -> list[str]:
        """Get a list of IDs for all registered agent configurations.

        Returns:
            list[str]: List of agent configuration IDs
        """
        return list(self.known_agent_configs.keys())

    def get_agent(self, id: str) -> Agent:
        """Get an agent instance with default bindings.

        Args:
            id (str): The ID of the agent configuration to use

        Returns:
            Agent: A new agent instance
        """
        return self.get_agent_with(id, None)
    
    def get_agent_with(self, id: str, override_config: Optional[ConfigOverrides], additional_event_listeners: list[tuple[str, callable]] = None) -> Agent:
        """Get an agent instance with custom bindings.

        Args:
            id (str): The ID of the agent configuration to use
            override_config (ConfigOverrides): Custom bindings to override defaults
            additional_event_listeners (list[tuple[str, callable]], optional): Additional event listeners to register.
                Each tuple contains (prefix, handler). Defaults to None.

        Returns:
            Agent: A new agent instance with the specified bindings
        """
        if id not in self.known_agent_configs:
            raise KeyError(f"No agent configuration found for id: {id}")
        config = self.known_agent_configs[id]
        
        # Filter event listeners for this agent
        agent_listeners = [
            (prefix, handler) for prefix, agent_filter, handler in self.event_listeners 
            if agent_filter is None or agent_filter == id
        ]

        # Add any additional event listeners
        if additional_event_listeners:
            agent_listeners.extend(additional_event_listeners)

        if override_config is None:
            override_config = ConfigOverrides()

        exchange = Exchange(
            config,
            override_config=ConfigOverrides(
                instances=dict(
                    list(override_config.instances.items()) +
                    list(self.agent_module_instances[id].items()) +
                    list(self.server_module_instances.items())
                ),
                exchange=(
                    override_config.exchange +
                    [
                        ExchangeConfig(
                            protocol=module.__class__,
                            provider=id
                        ) for (id, module) in  self.server_module_instances.items()
                    ]
                )
            ),
            event_listeners=agent_listeners
        )

        return Agent(id=id, exchange=exchange)
    
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