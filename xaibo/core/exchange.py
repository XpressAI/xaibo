from typing import Type, Union
from .config import AgentConfig
from .protocols.events import EventType, Event
import time

class Exchange:
    """Handles module instantiation and dependency injection for agents."""

    def instantiate_modules(self, config: AgentConfig, override_bindings: dict[Union[str, Type], any], event_listeners: list[tuple[str, callable]] = None) -> dict[str, any]:
        """Create instances of all modules defined in config."""
        module_instances = {}
        event_listeners = event_listeners or []

        # First pass - instantiate modules that don't have dependencies
        for module_config in config.modules:
            if not module_config.uses:
                module_class = config._import_module_class(module_config.module)
                module_instances[module_config.id] = Proxy(module_class(
                    config=module_config.config
                ), event_listeners=event_listeners, agent_id=config.id)

        # Second pass - instantiate modules with dependencies
        for module_config in config.modules:
            if module_config.id not in module_instances and module_config.uses:
                module_class = config._import_module_class(module_config.module)
                dependencies = self._get_module_dependencies(config, module_config, module_instances, module_class)
                dependencies.update(self._get_overrides_by_type(module_class, override_bindings))


                module_instances[module_config.id] = Proxy(module_class(
                    **dependencies,
                    config=module_config.config
                ), event_listeners=event_listeners, agent_id=config.id)

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

    def _get_overrides_by_type(self, module_class: any, override_bindings: dict[Union[str, Type], any]) -> dict[str, any]:
        """Map override bindings to module parameters based on type matching."""
        params = module_class.__init__.__annotations__
        dependencies = {}

        for param_name, param_type in params.items():
            # Check for direct type match
            if param_type in override_bindings:
                dependencies[param_name] = override_bindings[param_type]
            # Check for string type name match
            elif param_type.__name__ in override_bindings:
                dependencies[param_name] = override_bindings[param_type.__name__]
        return dependencies
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
    to the parent object to preserve the method's context and emits events to registered listeners.
    """

    def __init__(self, method, parent, event_listeners=None, agent_id=None):
        """Initialize the method proxy.
        
        Args:
            method: The method to wrap and proxy
            parent: The parent object that owns this method
            event_listeners: List of (prefix, handler) tuples for event handling
            agent_id: ID of the agent this method belongs to
        """
        self._method = method
        self._parent = parent
        self._event_listeners = event_listeners or []
        self._call_id = 0
        self._agent_id = agent_id

    def _emit_event(self, event_type: EventType, result=None, arguments=None):
        """Emit an event to all registered listeners.
        
        Args:
            event_type: Type of event (CALL or RESULT)
            result: Optional result value for RESULT events
            arguments: Optional arguments for CALL events
        """
        if len(self._event_listeners) == 0:
            return
        
        method_name = self._method.__name__
        module_class = self._parent.__class__.__name__
        module_package = self._parent.__class__.__module__
        
        event = Event(
            event_name=f"{module_package}.{module_class}.{method_name}.{event_type.value}",
            event_type=event_type,
            module_class=module_class,
            method_name=method_name,
            time=time.time(),
            result=result,
            arguments=arguments,
            call_id=f"{id(self._parent)}-{id(self._method)}-{self._call_id}",
            agent_id=self._agent_id
        )

        for prefix, handler in self._event_listeners:
            if not prefix or event.event_name.startswith(prefix):
                handler(event)
    def __call__(self, *args, **kwargs):
        """Forward calls to the wrapped method.
        
        Args:
            *args: Positional arguments to pass to wrapped method
            **kwargs: Keyword arguments to pass to wrapped method
            
        Returns:
            The result of calling the wrapped method
        """
        self._call_id += 1
        
        # Emit call event
        self._emit_event(
            EventType.CALL,
            arguments={"args": args, "kwargs": kwargs}
        )

        # Call method
        result = self._method(*args, **kwargs)

        # Emit result event
        self._emit_event(
            EventType.RESULT,
            result=result
        )

        return result

    def __repr__(self):
        return f"MethodProxy({self._method.__name__})"

class Proxy:
    """A proxy class that wraps an object and delegates attribute access.
    
    This proxy forwards all attribute access to the wrapped object. It wraps any callable
    attributes in a MethodProxy to maintain the proper context, while returning other
    attributes directly.
    """

    def __init__(self, obj, event_listeners=None, agent_id=None):
        """Initialize the proxy with an object to wrap.
        
        Args:
            obj: The object to wrap and proxy
            event_listeners: List of (prefix, handler) tuples for event handling
            agent_id: ID of the agent this proxy belongs to
        """
        self._obj = obj
        self._event_listeners = event_listeners or []
        self._agent_id = agent_id

    def __getattr__(self, name):
        """Forward attribute access to the wrapped object.
        
        Args:
            name: Name of the attribute to access
            
        Returns:
            The attribute value from the wrapped object, wrapped in a MethodProxy if callable
        """        
        attr = getattr(self._obj, name)
        if callable(attr):
            return MethodProxy(attr, self._obj, self._event_listeners, self._agent_id)
        return attr

    def __repr__(self):
        return f"Proxy({self._obj.__class__.__name__})"