from typing import Dict, Any, List, Optional
import uuid

from xaibo.core.protocols.memory import MemoryProtocol, MemorySearchResult
from xaibo.core.protocols.tools import ToolProviderProtocol
from xaibo.core.models.tools import Tool, ToolResult, ToolParameter


class MemoryToolProvider(ToolProviderProtocol):
    """
    Tool provider that exposes memory functionality through tools.
    Implements ToolProviderProtocol to provide memory-related tools.
    """

    def __init__(self, memory_provider: MemoryProtocol, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory tool provider with a memory provider.
        
        Args:
            memory_provider: An implementation of MemoryProtocol
        """
        self.memory_provider = memory_provider
        self._tools = self._initialize_tools()

    def _initialize_tools(self) -> List[Tool]:
        """Initialize the list of available tools"""
        return [
            Tool(
                name="store_memory",
                description="Store a new memory in the system",
                parameters={
                    "text": ToolParameter(
                        type="string",
                        description="Text content to store in memory",
                        required=True
                    ),
                    "attributes": ToolParameter(
                        type="object",
                        description="Optional metadata attributes for the memory. Useful for adding information about the source of the memory, etc.",
                        required=False
                    )
                }
            ),
            Tool(
                name="get_memory",
                description="Retrieve a specific memory by ID",
                parameters={
                    "memory_id": ToolParameter(
                        type="string",
                        description="ID of the memory to retrieve",
                        required=True
                    )
                }
            ),
            Tool(
                name="search_memory",
                description="Search memories semantically using a text query",
                parameters={
                    "query": ToolParameter(
                        type="string",
                        description="Search query text",
                        required=True
                    ),
                    "k": ToolParameter(
                        type="integer",
                        description="Number of results to return",
                        default=10,
                        required=False
                    )
                }
            ),
            Tool(
                name="list_memories",
                description="List all stored memories",
                parameters={}
            ),
            Tool(
                name="delete_memory",
                description="Delete a memory by ID",
                parameters={
                    "memory_id": ToolParameter(
                        type="string",
                        description="ID of the memory to delete",
                        required=True
                    )
                }
            ),
            Tool(
                name="update_memory",
                description="Update an existing memory",
                parameters={
                    "memory_id": ToolParameter(
                        type="string",
                        description="ID of the memory to update",
                        required=True
                    ),
                    "text": ToolParameter(
                        type="string",
                        description="New text content",
                        required=True
                    ),
                    "attributes": ToolParameter(
                        type="object",
                        description="Optional new metadata attributes. Useful for adding information about the source of the memory, etc.",
                        required=False
                    )
                }
            )
        ]

    async def list_tools(self) -> List[Tool]:
        """
        List all available memory-related tools.
        
        Returns:
            List of Tool objects representing available memory operations
        """
        return self._tools

    def _create_error_result(self, message: str) -> ToolResult:
        """Create an error result"""
        return ToolResult(success=False, error=message)

    def _create_success_result(self, result: Any) -> ToolResult:
        """Create a success result"""
        return ToolResult(success=True, result=result)

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute a memory-related tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool execution
            
        Returns:
            ToolResult containing the result of the operation
        """
        try:
            handlers = {
                "store_memory": self._handle_store_memory,
                "get_memory": self._handle_get_memory,
                "search_memory": self._handle_search_memory,
                "list_memories": self._handle_list_memories,
                "delete_memory": self._handle_delete_memory,
                "update_memory": self._handle_update_memory
            }

            handler = handlers.get(tool_name)
            if not handler:
                return self._create_error_result(f"Unknown tool: {tool_name}")

            return await handler(parameters)

        except Exception as e:
            return self._create_error_result(f"Error executing tool {tool_name}: {str(e)}")

    async def _handle_store_memory(self, parameters: Dict[str, Any]) -> ToolResult:
        memory_id = await self.memory_provider.store_memory(
            parameters["text"],
            parameters.get("attributes")
        )
        return self._create_success_result({"memory_id": memory_id})

    async def _handle_get_memory(self, parameters: Dict[str, Any]) -> ToolResult:
        memory_id = parameters["memory_id"]
        memory = await self.memory_provider.get_memory(memory_id)
        if memory is None:
            return self._create_error_result(f"Memory with ID {memory_id} not found")
        return self._create_success_result(memory)

    async def _handle_search_memory(self, parameters: Dict[str, Any]) -> ToolResult:
        results = await self.memory_provider.search_memory(
            parameters["query"],
            parameters.get("k", 10)
        )
        result_dicts = [
            {
                "memory_id": r.memory_id,
                "content": r.content,
                "similarity_score": r.similarity_score,
                "attributes": r.attributes
            }
            for r in results
        ]
        return self._create_success_result(result_dicts)

    async def _handle_list_memories(self, parameters: Dict[str, Any]) -> ToolResult:
        memories = await self.memory_provider.list_memories()
        return self._create_success_result(memories)

    async def _handle_delete_memory(self, parameters: Dict[str, Any]) -> ToolResult:
        memory_id = parameters["memory_id"]
        success = await self.memory_provider.delete_memory(memory_id)
        if not success:
            return self._create_error_result(
                f"Memory with ID {memory_id} not found or could not be deleted"
            )
        return self._create_success_result({"deleted": memory_id})

    async def _handle_update_memory(self, parameters: Dict[str, Any]) -> ToolResult:
        memory_id = parameters["memory_id"]
        success = await self.memory_provider.update_memory(
            memory_id,
            parameters["text"],
            parameters.get("attributes")
        )
        if not success:
            return self._create_error_result(
                f"Memory with ID {memory_id} not found or could not be updated"
            )
        return self._create_success_result({"updated": memory_id})
