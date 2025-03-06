from xaibo.core.agent import Agent
from xaibo.core.config import AgentConfig
from xaibo.core.exchange import Exchange


class Registry:
    """A registry for managing agent configurations and instantiating agents.

    The Registry class provides functionality to register agent configurations and create
    agent instances based on those configurations.
    """

    def __init__(self):
        """Initialize a new Registry instance with an empty configuration dictionary."""
        self.known_agent_configs: dict[str, AgentConfig] = dict()
        self.exchange = Exchange()

    def registerAgent(self, agent_config: AgentConfig) -> None:
        """Register a new agent configuration.

        Args:
            agent_config (AgentConfig): The configuration to register
        """
        self.known_agent_configs[agent_config.id] = agent_config

    def getAgent(self, id: str) -> Agent:
        """Get an agent instance with default bindings.

        Args:
            id (str): The ID of the agent configuration to use

        Returns:
            Agent: A new agent instance
        """
        return self.getAgentWith(id, {})
    
    def getAgentWith(self, id: str, override_bindings: dict[str, any]) -> Agent:
        """Get an agent instance with custom bindings.

        Args:
            id (str): The ID of the agent configuration to use
            override_bindings (dict[str, any]): Custom bindings to override defaults

        Returns:
            Agent: A new agent instance with the specified bindings
        """
        config = self._get_config_or_raise(id)
        module_instances = self.exchange.instantiate_modules(config, override_bindings)
        return Agent(id=id, modules=module_instances)

    def _get_config_or_raise(self, id: str) -> AgentConfig:
        """Get agent config by ID or raise KeyError if not found."""
        if id not in self.known_agent_configs:
            raise KeyError(f"No agent configuration found for id: {id}")
        return self.known_agent_configs[id]