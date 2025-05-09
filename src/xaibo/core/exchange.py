from collections import defaultdict
from typing import Type, Union
from typing_extensions import get_origin
from .config import AgentConfig, ModuleConfig
from xaibo.core.models import EventType, Event
import time

import traceback


class ExchangeRedone:
    """Handles module instantiation and dependency injection for agents."""

    def __init__(self, config: AgentConfig = None, override_bindings: dict[Union[str, Type], any] = None,
                 event_listeners: list[tuple[str, callable]] = None):
        """Initialize the exchange and optionally instantiate modules.

        Args:
            config (AgentConfig, optional): The agent configuration to instantiate modules from. Defaults to None.
            override_bindings (dict[Union[str, Type], any], optional): Custom bindings to override defaults. Defaults to None.
            event_listeners (list[tuple[str, callable]], optional): Event listeners to register. Defaults to None.
        """
        self.module_instances = {}
        self.overrides = {}
        self.event_listeners = event_listeners or []
        self.config = config
        if config:
            self._instantiate_modules(override_bindings or {})

    def _instantiate_modules(self, override_bindings: dict[Union[str, Type], any]) -> None:
        """Create instances of all modules defined in config."""
        module_mapping = {
            module.id: module
            for module in self.config.modules
        }
        dependency_mapping = {
            module.id: self._get_module_dependencies(module)
            for module in self.config.modules
        }

        module_order = [module.id for module in self.config.modules]
        # presort modules based on dependencies
        module_order.sort(key=lambda x: len(dependency_mapping[x]))

        # sort such that dependencies are met first
        i = 0
        while i < len(module_order):
            current_module_id = module_order[i]
            cur_dependencies = dependency_mapping[current_module_id]
            if len(cur_dependencies) > 0:
                highest_dependency_idx = max(module_order.index(m)  for m in cur_dependencies)
                if highest_dependency_idx > i:
                    module_order[i], module_order[highest_dependency_idx] = module_order[highest_dependency_idx], module_order[i]
                    continue
            i = i + 1

        for module_id in module_order:
            module_config = module_mapping[module_id]
            dependencies = dependency_mapping[module_id]

            #get module class
            module_class = self.config._import_module_class(module_config.module)

            # 




    def _get_module_dependencies(self, module_config: ModuleConfig) -> dict[str, list[str]]:
        """Get dependencies for a module from exchange config.
        """
        module_class = self.config._import_module_class(module_config.module)

        dependencies = {
            param: [] for param, _ in module_class.__init__.__annotations__
        }

        types = defaultdict(list)
        for param, type_hint in module_class.__init__.__annotations__:
            types[type_hint].append(param)

        relevant_exchange_configs = [e for e in self.config.exchange if e.module == module_config.id]
        for exchange_config in relevant_exchange_configs:
            if exchange_config.field_name is not None:
                param_list = [dependencies[exchange_config.field_name]]
            else:
                param_list = types[exchange_config.protocol]
            for param in param_list:
                if isinstance(exchange_config.provider, list):
                    dependencies[param].extend(exchange_config.provider)
                else:
                    dependencies[param].append(exchange_config.provider)
        return dependencies




class Exchange:
    """Handles module instantiation and dependency injection for agents."""

    def __init__(self, config: AgentConfig = None, override_bindings: dict[Union[str, Type], any] = None, event_listeners: list[tuple[str, callable]] = None):
        """Initialize the exchange and optionally instantiate modules.
        
        Args:
            config (AgentConfig, optional): The agent configuration to instantiate modules from. Defaults to None.
            override_bindings (dict[Union[str, Type], any], optional): Custom bindings to override defaults. Defaults to None.
            event_listeners (list[tuple[str, callable]], optional): Event listeners to register. Defaults to None.
        """
        self.module_instances = {}
        self.overrides = {}
        self.event_listeners = event_listeners or []
        self.config = config
        if config:
            self._instantiate_modules(override_bindings or {})

    def _instantiate_modules(self, override_bindings: dict[Union[str, Type], any]) -> None:
        """Create instances of all modules defined in config."""
        self.module_instances = {}        

        # Process override bindings as pre-instantiated modules
        for idx, (binding_protocol, binding_value) in enumerate(override_bindings.items()):
            # Create a unique ID for each override binding
            override_id = f"override_{idx}"
            self.module_instances[override_id] = binding_value
            self.overrides[binding_protocol] = override_id


        
        # Keep track of modules that still need to be instantiated
        remaining_modules = set(module_config.id for module_config in self.config.modules)
        
        # Continue until all modules are instantiated or no progress is made
        while remaining_modules:
            progress_made = False
            
            # Try to instantiate any module whose dependencies are satisfied
            for module_config in self.config.modules:
                if module_config.id not in remaining_modules:
                    continue  # Already instantiated
                
                # Check if this module has no dependencies or all dependencies are already instantiated
                dependencies_satisfied = True
                required_dependencies = []
                
                if module_config.uses:
                    # Find all dependencies for this module
                    for exchange in self.config.exchange:
                        if exchange.module == module_config.id:
                            if exchange.provider not in self.module_instances:
                                dependencies_satisfied = False
                                required_dependencies.append(exchange.provider)
                
                if not module_config.uses or dependencies_satisfied:
                    # All dependencies are available, instantiate this module
                    module_class = self.config._import_module_class(module_config.module)
                    
                    if module_config.uses:
                        dependencies = self._get_module_dependencies(module_config, module_class)
                        dependencies.update(self._get_overrides_by_type(module_class))
                        
                        self.module_instances[module_config.id] = module_class(
                            **(self._get_proxied_dependencies(module_config, dependencies)),
                            config=module_config.config
                        )
                    else:
                        self.module_instances[module_config.id] = module_class(
                            config=module_config.config
                        )
                    
                    remaining_modules.remove(module_config.id)
                    progress_made = True

            # If no progress was made in this iteration, we have a circular dependency
            if not progress_made and remaining_modules:
                raise ValueError(f"Circular dependency detected among modules: {remaining_modules}")
        
        self.module_instances['__entry__'] = self._get_entry_module(self.module_instances)        
    
    def _get_module_dependencies(self, module_config: any, module_class: any) -> dict[str, any]:
        """Get dependencies for a module from exchange config.
        
        Args:
            module_config (any): The module configuration containing ID and dependency info
            module_class (any): The module class to get dependencies for
            
        Returns:
            dict[str, any]: Dictionary mapping parameter names to module instances
            
        Raises:
            ValueError: If multiple parameters match a protocol or no matching parameter is found
        """
        dependencies = {}
        for exchange in self.config.exchange:
            if exchange.module == module_config.id:
                params = module_class.__init__.__annotations__
                matching_params = [
                    param for param, type_hint in params.items()
                    if isinstance(self.module_instances[exchange.provider], type_hint)
                ]

                if len(matching_params) > 1:
                    raise ValueError(f"Multiple parameters match protocol {exchange.protocol} in module {module_config.id}")
                elif len(matching_params) == 0:
                    raise ValueError(f"No parameter found matching protocol {exchange.protocol} and type of {exchange.provider} in module {module_config.id}")

                dependencies[matching_params[0]] = self.module_instances[exchange.provider]
        return dependencies

    def _get_overrides_by_type(self, module_class: any) -> dict[str, any]:
        """Map override bindings to module parameters based on type matching."""
        params = module_class.__init__.__annotations__
        dependencies = {}

        for param_name, param_type in params.items():
            # Check for direct type match
            if param_type in self.overrides:
                dependencies[param_name] = self.module_instances[self.overrides[param_type]]
            # Check for string type name match
            elif param_type.__name__ in self.overrides:
                dependencies[param_name] = self.module_instances[self.overrides[param_type.__name__]]
        return dependencies

    def _get_entry_module(self, module_instances: dict[str, any]) -> any:
        """Get the entry module from exchange config."""
        entry_module = None
        for exchange in self.config.exchange:
            if exchange.module == "__entry__":
                if entry_module is not None:
                    raise ValueError("Multiple message handlers found")
                entry_module = module_instances[exchange.provider]

        if entry_module is None:
            raise ValueError("No message handler found in exchange config")

        return entry_module

    def _get_proxied_dependencies(self, module_config: ModuleConfig, module_instances: dict[str, any]) -> dict[str, any]:
        """Get proxied dependencies for module from exchange config."""
        module_keys = {module: key for (key, module) in self.module_instances.items()}


        return {
            key: Proxy(value, event_listeners=self.event_listeners, agent_id=self.config.id, caller_id=module_config.id, module_id=module_keys[value])
            for key, value in module_instances.items()
        }
    
    def get_module(self, module_name: str, caller_id: str):
        """Get a module in this exchange.
        
        Args:
            module_name (str): The name of the module to retrieve
            caller_id (str): Id of the module requesting this.
            
        Returns:
            The module instance or None if not found
        """        
        module = self.module_instances.get(module_name)    
        if module:
            return Proxy(module, event_listeners=self.event_listeners, agent_id=self.config.id, caller_id=caller_id, module_id=module_name)

class MethodProxy:
    """A proxy class that wraps a method and delegates calls.
    
    This proxy forwards method calls to the wrapped method. It maintains a reference 
    to the parent object to preserve the method's context and emits events to registered listeners.
    """

    def __init__(self, method, parent, event_listeners=None, agent_id=None, caller_id=None, module_id=None):
        """Initialize the method proxy.
        
        Args:
            method: The method to wrap and proxy
            parent: The parent object that owns this method
            event_listeners: List of (prefix, handler) tuples for event handling
            agent_id: ID of the agent this method belongs to
            caller_id: ID of the method caller
            module_id: ID of the called module
        """
        self._method = method
        self._parent = parent
        self._event_listeners = event_listeners or []
        self._call_id = 0
        self._agent_id = agent_id
        self._caller_id = caller_id
        self._module_id = module_id

    def _emit_event(self, event_type: EventType, result=None, arguments=None, exception=None):
        """Emit an event to all registered listeners.
        
        Args:
            event_type: Type of event (CALL or RESULT)
            result: Optional result value for RESULT events
            arguments: Optional arguments for CALL events
            exception: Optional exception for EXCEPTION events
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
            exception=exception,
            call_id=f"{id(self._parent)}-{id(self._method)}-{self._call_id}",
            agent_id=self._agent_id,
            caller_id=self._caller_id,
            module_id=self._module_id
        )

        for prefix, handler in self._event_listeners:
            if not prefix or event.event_name.startswith(prefix):
                try:
                    handler(event)
                except:
                    print("Exception during event handling")
                    traceback.print_exc()
                
    async def __call__(self, *args, **kwargs):
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

        try:
            # Call method
            result = await self._method(*args, **kwargs)
        except:
            self._emit_event(
                EventType.EXCEPTION,
                exception=traceback.format_exc()
            )
            traceback.print_exc()
            raise


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

    def __init__(self, obj, event_listeners=None, agent_id=None, caller_id=None, module_id=None):
        """Initialize the proxy with an object to wrap.
        
        Args:
            obj: The object to wrap and proxy
            event_listeners: List of (prefix, handler) tuples for event handling
            agent_id: ID of the agent this proxy belongs to
            caller_id: ID of the calling module
            module_id: ID of the called module
        """
        self._obj = obj
        self._event_listeners = event_listeners or []
        self._agent_id = agent_id
        self._caller_id = caller_id
        self._module_id = module_id

    def __getattr__(self, name):
        """Forward attribute access to the wrapped object.
        
        Args:
            name: Name of the attribute to access
            
        Returns:
            The attribute value from the wrapped object, wrapped in a MethodProxy if callable
        """        
        attr = getattr(self._obj, name)
        if callable(attr):
            return MethodProxy(attr, self._obj, self._event_listeners, self._agent_id, self._caller_id, self._module_id)
        return attr

    def __repr__(self):
        return f"Proxy({self._obj.__class__.__name__})"