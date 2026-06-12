import importlib
import inspect
import sys
import types
import typing
from typing import Any, Dict, List

import docstring_parser

from xaibo.core.models.tools import Tool, ToolParameter, ToolResult
from xaibo.core.protocols.tools import ToolProviderProtocol

import logging
logger = logging.getLogger(__name__)


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

            except ImportError as e:
                logger.warning("Failed to import tool module '%s'", package_path, exc_info=True)
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
                type=self._annotation_type_name(param.annotation),
                description=param_docs.get(param.name, ""),
                required=param.default == inspect.Parameter.empty
            )

        return Tool(
            name=self._get_tool_name(fn),
            description=docstr.description or "",
            parameters=parameters
        )

    # Python type names → JSON Schema types. Anything outside JSON Schema's
    # {string,integer,number,boolean,array,object,null} gets rejected by
    # providers with strict schema validation (OpenAI 400s the whole request
    # over a single 'Optional'/'dict'/'list' type), so unknowns degrade to
    # 'string' — never to an invalid schema.
    _JSON_SCHEMA_TYPES = {
        'str': 'string', 'int': 'integer', 'float': 'number', 'bool': 'boolean',
        'list': 'array', 'tuple': 'array', 'set': 'array', 'frozenset': 'array',
        'dict': 'object', 'mapping': 'object', 'sequence': 'array',
        'iterable': 'array', 'bytes': 'string', 'none': 'null', 'nonetype': 'null',
        'any': 'string', 'string': 'string', 'integer': 'integer',
        'number': 'number', 'boolean': 'boolean', 'array': 'array',
        'object': 'object', 'null': 'null',
    }

    @classmethod
    def _annotation_type_name(cls, annotation) -> str:
        """JSON Schema type for a parameter annotation.

        Never raises, and never emits a type outside JSON Schema's vocabulary.
        Handles real typing objects via get_origin/get_args (so
        Optional[list[str]] maps to 'array' on every Python version, instead of
        leaking 'Optional'/'Union' from __name__), plain classes, and string
        annotations (quoted, or any module using
        `from __future__ import annotations`).
        """
        if annotation is inspect.Parameter.empty:
            return "string"
        if isinstance(annotation, str):
            token = annotation.strip()
            lowered = token.lower()
            if lowered.startswith('optional[') and lowered.endswith(']'):
                return cls._annotation_type_name(token[9:-1])
            return cls._JSON_SCHEMA_TYPES.get(lowered.split('[', 1)[0], 'string')
        origin = typing.get_origin(annotation)
        union_kinds = (typing.Union, getattr(types, 'UnionType', typing.Union))
        if origin in union_kinds:
            args = [a for a in typing.get_args(annotation) if a is not type(None)]
            return cls._annotation_type_name(args[0]) if args else 'string'
        if origin is not None:
            annotation = origin
        if annotation is type(None):
            return 'null'
        name = getattr(annotation, '__name__', None) or str(annotation)
        return cls._JSON_SCHEMA_TYPES.get(name.lower(), 'string')

    def _get_tool_name(self, fn) -> str:
        """Get the full tool name including module path"""
        return (inspect.getmodule(fn).__name__ + "." + fn.__name__).replace(".", "-")

def tool(fn):
    """Decorator to mark a function as a tool"""
    setattr(fn, "__xaibo_tool__", True)
    return fn
