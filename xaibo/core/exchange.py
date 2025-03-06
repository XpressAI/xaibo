from .config import AgentConfig

class Exchange:
    """Handles module instantiation and dependency injection for agents."""

    def instantiate_modules(self, config: AgentConfig, override_bindings: dict[str, any]) -> dict[str, any]:
        """Create instances of all modules defined in config."""
        module_instances = {}

        # First pass - instantiate modules that don't have dependencies
        for module_config in config.modules:
            if not module_config.uses:
                module_class = config._import_module_class(module_config.module)
                module_instances[module_config.id] = Proxy(module_class(
                    config=module_config.config
                ))

        # Second pass - instantiate modules with dependencies
        for module_config in config.modules:
            if module_config.id not in module_instances and module_config.uses:
                module_class = config._import_module_class(module_config.module)
                dependencies = self._get_module_dependencies(config, module_config, module_instances, module_class)
                dependencies.update(self._filter_overrides(module_class, override_bindings))

                module_instances[module_config.id] = Proxy(module_class(
                    **dependencies,
                    config=module_config.config
                ))

        module_instances['__entry__'] = self._get_entry_module(config, module_instances)
        return module_instances

    def _get_module_dependencies(self, config: AgentConfig, module_config: any, module_instances: dict[str, any], module_class: any) -> dict[str, any]:
        """Get dependencies for a module from exchange config."""
        dependencies = {}
        for exchange in config.exchange:
            if exchange.module == module_config.id:
                params = module_class.__init__.__annotations__
                matching_params = [
                    param for param, type_hint in params.items()
                    if isinstance(module_instances[exchange.provider], type_hint)
                ]

                if len(matching_params) > 1:
                    raise ValueError(f"Multiple parameters match protocol {exchange.protocol} in module {module_config.id}")
                elif len(matching_params) == 0:
                    raise ValueError(f"No parameter found matching protocol {exchange.protocol} and type of {exchange.provider} in module {module_config.id}")

                dependencies[matching_params[0]] = module_instances[exchange.provider]
        return dependencies

    def _filter_overrides(self, module_class: any, override_bindings: dict[str, any]) -> dict[str, any]:
        """Filter override bindings to only include valid module parameters."""
        module_params = module_class.__init__.__code__.co_varnames
        return {
            k: v for k, v in override_bindings.items()
            if k in module_params
        }

    def _get_entry_module(self, config: AgentConfig, module_instances: dict[str, any]) -> any:
        """Get the entry module from exchange config."""
        entry_module = None
        for exchange in config.exchange:
            if exchange.module == "__entry__":
                if entry_module is not None:
                    raise ValueError("Multiple message handlers found")
                entry_module = module_instances[exchange.provider]

        if entry_module is None:
            raise ValueError("No message handler found in exchange config")

        return entry_module

class MethodProxy:
    """A proxy class that wraps a method and delegates calls.
    
    This proxy forwards method calls to the wrapped method. It maintains a reference 
    to the parent object to preserve the method's context.
    """

    def __init__(self, method, parent):
        """Initialize the method proxy.
        
        Args:
            method: The method to wrap and proxy
            parent: The parent object that owns this method
        """
        self._method = method
        self._parent = parent

    def __call__(self, *args, **kwargs):
        """Forward calls to the wrapped method.
        
        Args:
            *args: Positional arguments to pass to wrapped method
            **kwargs: Keyword arguments to pass to wrapped method
            
        Returns:
            The result of calling the wrapped method, wrapped in a MethodProxy if callable
        """
        result = self._method(*args, **kwargs)
        return MethodProxy(result, self._parent) if callable(result) else result

    def __repr__(self):
        return f"MethodProxy({self._method.__name__})"


class Proxy:
    """A proxy class that wraps an object and delegates attribute access.
    
    This proxy forwards all attribute access to the wrapped object. It wraps any callable
    attributes in a MethodProxy to maintain the proper context, while returning other
    attributes directly.
    """

    def __init__(self, obj):
        """Initialize the proxy with an object to wrap.
        
        Args:
            obj: The object to wrap and proxy
        """
        self._obj = obj

    def __getattr__(self, name):
        """Forward attribute access to the wrapped object.
        
        Args:
            name: Name of the attribute to access
            
        Returns:
            The attribute value from the wrapped object, wrapped in a MethodProxy if callable
        """        
        attr = getattr(self._obj, name)
        if callable(attr):
            return MethodProxy(attr, self._obj)
        return attr

    def __repr__(self):
        return f"Proxy({self._obj.__class__.__name__})"