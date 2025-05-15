import pytest
from typing import Dict, Any, List, Optional
import uuid
from unittest.mock import AsyncMock

from xaibo.core.protocols.memory import MemoryProtocol, MemorySearchResult
from xaibo.core.models.tools import Tool, ToolResult, ToolParameter
from xaibo.primitives.modules.memory.memory_provider import MemoryToolProvider


class MockMemoryProvider(MemoryProtocol):
    """Mock implementation of MemoryProtocol for testing"""
    
    def __init__(self):
        self.memories = {}
        
    async def store_memory(self, text: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        memory_id = str(uuid.uuid4())
        self.memories[memory_id] = {"text": text, "attributes": attributes or {}}
        return memory_id
        
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self.memories.get(memory_id)
        
    async def search_memory(self, query: str, k: int = 10) -> List[MemorySearchResult]:
        results = []
        for memory_id, memory in self.memories.items():
            results.append(
                MemorySearchResult(
                    memory_id=memory_id,
                    content=memory["text"],
                    similarity_score=0.9,  # Mock similarity score
                    attributes=memory["attributes"]
                )
            )
            if len(results) >= k:
                break
        return results
        
    async def list_memories(self) -> List[Dict[str, Any]]:
        return [
            {"memory_id": memory_id, **memory}
            for memory_id, memory in self.memories.items()
        ]
        
    async def delete_memory(self, memory_id: str) -> bool:
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False
        
    async def update_memory(self, memory_id: str, text: str, attributes: Optional[Dict[str, Any]] = None) -> bool:
        if memory_id in self.memories:
            self.memories[memory_id] = {
                "text": text,
                "attributes": attributes or self.memories[memory_id].get("attributes", {})
            }
            return True
        return False


@pytest.fixture
def memory_provider():
    return MockMemoryProvider()


@pytest.fixture
def memory_tool_provider(memory_provider):
    return MemoryToolProvider(memory_provider)


@pytest.mark.asyncio    
async def test_list_tools( memory_tool_provider):
    tools = await memory_tool_provider.list_tools()
    assert len(tools) == 6
    tool_names = [tool.name for tool in tools]
    assert "store_memory" in tool_names
    assert "get_memory" in tool_names
    assert "search_memory" in tool_names
    assert "list_memories" in tool_names
    assert "delete_memory" in tool_names
    assert "update_memory" in tool_names

@pytest.mark.asyncio
async def test_store_memory( memory_tool_provider):
    result = await memory_tool_provider.execute_tool("store_memory", {
        "text": "Test memory",
        "attributes": {"category": "test"}
    })

    assert result.success is True
    assert "memory_id" in result.result

@pytest.mark.asyncio
async def test_get_memory( memory_tool_provider, memory_provider):
    # Store a memory first
    memory_id = await memory_provider.store_memory("Test memory", {"category": "test"})

    # Get the memory
    result = await memory_tool_provider.execute_tool("get_memory", {
        "memory_id": memory_id
    })

    assert result.success is True
    assert result.result["text"] == "Test memory"
    assert result.result["attributes"]["category"] == "test"

@pytest.mark.asyncio
async def test_get_nonexistent_memory( memory_tool_provider):
    result = await memory_tool_provider.execute_tool("get_memory", {
        "memory_id": "nonexistent-id"
    })

    assert result.success is False
    assert "not found" in result.error

@pytest.mark.asyncio
async def test_search_memory( memory_tool_provider, memory_provider):
    # Store some memories
    await memory_provider.store_memory("First test memory", {"category": "test"})
    await memory_provider.store_memory("Second test memory", {"category": "test"})

    # Search memories
    result = await memory_tool_provider.execute_tool("search_memory", {
        "query": "test memory",
        "k": 2
    })

    assert result.success is True
    assert len(result.result) <= 2
    assert result.result[0]["content"] in ["First test memory", "Second test memory"]

@pytest.mark.asyncio
async def test_list_memories( memory_tool_provider, memory_provider):
    # Store some memories
    await memory_provider.store_memory("Memory 1", {"category": "test"})
    await memory_provider.store_memory("Memory 2", {"category": "test"})

    # List memories
    result = await memory_tool_provider.execute_tool("list_memories", {})

    assert result.success is True
    assert len(result.result) == 2

@pytest.mark.asyncio
async def test_delete_memory( memory_tool_provider, memory_provider):
    # Store a memory
    memory_id = await memory_provider.store_memory("Test memory", {"category": "test"})

    # Delete the memory
    result = await memory_tool_provider.execute_tool("delete_memory", {
        "memory_id": memory_id
    })

    assert result.success is True
    assert result.result["deleted"] == memory_id

    # Verify it's deleted
    assert await memory_provider.get_memory(memory_id) is None

@pytest.mark.asyncio
async def test_delete_nonexistent_memory( memory_tool_provider):
    result = await memory_tool_provider.execute_tool("delete_memory", {
        "memory_id": "nonexistent-id"
    })

    assert result.success is False
    assert "not found" in result.error

@pytest.mark.asyncio
async def test_update_memory( memory_tool_provider, memory_provider):
    # Store a memory
    memory_id = await memory_provider.store_memory("Original text", {"category": "test"})

    # Update the memory
    result = await memory_tool_provider.execute_tool("update_memory", {
        "memory_id": memory_id,
        "text": "Updated text",
        "attributes": {"category": "updated"}
    })

    assert result.success is True
    assert result.result["updated"] == memory_id

    # Verify it's updated
    updated_memory = await memory_provider.get_memory(memory_id)
    assert updated_memory["text"] == "Updated text"
    assert updated_memory["attributes"]["category"] == "updated"

@pytest.mark.asyncio
async def test_update_nonexistent_memory( memory_tool_provider):
    result = await memory_tool_provider.execute_tool("update_memory", {
        "memory_id": "nonexistent-id",
        "text": "Updated text"
    })

    assert result.success is False
    assert "not found" in result.error

@pytest.mark.asyncio
async def test_unknown_tool( memory_tool_provider):
    result = await memory_tool_provider.execute_tool("unknown_tool", {})

    assert result.success is False
    assert "Unknown tool" in result.error
