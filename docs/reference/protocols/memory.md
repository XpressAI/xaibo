# Memory Protocol Specification

The Memory Protocol defines interfaces for memory storage, retrieval, and vector-based semantic search in Xaibo agents. It provides a multi-layered architecture supporting chunking, embedding, indexing, and high-level memory operations.

**Source**: [`src/xaibo/core/protocols/memory.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/memory.py)

## Protocol Hierarchy

The memory system consists of four protocol layers:

1. **ChunkingProtocol**: Text segmentation for embedding
2. **EmbeddingProtocol**: Multi-modal embedding generation
3. **VectorIndexProtocol**: Vector storage and similarity search
4. **MemoryProtocol**: High-level memory operations

## ChunkingProtocol

Protocol for splitting text into chunks suitable for embedding.

```python
@runtime_checkable
class ChunkingProtocol(Protocol):
    """Protocol for chunking text for embedding into a vector space"""
    
    async def chunk(self, text: str) -> List[str]:
        """Chunk text into smaller chunks for embedding"""
        ...
```

### Methods

---

#### `chunk(text: str) -> List[str]`

Split input text into smaller chunks optimized for embedding.

**Parameters:**

- `text` (`str`, required): Input text to be split into chunks

**Returns:**

- `List[str]`: List of text chunks suitable for embedding

**Example:**
```python
chunker = TokenChunker(window_size=512, window_overlap=50)
chunks = await chunker.chunk("Long document text here...")
print(f"Split into {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {chunk[:100]}...")
```

---

## EmbeddingProtocol

Protocol for converting multiple modalities into vector embeddings.

```python
@runtime_checkable
class EmbeddingProtocol(Protocol):
    """Protocol for embedding multiple modalities into a vector space"""

    async def text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text into vector embedding"""
        ...

    async def image_to_embedding(self, image_data: bytes) -> np.ndarray:
        """Convert image data into vector embedding"""
        ...

    async def audio_to_embedding(self, audio_data: bytes) -> np.ndarray:
        """Convert audio data into vector embedding"""
        ...
```

### Methods

---

#### `text_to_embedding(text: str) -> np.ndarray`

Convert text into a vector embedding.

**Parameters:**

- `text` (`str`, required): Input text to embed

**Returns:**

- `np.ndarray`: Vector embedding as NumPy array

**Example:**
```python
embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
embedding = await embedder.text_to_embedding("Hello world")
print(f"Embedding shape: {embedding.shape}")  # (384,)
```

---

#### `image_to_embedding(image_data: bytes) -> np.ndarray`

Convert image data into a vector embedding.

**Parameters:**

- `image_data` (`bytes`, required): Raw image bytes to embed

**Returns:**

- `np.ndarray`: Vector embedding as NumPy array

**Example:**
```python
with open("image.jpg", "rb") as f:
    image_data = f.read()

embedding = await embedder.image_to_embedding(image_data)
print(f"Image embedding shape: {embedding.shape}")
```

---

#### `audio_to_embedding(audio_data: bytes) -> np.ndarray`

Convert audio data into a vector embedding.

**Parameters:**

- `audio_data` (`bytes`, required): Raw audio bytes to embed

**Returns:**

- `np.ndarray`: Vector embedding as NumPy array

**Example:**
```python
with open("audio.wav", "rb") as f:
    audio_data = f.read()

embedding = await embedder.audio_to_embedding(audio_data)
print(f"Audio embedding shape: {embedding.shape}")
```

---

## VectorIndexProtocol

Protocol for indexing and searching vector embeddings.

```python
@runtime_checkable
class VectorIndexProtocol(Protocol):
    """Protocol for indexing and searching a vector space given a query vector"""

    async def add_vectors(self, vectors: List[np.ndarray], attributes: Optional[List[dict]] = None) -> None:
        """Add vectors to the index with optional attributes"""
        ...

    async def search(self, query_vector: np.ndarray, k: int = 10) -> List[VectorSearchResult]:
        """Search for similar vectors given a query vector"""
        ...
```

### Methods

---

#### `add_vectors(vectors: List[np.ndarray], attributes: Optional[List[dict]] = None) -> None`

Add vectors to the index with optional metadata.

**Parameters:**

- `vectors` (`List[np.ndarray]`, required): List of vector embeddings to add to index
- `attributes` (`Optional[List[dict]]`, optional): Optional list of attribute dictionaries, one per vector

**Example:**
```python
vectors = [embedding1, embedding2, embedding3]
attributes = [
    {"source": "document1.txt", "page": 1},
    {"source": "document1.txt", "page": 2},
    {"source": "document2.txt", "page": 1}
]

await vector_index.add_vectors(vectors, attributes)
```

---

#### `search(query_vector: np.ndarray, k: int = 10) -> List[VectorSearchResult]`

Search for similar vectors using a query vector.

**Parameters:**

- `query_vector` (`np.ndarray`, required): Vector embedding to search for
- `k` (`int`, optional): Number of results to return (default: 10)

**Returns:**

- `List[VectorSearchResult]`: List of search results with similarity scores and attributes

**Example:**
```python
query_embedding = await embedder.text_to_embedding("search query")
results = await vector_index.search(query_embedding, k=5)

for result in results:
    print(f"ID: {result.vector_id}, Score: {result.similarity_score}")
    print(f"Attributes: {result.attributes}")
```

---

## MemoryProtocol

High-level protocol for memory storage and retrieval operations.

```python
@runtime_checkable
class MemoryProtocol(Protocol):
    """Protocol for modules providing memory functionality"""

    async def store_memory(self, text: str, attributes: Optional[dict] = None) -> str:
        """Store a new memory"""
        ...

    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """Retrieve a specific memory by ID"""
        ...

    async def search_memory(self, query: str, k: int = 10) -> List[MemorySearchResult]:
        """Search memories semantically"""
        ...

    async def list_memories(self) -> List[dict]:
        """List all stored memories"""
        ...

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        ...

    async def update_memory(self, memory_id: str, text: str, attributes: Optional[dict] = None) -> bool:
        """Update an existing memory"""
        ...
```

### Methods

---

#### `store_memory(text: str, attributes: Optional[dict] = None) -> str`

Store a new memory with optional metadata.

**Parameters:**

- `text` (`str`, required): Text content to store
- `attributes` (`Optional[dict]`, optional): Optional metadata attributes

**Returns:**

- `str`: ID of stored memory

**Example:**
```python
memory_id = await memory.store_memory(
    "Important meeting notes from today",
    attributes={
        "date": "2024-01-15",
        "type": "meeting",
        "participants": ["Alice", "Bob"]
    }
)
print(f"Stored memory with ID: {memory_id}")
```

---

#### `get_memory(memory_id: str) -> Optional[dict]`

Retrieve a specific memory by its ID.

**Parameters:**

- `memory_id` (`str`, required): ID of memory to retrieve

**Returns:**

- `Optional[dict]`: Memory data if found, None if not found

**Example:**
```python
memory_data = await memory.get_memory("mem_123")
if memory_data:
    print(f"Content: {memory_data['content']}")
    print(f"Attributes: {memory_data['attributes']}")
else:
    print("Memory not found")
```

---

#### `search_memory(query: str, k: int = 10) -> List[MemorySearchResult]`

Search memories using semantic similarity.

**Parameters:**

- `query` (`str`, required): Search query text
- `k` (`int`, optional): Number of results to return (default: 10)

**Returns:**

- `List[MemorySearchResult]`: List of search results with memory content and similarity scores

**Example:**
```python
results = await memory.search_memory("meeting notes", k=5)
for result in results:
    print(f"Memory ID: {result.memory_id}")
    print(f"Content: {result.content}")
    print(f"Similarity: {result.similarity_score}")
    print(f"Attributes: {result.attributes}")
```

---

#### `list_memories() -> List[dict]`

List all stored memories.

**Returns:**

- `List[dict]`: List of all memory entries

**Example:**
```python
all_memories = await memory.list_memories()
print(f"Total memories: {len(all_memories)}")
for mem in all_memories:
    print(f"ID: {mem['id']}, Content: {mem['content'][:50]}...")
```

---

#### `delete_memory(memory_id: str) -> bool`

Delete a memory by its ID.

**Parameters:**

- `memory_id` (`str`, required): ID of memory to delete

**Returns:**

- `bool`: True if deleted, False if not found

**Example:**
```python
deleted = await memory.delete_memory("mem_123")
if deleted:
    print("Memory deleted successfully")
else:
    print("Memory not found")
```

---

#### `update_memory(memory_id: str, text: str, attributes: Optional[dict] = None) -> bool`

Update an existing memory with new content and attributes.

**Parameters:**

- `memory_id` (`str`, required): ID of memory to update
- `text` (`str`, required): New text content
- `attributes` (`Optional[dict]`, optional): Optional new metadata attributes

**Returns:**

- `bool`: True if updated, False if not found

**Example:**
```python
updated = await memory.update_memory(
    "mem_123",
    "Updated meeting notes with action items",
    attributes={"status": "updated", "action_items": 3}
)
if updated:
    print("Memory updated successfully")
else:
    print("Memory not found")
```

---

## Data Models

### MemorySearchResult

Result from memory search operations.

**Source**: [`src/xaibo/core/protocols/memory.py:6`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/memory.py#L6)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `memory_id` | `str` | Yes | Unique identifier for the memory |
| `content` | `str` | Yes | Text content of the memory |
| `similarity_score` | `float` | Yes | Similarity score (0.0 to 1.0) |
| `attributes` | `Dict[str, Any]` | No | Optional metadata attributes |

### VectorSearchResult

Result from vector index search operations.

**Source**: [`src/xaibo/core/protocols/memory.py:14`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/memory.py#L14)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vector_id` | `str` | Yes | Unique identifier for the vector |
| `similarity_score` | `float` | Yes | Similarity score (0.0 to 1.0) |
| `attributes` | `Dict[str, Any]` | No | Optional metadata attributes |

## Implementation Example

```python
from xaibo.core.protocols.memory import MemoryProtocol, ChunkingProtocol, EmbeddingProtocol, VectorIndexProtocol
from xaibo.core.protocols.memory import MemorySearchResult, VectorSearchResult
import uuid
import numpy as np
from typing import Dict, List, Optional, Any

class SimpleMemorySystem:
    """Example implementation combining all memory protocols"""
    
    def __init__(
        self, 
        chunker: ChunkingProtocol,
        embedder: EmbeddingProtocol,
        vector_index: VectorIndexProtocol
    ):
        self.chunker = chunker
        self.embedder = embedder
        self.vector_index = vector_index
        self.memories: Dict[str, dict] = {}
        self.chunk_to_memory: Dict[str, str] = {}
    
    async def store_memory(self, text: str, attributes: Optional[dict] = None) -> str:
        """Store a new memory with chunking and embedding"""
        memory_id = str(uuid.uuid4())
        
        # Store memory metadata
        self.memories[memory_id] = {
            "id": memory_id,
            "content": text,
            "attributes": attributes or {},
            "chunks": []
        }
        
        # Chunk the text
        chunks = await self.chunker.chunk(text)
        
        # Embed each chunk
        vectors = []
        chunk_attributes = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{memory_id}_chunk_{i}"
            self.chunk_to_memory[chunk_id] = memory_id
            self.memories[memory_id]["chunks"].append(chunk_id)
            
            # Create embedding
            embedding = await self.embedder.text_to_embedding(chunk)
            vectors.append(embedding)
            
            # Prepare attributes
            chunk_attrs = {
                "memory_id": memory_id,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "chunk_text": chunk,
                **(attributes or {})
            }
            chunk_attributes.append(chunk_attrs)
        
        # Add to vector index
        await self.vector_index.add_vectors(vectors, chunk_attributes)
        
        return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """Retrieve a specific memory by ID"""
        return self.memories.get(memory_id)
    
    async def search_memory(self, query: str, k: int = 10) -> List[MemorySearchResult]:
        """Search memories using semantic similarity"""
        # Embed the query
        query_embedding = await self.embedder.text_to_embedding(query)
        
        # Search vector index
        vector_results = await self.vector_index.search(query_embedding, k * 2)  # Get more to deduplicate
        
        # Group results by memory and take best score per memory
        memory_scores: Dict[str, float] = {}
        memory_chunks: Dict[str, List[str]] = {}
        
        for result in vector_results:
            memory_id = result.attributes["memory_id"]
            chunk_text = result.attributes["chunk_text"]
            
            if memory_id not in memory_scores or result.similarity_score > memory_scores[memory_id]:
                memory_scores[memory_id] = result.similarity_score
            
            if memory_id not in memory_chunks:
                memory_chunks[memory_id] = []
            memory_chunks[memory_id].append(chunk_text)
        
        # Create memory search results
        results = []
        for memory_id in sorted(memory_scores.keys(), key=lambda x: memory_scores[x], reverse=True)[:k]:
            memory_data = self.memories[memory_id]
            results.append(MemorySearchResult(
                memory_id=memory_id,
                content=memory_data["content"],
                similarity_score=memory_scores[memory_id],
                attributes=memory_data["attributes"]
            ))
        
        return results
    
    async def list_memories(self) -> List[dict]:
        """List all stored memories"""
        return list(self.memories.values())
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory and its chunks"""
        if memory_id not in self.memories:
            return False
        
        # Clean up chunk mappings
        memory_data = self.memories[memory_id]
        for chunk_id in memory_data.get("chunks", []):
            self.chunk_to_memory.pop(chunk_id, None)
        
        # Remove memory
        del self.memories[memory_id]
        
        # Note: In a real implementation, you'd also remove vectors from the index
        return True
    
    async def update_memory(self, memory_id: str, text: str, attributes: Optional[dict] = None) -> bool:
        """Update an existing memory"""
        if memory_id not in self.memories:
            return False
        
        # Delete old memory
        await self.delete_memory(memory_id)
        
        # Store updated memory with same ID
        self.memories[memory_id] = {
            "id": memory_id,
            "content": text,
            "attributes": attributes or {},
            "chunks": []
        }
        
        # Re-chunk and re-embed
        chunks = await self.chunker.chunk(text)
        vectors = []
        chunk_attributes = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{memory_id}_chunk_{i}"
            self.chunk_to_memory[chunk_id] = memory_id
            self.memories[memory_id]["chunks"].append(chunk_id)
            
            embedding = await self.embedder.text_to_embedding(chunk)
            vectors.append(embedding)
            
            chunk_attrs = {
                "memory_id": memory_id,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "chunk_text": chunk,
                **(attributes or {})
            }
            chunk_attributes.append(chunk_attrs)
        
        await self.vector_index.add_vectors(vectors, chunk_attributes)
        
        return True

# Verify protocol compliance
assert isinstance(SimpleMemorySystem(None, None, None), MemoryProtocol)
```

## Testing

Mock implementations for testing:

```python
class MockChunker:
    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
    
    async def chunk(self, text: str) -> List[str]:
        # Simple character-based chunking
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

class MockEmbedder:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    async def text_to_embedding(self, text: str) -> np.ndarray:
        # Generate deterministic embedding based on text hash
        import hashlib
        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_value % (2**32))
        return np.random.normal(0, 1, self.dimension).astype(np.float32)
    
    async def image_to_embedding(self, image_data: bytes) -> np.ndarray:
        return await self.text_to_embedding(str(len(image_data)))
    
    async def audio_to_embedding(self, audio_data: bytes) -> np.ndarray:
        return await self.text_to_embedding(str(len(audio_data)))

class MockVectorIndex:
    def __init__(self):
        self.vectors: List[np.ndarray] = []
        self.attributes: List[dict] = []
    
    async def add_vectors(self, vectors: List[np.ndarray], attributes: Optional[List[dict]] = None) -> None:
        self.vectors.extend(vectors)
        if attributes:
            self.attributes.extend(attributes)
        else:
            self.attributes.extend([{}] * len(vectors))
    
    async def search(self, query_vector: np.ndarray, k: int = 10) -> List[VectorSearchResult]:
        if not self.vectors:
            return []
        
        # Calculate cosine similarity
        similarities = []
        for i, vector in enumerate(self.vectors):
            similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
            similarities.append((i, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, (vector_idx, score) in enumerate(similarities[:k]):
            results.append(VectorSearchResult(
                vector_id=str(vector_idx),
                similarity_score=float(score),
                attributes=self.attributes[vector_idx]
            ))
        
        return results

# Verify protocol compliance
assert isinstance(MockChunker(), ChunkingProtocol)
assert isinstance(MockEmbedder(), EmbeddingProtocol)
assert isinstance(MockVectorIndex(), VectorIndexProtocol)
```

## Best Practices

### Memory Design

1. **Chunking Strategy**: Choose appropriate chunk sizes for your embedding model
2. **Metadata**: Store rich metadata for filtering and context
3. **Deduplication**: Handle duplicate or similar content appropriately
4. **Versioning**: Consider versioning for updated memories
5. **Cleanup**: Implement proper cleanup for deleted memories

### Performance Optimization

1. **Batch Operations**: Process multiple items together when possible
2. **Caching**: Cache frequently accessed embeddings
3. **Indexing**: Use efficient vector indexing algorithms
4. **Lazy Loading**: Load large memories on demand
5. **Compression**: Consider embedding compression for storage

### Error Handling

1. **Graceful Degradation**: Handle embedding failures gracefully
2. **Validation**: Validate input text and parameters
3. **Resource Limits**: Implement memory and storage limits
4. **Retry Logic**: Add retry logic for transient failures
5. **Monitoring**: Monitor memory usage and performance