import uuid
import os
import pickle
from typing import List, Dict, Optional, Any
import numpy as np

from xaibo.core.protocols.memory import (
    MemoryProtocol,
    ChunkingProtocol,
    EmbeddingProtocol,
    VectorIndexProtocol,
    MemorySearchResult
)


class VectorMemory(MemoryProtocol):
    """
    Implementation of MemoryProtocol that uses vector embeddings for semantic search.
    Uses a chunker to split text, an embedder to create vector embeddings, 
    and a vector index for storage and retrieval.
    Memories are persisted to disk using pickle.
    """
    
    def __init__(
        self,
        chunker: ChunkingProtocol,
        embedder: EmbeddingProtocol,
        vector_index: VectorIndexProtocol,
        config: Dict[str, Any]
    ):
        """
        Initialize the VectorMemory with required components.
        
        Args:
            chunker: Component that implements ChunkingProtocol for text chunking
            embedder: Component that implements EmbeddingProtocol for creating embeddings
            vector_index: Component that implements VectorIndexProtocol for vector storage and search
            config: Configuration dictionary containing:
                - memory_file_path: Path to the pickle file for storing memories
        """
        if "memory_file_path" not in config:
            raise ValueError("memory_file_path is required in config")
            
        self.chunker = chunker
        self.embedder = embedder
        self.vector_index = vector_index
        self.memory_file_path = config["memory_file_path"]
        
        # Load existing memories if file exists, otherwise start with empty dict
        if os.path.exists(self.memory_file_path):
            with open(self.memory_file_path, 'rb') as f:
                self.memories = pickle.load(f)
        else:
            self.memories = {}  # In-memory storage of full memories
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
            self._save_memories()
    
    def _save_memories(self):
        """Save memories to disk using pickle"""
        with open(self.memory_file_path, 'wb') as f:
            pickle.dump(self.memories, f)
    
    async def store_memory(self, text: str, attributes: Optional[dict] = None) -> str:
        """
        Store a new memory by chunking text, creating embeddings, and storing in vector index.
        
        Args:
            text: Text content to store
            attributes: Optional metadata attributes
            
        Returns:
            ID of stored memory
        """
        memory_id = str(uuid.uuid4())
        
        # Store the full memory text and attributes
        memory_data = {
            "id": memory_id,
            "content": text,
            "attributes": attributes or {}
        }
        self.memories[memory_id] = memory_data
        self._save_memories()
        
        # Chunk the text
        chunks = await self.chunker.chunk(text)
        
        # Create embeddings for each chunk
        vectors = []
        chunk_attributes = []
        
        for i, chunk in enumerate(chunks):
            vector = await self.embedder.text_to_embedding(chunk)
            vectors.append(vector)
            
            # Create attributes for this chunk that link back to the original memory
            chunk_attr = {
                "memory_id": memory_id,
                "chunk_index": i,
                "chunk_text": chunk
            }
            if attributes:
                chunk_attr.update(attributes)
            
            chunk_attributes.append(chunk_attr)
        
        # Add vectors to the index
        await self.vector_index.add_vectors(vectors, chunk_attributes)
        
        return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: ID of memory to retrieve
            
        Returns:
            Memory data if found, None if not found
        """
        return self.memories.get(memory_id)
    
    async def search_memory(self, query: str, k: int = 10) -> List[MemorySearchResult]:
        """
        Search memories semantically using vector similarity.
        
        Args:
            query: Search query text
            k: Number of results to return (default: 10)
            
        Returns:
            List of MemorySearchResult objects with memory content and similarity scores
        """
        # Create embedding for the query
        query_vector = await self.embedder.text_to_embedding(query)
        
        # Search the vector index
        vector_results = await self.vector_index.search(query_vector, k=k)
        
        # Convert vector results to memory results
        memory_results = []
        seen_memory_ids = set()
        
        for result in vector_results:
            memory_id = result.attributes.get("memory_id")
            
            # Skip if we've already included this memory or if memory_id is missing
            if not memory_id or memory_id in seen_memory_ids:
                continue
            
            memory = self.memories.get(memory_id)
            if memory:
                seen_memory_ids.add(memory_id)
                memory_results.append(
                    MemorySearchResult(
                        memory_id=memory_id,
                        content=memory["content"],
                        similarity_score=result.similarity_score,
                        attributes=memory.get("attributes")
                    )
                )
        
        return memory_results
    
    async def list_memories(self) -> List[dict]:
        """
        List all stored memories.
        
        Returns:
            List of all memory entries
        """
        return list(self.memories.values())
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        Note: This implementation only removes from in-memory storage.
        Vector index entries remain (would need vector_index.delete_by_attribute support).
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save_memories()
            return True
        return False
    
    async def update_memory(self, memory_id: str, text: str, attributes: Optional[dict] = None) -> bool:
        """
        Update an existing memory.
        Implements a delete-then-insert approach for simplicity.
        
        Args:
            memory_id: ID of memory to update
            text: New text content
            attributes: Optional new metadata attributes
            
        Returns:
            True if updated, False if not found
        """
        if memory_id not in self.memories:
            return False
        
        # Delete the old memory
        await self.delete_memory(memory_id)
        
        # Store the new memory with the same ID
        old_memory = self.memories.get(memory_id, {})
        merged_attributes = old_memory.get("attributes", {}).copy()
        if attributes:
            merged_attributes.update(attributes)
        
        # Create a new memory with the same ID
        memory_data = {
            "id": memory_id,
            "content": text,
            "attributes": merged_attributes
        }
        self.memories[memory_id] = memory_data
        self._save_memories()
        
        # Chunk the text
        chunks = await self.chunker.chunk(text)
        
        # Create embeddings for each chunk
        vectors = []
        chunk_attributes = []
        
        for i, chunk in enumerate(chunks):
            vector = await self.embedder.text_to_embedding(chunk)
            vectors.append(vector)
            
            # Create attributes for this chunk that link back to the original memory
            chunk_attr = {
                "memory_id": memory_id,
                "chunk_index": i,
                "chunk_text": chunk
            }
            if merged_attributes:
                chunk_attr.update(merged_attributes)
            
            chunk_attributes.append(chunk_attr)
        
        # Add vectors to the index
        await self.vector_index.add_vectors(vectors, chunk_attributes)
        
        return True
