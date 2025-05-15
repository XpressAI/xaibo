from itertools import chain
from collections import defaultdict
from typing import Type, Union, Any
from typing_extensions import get_origin, get_args
from .config import AgentConfig, ModuleConfig, ConfigOverrides, ExchangeConfig
from .models import EventType, Event
import time

import traceback


class Exchange:
    """Handles module instantiation and dependency injection for agents."""

    def __init__(self,
                 config: AgentConfig = None,
                 override_config: ConfigOverrides = None,
                 event_listeners: list[tuple[str, callable]] = None,
                 specific_modules: list[str] = None):
        """Initialize the exchange and optionally instantiate modules.

        Args:
            config (AgentConfig, optional): The agent configuration to instantiate modules from. Defaults to None.
            override_config (ConfigOverrides, optional): Custom bindings to override defaults. Defaults to None.
            event_listeners (list[tuple[str, callable]], optional): Event listeners to register. Defaults to None.
            specific_modules (list[str], optional): List of specific module ids that should be instantiated. Defaults to None.
        """
        self.module_instances: dict[str, object] = {
            '__exchange__': self
        }
        self.overrides = override_config
        self.event_listeners = event_listeners or []
        self.config = config

        if config:
            self.config.exchange = [ex for ex in self.config.exchange]
            self.config.exchange.append(ExchangeConfig(
                protocol=Exchange,
                provider='__exchange__'
            ))
            if self.overrides:
                self.module_instances.update(self.overrides.instances)
                for ex in self.overrides.exchange:
                    conflicts = [cx for cx in self.config.exchange if cx.module == ex.module and cx.protocol == ex.protocol and cx.field_name == ex.field_name]
                    for conflict in conflicts:
                        self.config.exchange.remove(conflict)
                    self.config.exchange.append(ex)
            self._instantiate_modules(specific_modules)

    def get_entry_point_ids(self):
        for exchange in self.config.exchange:
            if exchange.module == "__entry__":
                if isinstance(exchange.provider, list):
                    return exchange.provider
                else:
                    return [exchange.provider]
        return []

    def _instantiate_modules(self, specific_modules: list[str]) -> None:
        """Create instances of all modules defined in config."""
        # make it easy to access a module by id
        module_mapping = {
            module.id: module
            for module in self.config.modules
        }

        # figure out what the module really depends on
        dependency_mapping = {
            module.id: self._get_module_dependencies(module)
            for module in self.config.modules
        }
        # modules that have already been instantiated don't depend on anything
        for module_id in self.module_instances:
            dependency_mapping[module_id] = {}

        if specific_modules is None:
            # Collect all known module ids
            module_order = [module.id for module in self.config.modules] + [module_id for module_id in self.module_instances]
        else:
            # only instantiate those specific modules and their dependencies
            module_order = set(module_id for module_id in specific_modules)
            for module_id in specific_modules:
                cur_deps = dependency_mapping[module_id]
                for deps in cur_deps.values():
                    module_order.update(deps)
            module_order = list(module_order)

        # presort modules based on their dependency count
        module_order.sort(key=lambda x: len(dependency_mapping[x]))

        # sort modules such that dependencies will be instantiated before their dependents
        i = 0
        while i < len(module_order):
            current_module_id = module_order[i]
            cur_dependencies = set(chain(*dependency_mapping[current_module_id].values()))
            if len(cur_dependencies) > 0:
                highest_dependency_idx = max(module_order.index(m) for m in cur_dependencies)
                if highest_dependency_idx > i:
                    module_order[i], module_order[highest_dependency_idx] = module_order[highest_dependency_idx], module_order[i]
                    continue
            i = i + 1

        # instantiate modules in correct order
        for module_id in module_order:
            if module_id in self.module_instances:
                # skip already instantiated modules (e.g. from overrides or other lifecycles)
                continue

            module_config = module_mapping[module_id]
            dependencies = dependency_mapping[module_id]

            module_class = self.config._import_module_class(module_config.module)

            init_parameters = {}
            for (param, param_type) in self._get_module_parameters(module_class):
                dependency_ids = dependencies[param]
                # ensure that list type parameters are handled off as a list
                if get_origin(param_type) is list:
                    init_parameters[param] = [self.get_module(did, module_id, raise_on_not_found=True) for did in dependency_ids]
                # ... and others are singleton lists that are unpacked
                else:
                    if len(dependency_ids) != 1:
                        raise ValueError(f"Expected to find exactly one dependency resolution for module `{module_id}` parameter `{param}`, but found {len(dependency_ids)} `{repr(dependency_ids)}`")
                    init_parameters[param] = self.get_module(dependency_ids[0], module_id, raise_on_not_found=True)

            self.module_instances[module_id] = module_class(**init_parameters, config=module_config.config)

    def _get_module_dependencies(self, module_config: ModuleConfig) -> dict[str, list[str]]:
        """Get dependencies for a module from exchange config.
        """
        module_class = self.config._import_module_class(module_config.module)

        types = defaultdict(list)
        dependencies = {}
        for param, type_hint in self._get_module_parameters(module_class):
            args = get_args(type_hint)
            if len(args) == 0:
                types[type_hint.__name__].append(param)
            else:
                types[args[0].__name__].append(param)

            dependencies[param] = []

        # When an override exchange does not provide a module, it is meant for all modules
        relevant_exchange_configs = [e for e in self.config.exchange if e.module == module_config.id or e.module is None]
        for exchange_config in relevant_exchange_configs:
            if exchange_config.field_name is not None:
                param_list = [exchange_config.field_name]
            else:
                param_list = types[exchange_config.protocol]
            for param in param_list:
                if isinstance(exchange_config.provider, list):
                    dependencies[param].extend(exchange_config.provider)
                else:
                    dependencies[param].append(exchange_config.provider)
        return dependencies

    def _get_module_parameters(self, module_class):
        """Get the injectable parameters for the given module class."""
        return ((param, param_type) for (param, param_type) in module_class.__init__.__annotations__.items() if param != 'config')

    def _get_entry_module_id(self) -> Any:
        """Get the entry module from exchange config."""
        for exchange in self.config.exchange:
            if exchange.module == "__entry__":
                return exchange.provider
        raise ValueError("No message handler found in exchange config")

    def get_module(self, module_id: str, caller_id: str, raise_on_not_found: bool = False):
        """Get a module in this exchange.

        Args:
            module_id (str): The name of the module to retrieve
            caller_id (str): Id of the module requesting this.
            raise_on_not_found (bool): Raise an exception if module was not found instead of returning None

        Returns:
            The module instance or None if not found
        """
        if module_id == '__entry__':
            module_id = self._get_entry_module_id()
        module = self.module_instances.get(module_id)

        if module:
            return Proxy(module,
                         event_listeners=self.event_listeners,
                         agent_id=self.config.id,
                         caller_id=caller_id,
                         module_id=module_id)
        else:
            if raise_on_not_found:
                raise ValueError(f"Requested module {module_id} could not be found!")
            return None


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