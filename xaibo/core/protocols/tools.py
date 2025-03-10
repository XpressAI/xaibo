from typing import Protocol, List, Dict, Any, runtime_checkable

from xaibo.core.models.tools import Tool, ToolResult

@runtime_checkable
class ToolProviderProtocol(Protocol):
    """Protocol for providing and executing tools"""
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools provided by this provider"""
        ...
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool with the given parameters"""
        ...
