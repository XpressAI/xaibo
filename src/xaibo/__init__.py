try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("xaibo")
except PackageNotFoundError:
    __version__ = "unknown"

from .core import AgentConfig, ModuleConfig, ExchangeConfig, Registry, Agent, Xaibo, ConfigOverrides

__all__ = [
    "__version__",
    "AgentConfig", 
    "ModuleConfig", 
    "ExchangeConfig", 
    "Registry", 
    "Agent", 
    "Xaibo", 
    "ConfigOverrides"
]