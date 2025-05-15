import os
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from xaibo.primitives.modules.memory.vector_memory import VectorMemory
from xaibo.core.protocols.memory import MemorySearchResult, VectorSearchResult


@pytest.fixture
def mock_chunker():
    chunker = AsyncMock()
    chunker.chunk.return_value = ["chunk1", "chunk2"]
    return chunker

@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.text_to_embedding = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
    return embedder

@pytest.fixture
def mock_vector_index():
    vector_index = MagicMock()
    vector_index.add_vectors = AsyncMock()
    vector_index.search = AsyncMock()
    return vector_index

@pytest.fixture
def memory_config(tmp_path):
    return {"memory_file_path": os.path.join(tmp_path, "memories.pkl")}

@pytest.fixture
def vector_memory(mock_chunker, mock_embedder, mock_vector_index, memory_config):
    return VectorMemory(
        chunker=mock_chunker,
        embedder=mock_embedder,
        vector_index=mock_vector_index,
        config=memory_config
    )

@pytest.mark.asyncio
async def test_init_missing_config(mock_chunker, mock_embedder, mock_vector_index):
    with pytest.raises(ValueError, match="memory_file_path is required in config"):
        VectorMemory(mock_chunker, mock_embedder, mock_vector_index, {})

@pytest.mark.asyncio
async def test_store_memory(vector_memory, mock_chunker, mock_embedder, mock_vector_index):
    memory_id = await vector_memory.store_memory("test memory", {"tag": "test"})
    
    # Check that the memory was stored
    assert memory_id in vector_memory.memories
    assert vector_memory.memories[memory_id]["content"] == "test memory"
    assert vector_memory.memories[memory_id]["attributes"] == {"tag": "test"}
    
    # Check that chunking was called
    mock_chunker.chunk.assert_called_once_with("test memory")
    
    # Check that embeddings were created
    assert mock_embedder.text_to_embedding.call_count == 2  # Two chunks
    
    # Check that vectors were added to index
    mock_vector_index.add_vectors.assert_called_once()
    args = mock_vector_index.add_vectors.call_args[0]
    assert len(args[0]) == 2  # Two vectors
    assert len(args[1]) == 2  # Two sets of attributes
    assert args[1][0]["memory_id"] == memory_id
    assert args[1][0]["chunk_index"] == 0
    assert args[1][0]["chunk_text"] == "chunk1"
    assert args[1][0]["tag"] == "test"

@pytest.mark.asyncio
async def test_get_memory(vector_memory):
    # Store a test memory
    memory_id = await vector_memory.store_memory("test memory")
    
    # Retrieve the memory
    memory = await vector_memory.get_memory(memory_id)
    
    assert memory["content"] == "test memory"
    assert memory["id"] == memory_id
    
    # Test retrieving non-existent memory
    assert await vector_memory.get_memory("nonexistent") is None

@pytest.mark.asyncio
async def test_search_memory(vector_memory, mock_vector_index):
    # Store test memories
    memory_id1 = await vector_memory.store_memory("test memory 1")
    memory_id2 = await vector_memory.store_memory("test memory 2")
    
    # Mock search results
    mock_vector_index.search.return_value = [
        VectorSearchResult(
            vector_id="1",
            similarity_score=0.9,
            attributes={"memory_id": memory_id1, "chunk_index": 0}
        ),
        VectorSearchResult(
            vector_id="2",
            similarity_score=0.8,
            attributes={"memory_id": memory_id2, "chunk_index": 0}
        )
    ]
    
    # Search for memories
    results = await vector_memory.search_memory("test query")
    
    # Check search results
    assert len(results) == 2
    assert results[0].memory_id == memory_id1
    assert results[0].similarity_score == 0.9
    assert results[0].content == "test memory 1"
    assert results[1].memory_id == memory_id2
    assert results[1].similarity_score == 0.8
    assert results[1].content == "test memory 2"
    
    # Check that search was called with correct parameters
    mock_vector_index.search.assert_called_once()

@pytest.mark.asyncio
async def test_list_memories(vector_memory):
    # Store test memories
    memory_id1 = await vector_memory.store_memory("test memory 1")
    memory_id2 = await vector_memory.store_memory("test memory 2")
    
    # List memories
    memories = await vector_memory.list_memories()
    
    # Check results
    assert len(memories) == 2
    assert memories[0]["id"] == memory_id1
    assert memories[0]["content"] == "test memory 1"
    assert memories[1]["id"] == memory_id2
    assert memories[1]["content"] == "test memory 2"

@pytest.mark.asyncio
async def test_delete_memory(vector_memory):
    # Store a test memory
    memory_id = await vector_memory.store_memory("test memory")
    
    # Delete the memory
    result = await vector_memory.delete_memory(memory_id)
    
    # Check result
    assert result is True
    assert memory_id not in vector_memory.memories
    
    # Try to delete non-existent memory
    result = await vector_memory.delete_memory("nonexistent")
    assert result is False

@pytest.mark.asyncio
async def test_update_memory(vector_memory, mock_chunker, mock_embedder, mock_vector_index):
    # Store a test memory
    memory_id = await vector_memory.store_memory("test memory", {"tag": "test"})
    
    # Reset mocks to check calls during update
    mock_chunker.chunk.reset_mock()
    mock_embedder.text_to_embedding.reset_mock()
    mock_vector_index.add_vectors.reset_mock()
    
    # Update the memory
    result = await vector_memory.update_memory(memory_id, "updated memory", {"new_tag": "updated"})
    
    # Check result
    assert result is True
    assert vector_memory.memories[memory_id]["content"] == "updated memory"
    assert vector_memory.memories[memory_id]["attributes"] == {"new_tag": "updated"}
    
    # Check that chunking was called
    mock_chunker.chunk.assert_called_once_with("updated memory")
    
    # Check that embeddings were created
    assert mock_embedder.text_to_embedding.call_count == 2  # Two chunks
    
    # Check that vectors were added to index
    mock_vector_index.add_vectors.assert_called_once()
    
    # Try to update non-existent memory
    result = await vector_memory.update_memory("nonexistent", "updated memory")
    assert result is False
