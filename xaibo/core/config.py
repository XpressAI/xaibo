from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str
from collections import defaultdict


class ModuleConfig(BaseModel):
    module: str
    id: str
    provides: Optional[List[str]] = None
    uses: Optional[List[str]] = None
    config: Optional[Dict] = None


class ExchangeConfig(BaseModel):
    module: str
    protocol: str
    provider: str


class AgentConfig(BaseModel):
    id: str
    modules: List[ModuleConfig]
    exchange: Optional[List[ExchangeConfig]] = None

    @classmethod
    def load_directory(cls, directory: str) -> Dict[str, "AgentConfig"]:
        """Load all agent configurations from a directory recursively.

        Args:
            directory: Path to directory containing YAML agent configurations

        Returns:
            Dictionary mapping filenames to AgentConfig instances

        Raises:
            ValueError: If any YAML files cannot be parsed as valid agent configs
        """
        import os

        configs = {}

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    full_path = os.path.join(root, file)
                    with open(full_path) as f:
                        try:
                            yaml_content = f.read()
                            config = cls.from_yaml(yaml_content)
                            configs[full_path] = config
                        except Exception as e:
                            raise ValueError(f"Invalid agent config in {full_path}: {str(e)}")

        return configs

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "AgentConfig":
        """Load an AgentConfig from a YAML string.

        Args:
            yaml_str: YAML string containing agent configuration

        Returns:
            AgentConfig instance parsed from the YAML
        """

        config = parse_yaml_raw_as(AgentConfig, yaml_str)
        config.populate_implicits()
        return config

    def to_yaml(self) -> str:
        """Convert this AgentConfig to YAML string format.

        Returns:
            YAML string representation of this config
        """

        return to_yaml_str(self)

    def populate_implicits(self):
        """Populate implicit configuration parts if not provided.

        This adds:
        - The __response__ module if not present
        - Exchange configurations for unambiguous protocol matches

        Raises:
            ValueError: If multiple providers are found for a protocol that a module uses
            ValueError: If multiple message handlers are found for a message type protocol
        """
        self._add_implicit_response_module()
        self._initialize_exchange_list()
        self._add_implicit_protocol_exchanges()
        self._add_implicit_entry_handlers()

    def _add_implicit_response_module(self):
        """Add the __response__ module if not present."""
        has_response = any(module.id == "__response__" for module in self.modules)

        if not has_response:
            response_module = ModuleConfig(
                module="xaibo.primitives.modules.ResponseHandler",
                id="__response__",
                provides=["ResponseProtocol"]
            )
            self.modules.append(response_module)

    def _initialize_exchange_list(self):
        """Initialize exchange list if None."""
        if self.exchange is None:
            self.exchange = []

    def _add_implicit_protocol_exchanges(self):
        """Add implicit exchange configurations for unambiguous protocol matches.
        
        Raises:
            ValueError: If multiple providers are found for a protocol that a module uses
        """
        # Map protocols to provider modules
        protocol_providers = self._get_protocol_providers()
        module_requirements = self._get_module_requirements()

        # First, update the 'uses' field for each module based on constructor requirements
        for module in self.modules:
            if module.id in module_requirements:
                if module.uses is None:
                    module.uses = []
                
                for param_name, param_type in module_requirements[module.id].items():
                    if param_type not in module.uses:
                        module.uses.append(param_type)

        # For each module that uses protocols
        for module in self.modules:
            if module.uses:
                for protocol in module.uses:
                    # Skip if module already has an exchange config for this protocol
                    has_config = any(ex.module == module.id and ex.protocol == protocol
                                     for ex in self.exchange)
                    if has_config:
                        continue

                    providers = protocol_providers[protocol]
                    # If there's exactly one provider for this protocol
                    if len(providers) == 1:
                        provider = providers[0]
                        self.exchange.append(ExchangeConfig(
                            module=module.id,
                            protocol=protocol,
                            provider=provider
                        ))
                    elif len(providers) > 1:
                        # Only raise if module isn't already configured
                        raise ValueError(
                            f"Multiple providers found for protocol {protocol} used by module {module.id}: {providers}"
                        )
                    
    def _get_protocol_providers(self):
        """Map protocols to provider modules.
        
        Returns:
            A defaultdict mapping protocol names to lists of provider module IDs
        """
        protocol_providers = defaultdict(list)
        for module in self.modules:
            if module.provides:
                for protocol in module.provides:
                    protocol_providers[protocol].append(module.id)
            
            # Check referenced module for provided protocols
            try:
                module_class = self._import_module_class(module.module)
                if hasattr(module_class, "provides") and callable(getattr(module_class, "provides")):
                    provided_protocols = module_class.provides()
                    for protocol_type in provided_protocols:
                        # Convert protocol type to string reference
                        protocol_name = protocol_type.__name__
                        if protocol_name not in (module.provides or []):
                            if module.provides is None:
                                module.provides = []
                            module.provides.append(protocol_name)
                            protocol_providers[protocol_name].append(module.id)
            except (ImportError, AttributeError):
                # Skip if module can't be imported or doesn't have provides method
                pass
                
        return protocol_providers
    
    def _get_module_requirements(self):
        """Analyze module constructors to determine their requirements.
        
        Returns:
            A dictionary mapping module IDs to dictionaries of parameter names and their types
        """
        import inspect
        from typing import get_type_hints
        
        module_requirements = {}
        
        for module in self.modules:
            try:
                module_class = self._import_module_class(module.module)
                if hasattr(module_class, "__init__"):
                    # Get constructor signature
                    signature = inspect.signature(module_class.__init__)
                    type_hints = get_type_hints(module_class.__init__)
                    
                    # Extract parameters that aren't self or config
                    requirements = {}
                    for param_name, param in signature.parameters.items():
                        if param_name not in ('self', 'config'):
                            # Try to get the type hint
                            if param_name in type_hints:
                                param_type = type_hints[param_name]
                                # Get the name of the type for protocol matching
                                if hasattr(param_type, "__name__"):
                                    type_name = param_type.__name__
                                    requirements[param_name] = type_name
                                elif hasattr(param_type, "_name"):
                                    # Handle Optional types
                                    type_name = str(param_type).replace("typing.Optional[", "").replace("]", "")
                                    if "." in type_name:
                                        type_name = type_name.split(".")[-1]
                                    requirements[param_name] = type_name
                    
                    if requirements:
                        module_requirements[module.id] = requirements
            except (ImportError, AttributeError):
                # Skip if module can't be imported or doesn't have __init__ method
                pass
                
        return module_requirements
    
    def _import_module_class(self, module_path: str):
        """Import a module class from its path.
        
        Args:
            module_path: The import path to the module
            
        Returns:
            The imported module class
            
        Raises:
            ImportError: If the module cannot be imported
        """
        import importlib
        
        # Split the path into module path and class name
        module_parts = module_path.split('.')
        class_name = module_parts[-1]
        module_import_path = '.'.join(module_parts[:-1])
        
        # Import the module
        module = importlib.import_module(module_import_path)
        
        # Get the class
        return getattr(module, class_name)

    def _add_implicit_entry_handlers(self):
        """Add implicit entry handlers for message protocols if unambiguous.
        
        Raises:
            ValueError: If multiple message handlers are found for a message type protocol
        """
        message_handlers = self._get_message_handlers()

        for protocol, handlers in message_handlers.items():
            # Skip if __entry__ already has an exchange config for this protocol
            has_config = any(ex.module == "__entry__" and ex.protocol == protocol
                             for ex in self.exchange)
            if has_config:
                continue

            if len(handlers) == 1:
                self.exchange.append(ExchangeConfig(
                    module="__entry__",
                    protocol=protocol,
                    provider=handlers[0]
                ))
            elif len(handlers) > 1:
                # Only raise if __entry__ isn't already configured
                raise ValueError(
                    f"Multiple handlers found for message protocol {protocol}: {handlers}"
                )

    def _get_message_handlers(self):
        """Get mapping of message handler protocols to implementing modules.
        
        Returns:
            A dictionary mapping message handler protocol names to lists of module IDs
        """
        message_handlers = {
            "TextMessageHandlerProtocol": [],
            "ImageMessageHandlerProtocol": [],
            "AudioMessageHandlerProtocol": [],
            "VideoMessageHandlerProtocol": []
        }

        for module in self.modules:
            if module.provides:
                for protocol in module.provides:
                    if protocol in message_handlers:
                        message_handlers[protocol].append(module.id)
                        
        return message_handlers