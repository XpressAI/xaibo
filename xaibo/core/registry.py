from xaibo.core.agent import Agent
from xaibo.core.config import AgentConfig


class Registry:
    """A registry for managing agent configurations and instantiating agents.

    The Registry class provides functionality to register agent configurations and create
    agent instances based on those configurations.
    """

    def __init__(self):
        """Initialize a new Registry instance with an empty configuration dictionary."""
        self.known_agent_configs: dict[str, AgentConfig] = dict()

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
        if id not in self.known_agent_configs:
            raise KeyError(f"No agent configuration found for id: {id}")
            
        config = self.known_agent_configs[id]

        # Create module instances based on config
        module_instances = {}
        
        # First pass - instantiate modules that don't have dependencies
        for module_config in config.modules:
            if not module_config.uses:
                module_class = config._import_module_class(module_config.module)
                module_instances[module_config.id] = module_class(
                    config=module_config.config
                )

        # Second pass - instantiate modules with dependencies
        for module_config in config.modules:
            if module_config.id not in module_instances and module_config.uses:
                module_class = config._import_module_class(module_config.module)
                
                # Get dependencies from exchange config
                dependencies = {}
                for exchange in config.exchange:
                    if exchange.module == module_config.id:
                        # Get module class parameters and their annotations
                        params = module_class.__init__.__annotations__

                        # Find parameters that match both protocol name and provider type
                        matching_params = [
                            param for param, type_hint in params.items() 
                            if isinstance(module_instances[exchange.provider], type_hint)
                        ]
                        
                        if len(matching_params) > 1:
                            raise ValueError(f"Multiple parameters match protocol {exchange.protocol} in module {module_config.id}")
                        elif len(matching_params) == 0:
                            raise ValueError(f"No parameter found matching protocol {exchange.protocol} and type of {exchange.provider} in module {module_config.id}")
                            
                        dependencies[matching_params[0]] = module_instances[exchange.provider]
                
                # Only include override bindings that match module parameters
                module_params = module_class.__init__.__code__.co_varnames
                filtered_overrides = {
                    k: v for k, v in override_bindings.items() 
                    if k in module_params
                }
                dependencies.update(filtered_overrides)
                
                # Instantiate module with dependencies
                module_instances[module_config.id] = module_class(
                    **dependencies,
                    config=module_config.config
                )

        # Set up entry module based on exchange config
        entry_module = None
        for exchange in config.exchange:
            if exchange.module == "__entry__":
                if entry_module is not None:
                    raise ValueError("Multiple message handlers found")
                entry_module = module_instances[exchange.provider]
        
        if entry_module is None:
            raise ValueError("No message handler found in exchange config")
        module_instances['__entry__'] = entry_module

        # Create and return agent with module instances and entry module
        agent = Agent(id=id, modules=module_instances)
            
        return agent