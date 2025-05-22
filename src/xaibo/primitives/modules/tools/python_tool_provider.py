import importlib
import inspect
import sys
from typing import Any, Dict, List

import docstring_parser

from xaibo.core.models.tools import Tool, ToolParameter, ToolResult
from xaibo.core.protocols.tools import ToolProviderProtocol


class PythonToolProvider(ToolProviderProtocol):
    """Provider for Python function-based tools"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration
        
        Args:
            config: Configuration dictionary containing:
                tool_packages: List of Python package paths containing tool functions
                tool_functions: Optional list of function objects to use as tools
        """
        self.tool_packages = config.get("tool_packages", [])
        self.tool_functions = config.get("tool_functions", [])

    async def list_tools(self) -> List[Tool]:
        """List all available tools from the configured packages and functions"""
        tools = []
        
        # Get tools from packages
        for package_path in self.tool_packages:
            try:
                if package_path in sys.modules:
                    pkg = importlib.reload(sys.modules[package_path])
                else:
                    pkg = importlib.import_module(package_path)
                    
                # Find all functions marked as tools
                for obj in pkg.__dict__.values():
                    if hasattr(obj, "__xaibo_tool__"):
                        tools.append(self._function_to_tool(obj))
            except ImportError:
                # Skip packages that don't exist
                continue
        
        # Get tools from directly provided functions
        for func in self.tool_functions:
            if callable(func):
                # Mark the function as a tool if not already marked
                if not hasattr(func, "__xaibo_tool__"):
                    setattr(func, "__xaibo_tool__", True)
                tools.append(self._function_to_tool(func))
        
        return tools

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool with the given parameters
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        # Check directly provided functions first
        for func in self.tool_functions:
            if (hasattr(func, "__xaibo_tool__") and 
                self._get_tool_name(func) == tool_name):
                try:
                    result = func(**parameters)
                    return ToolResult(success=True, result=result)
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=str(e)
                    )
        
        # Then check package-based tools
        for package_path in self.tool_packages:
            try:
                pkg = importlib.import_module(package_path)
                for obj in pkg.__dict__.values():
                    if (hasattr(obj, "__xaibo_tool__") and 
                        self._get_tool_name(obj) == tool_name):
                        try:
                            result = obj(**parameters)
                            return ToolResult(success=True, result=result)
                        except Exception as e:
                            return ToolResult(
                                success=False,
                                error=str(e)
                            )
            except ImportError:
                # Skip packages that don't exist
                continue
        
        return ToolResult(
            success=False,
            error=f"Tool {tool_name} not found"
        )

    def _function_to_tool(self, fn) -> Tool:
        """Convert a Python function to a Tool definition"""
        docstr = docstring_parser.parse(inspect.getdoc(fn))
        param_docs = {p.arg_name: p.description for p in docstr.params}
        
        parameters = {}
        for param in inspect.signature(fn).parameters.values():
            parameters[param.name] = ToolParameter(
                type=param.annotation.__name__ if param.annotation != inspect._empty else "any",
                description=param_docs.get(param.name, ""),
                required=param.default == inspect.Parameter.empty
            )
            if parameters[param.name].type == 'str':
                parameters[param.name].type = 'string'
            elif parameters[param.name].type == 'int':
                parameters[param.name].type = 'integer'

        return Tool(
            name=self._get_tool_name(fn),
            description=docstr.description or "",
            parameters=parameters
        )

    def _get_tool_name(self, fn) -> str:
        """Get the full tool name including module path"""
        return (inspect.getmodule(fn).__name__ + "." + fn.__name__).replace(".", "-")

def tool(fn):
    """Decorator to mark a function as a tool"""
    setattr(fn, "__xaibo_tool__", True)
    return fn
