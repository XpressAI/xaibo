from typing import Protocol, List, Optional, AsyncIterator, runtime_checkable, Dict, Any
import numpy as np
from pydantic import BaseModel


class MemorySearchResult(BaseModel):
    """Model representing a memory search result"""
    memory_id: str
    content: str
    similarity_score: float
    attributes: Optional[Dict[str, Any]] = None


class VectorSearchResult(BaseModel):
    """Model representing a vector search result"""
    vector_id: str
    similarity_score: float
    attributes: Optional[Dict[str, Any]] = None


@runtime_checkable
class ChunkingProtocol(Protocol):
    """Protocol for chunking text for embedding into a vector space"""
    
    async def chunk(self, text: str) -> List[str]:
        """Chunk text into smaller chunks for embedding
        
        Args:
            text: Input text to be split into chunks
            
        Returns:
            List of text chunks suitable for embedding
        """
        ...

@runtime_checkable
class EmbeddingProtocol(Protocol):
    """Protocol for embedding multiple modalities into a vector space"""

    async def text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text into vector embedding
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array representing the vector embedding
        """
        ...

    async def image_to_embedding(self, image_data: bytes) -> np.ndarray:
        """Convert image data into vector embedding
        
        Args:
            image_data: Raw image bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
        """
        ...

    async def audio_to_embedding(self, audio_data: bytes) -> np.ndarray:
        """Convert audio data into vector embedding
        
        Args:
            audio_data: Raw audio bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
        """
        ...



@runtime_checkable
class VectorIndexProtocol(Protocol):
    """Protocol for indexing and searching a vector space given a query vector"""

    async def add_vectors(self, vectors: List[np.ndarray], attributes: Optional[List[dict]] = None) -> None:
        """Add vectors to the index with optional attributes
        
        Args:
            vectors: List of vector embeddings to add to index
            attributes: Optional list of attribute dictionaries, one per vector
        """
        ...

    async def search(self, query_vector: np.ndarray, k: int = 10) -> List[VectorSearchResult]:
        """Search for similar vectors given a query vector
        
        Args:
            query_vector: Vector embedding to search for
            k: Number of results to return (default: 10)
            
        Returns:
            List of VectorSearchResult objects containing search results with similarity scores and attributes
        """
        ...


@runtime_checkable
class MemoryProtocol(Protocol):
    """Protocol for modules providing memory functionality"""

    async def store_memory(self, text: str, attributes: Optional[dict] = None) -> str:
        """Store a new memory
        
        Args:
            text: Text content to store
            attributes: Optional metadata attributes
            
        Returns:
            ID of stored memory
        """
        ...

    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """Retrieve a specific memory by ID
        
        Args:
            memory_id: ID of memory to retrieve
            
        Returns:
            Memory data if found, None if not found
        """
        ...

    async def search_memory(self, query: str, k: int = 10) -> List[MemorySearchResult]:
        """Search memories semantically
        
        Args:
            query: Search query text
            k: Number of results to return (default: 10)
            
        Returns:
            List of MemorySearchResult objects with memory content and similarity scores
        """
        ...

    async def list_memories(self) -> List[dict]:
        """List all stored memories
        
        Returns:
            List of all memory entries
        """
        ...

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        ...

    async def update_memory(self, memory_id: str, text: str, attributes: Optional[dict] = None) -> bool:
        """Update an existing memory
        
        Args:
            memory_id: ID of memory to update
            text: New text content
            attributes: Optional new metadata attributes
            
        Returns:
            True if updated, False if not found
        """
        ...
