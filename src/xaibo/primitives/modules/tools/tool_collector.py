from typing import Dict, Any, List

from xaibo.core.models import ToolResult, Tool
from xaibo.core.protocols import ToolProviderProtocol


class ToolCollector(ToolProviderProtocol):
    def __init__(self, tool_providers: list[ToolProviderProtocol], config: dict[str, Any] = None):
        self.tool_providers = tool_providers

    async def list_tools(self) -> List[Tool]:
        res = []
        for provider in self.tool_providers:
            res.extend(await provider.list_tools())
        return res

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        for provider in self.tool_providers:
            tools = await provider.list_tools()
            if any(tool.name == tool_name for tool in tools):
                return await provider.execute_tool(tool_name, parameters)
        return ToolResult(
            success=False,
            error=f"Could not find {tool_name}"
        )
