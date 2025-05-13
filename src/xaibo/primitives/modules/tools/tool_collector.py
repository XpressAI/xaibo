from typing import Dict, Any, List

from xaibo.core.models import ToolResult, Tool
from xaibo.core.protocols import ToolProviderProtocol


class ToolCollector(ToolProviderProtocol):
    def __init__(self, tool_providers: list[ToolProviderProtocol], config: dict[str, Any] = None):
        self.tool_providers = tool_providers
        self.tool_cache = {}

    async def list_tools(self) -> List[Tool]:
        self.tool_cache = {}
        res = []
        for provider in self.tool_providers:
            tools = await provider.list_tools()
            res.extend(tools)
            for tool in tools:
                self.tool_cache[tool.name] = provider
        return res

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        if len(self.tool_cache) == 0:
            await self._fill_cache()
        provider = self.tool_cache.get(tool_name)
        if provider is not None:
            return await provider.execute_tool(tool_name, parameters)
        return ToolResult(
            success=False,
            error=f"Could not find {tool_name}"
        )

    async def _fill_cache(self):
        self.tool_cache = {}
        for provider in self.tool_providers:
            tools = await provider.list_tools()
            for tool in tools:
                self.tool_cache[tool.name] = provider
