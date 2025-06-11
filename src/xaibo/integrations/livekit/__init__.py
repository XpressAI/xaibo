"""Xaibo plugin for LiveKit Agents

Integration with Xaibo for advanced conversational AI capabilities.
"""

from .log import logger
from .version import __version__
from .llm import XaiboLLM, XaiboLLMStream
from .agent_loader import XaiboAgentLoader

__all__ = [
    "logger",
    "__version__",
    "XaiboLLM",
    "XaiboLLMStream",
    "XaiboAgentLoader",
]

from livekit.agents import Plugin


class XaiboPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__(__name__, __version__, __package__, logger)


Plugin.register_plugin(XaiboPlugin())

# Cleanup docs of unexported modules
_module = dir()
NOT_IN_ALL = [m for m in _module if m not in __all__]

__pdoc__ = {}

for n in NOT_IN_ALL:
    __pdoc__[n] = False