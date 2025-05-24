# How to set up vector memory for agents

This guide shows you how to enable your Xaibo agents to store and retrieve information using vector embeddings, allowing them to remember and search through previous conversations and documents.

## Install memory dependencies

1. Install the required dependencies for local embeddings:

```bash
pip install xaibo[local]
```

This includes sentence-transformers, tiktoken, and other memory-related packages.

## Configure basic vector memory

2. Add vector memory to your agent configuration:

```yaml
# agents/memory_agent.yml
id: memory-agent
description: An agent with vector memory capabilities
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
      
  # Text chunker for splitting documents
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 512
      window_overlap: 50
      encoding_name: "cl100k_base"
      
  # Embedder for converting text to vectors
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: "all-MiniLM-L6-v2"
      
  # Vector index for storage and retrieval
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./memory_storage"
      
  # Main vector memory module
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "./agent_memory.pkl"
      
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      system_prompt: |
        You are a helpful assistant with memory capabilities.
        You can remember information from previous conversations.

exchange:
  # Connect memory components
  - module: memory
    protocol: ChunkerProtocol
    provider: chunker
  - module: memory
    protocol: EmbedderProtocol
    provider: embedder
  - module: memory
    protocol: VectorIndexProtocol
    provider: vector_index
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
```

## Use OpenAI embeddings

3. Configure OpenAI embeddings for higher quality vectors:

```bash
pip install xaibo[openai]
```

```yaml
# Replace the embedder module with OpenAI
modules:
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: "text-embedding-3-small"
      api_key: ${OPENAI_API_KEY}
      dimensions: 1536
```

Set your API key:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Available OpenAI embedding models:
- `text-embedding-3-small` - Cost-effective, good performance
- `text-embedding-3-large` - Higher quality, more expensive
- `text-embedding-ada-002` - Legacy model, still supported

## Configure Hugging Face embeddings

4. Use Hugging Face models for embeddings:

```yaml
modules:
  - module: xaibo.primitives.modules.memory.HuggingFaceEmbedder
    id: embedder
    config:
      model_name: "sentence-transformers/all-mpnet-base-v2"
      device: "cuda"  # Use "cpu" if no GPU available
      max_length: 512
      pooling_strategy: "mean"
```

Popular Hugging Face embedding models:
- `sentence-transformers/all-mpnet-base-v2` - High quality, balanced
- `sentence-transformers/all-MiniLM-L6-v2` - Fast and lightweight
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` - Multilingual support

## Customize text chunking

5. Configure chunking strategy for your content:

```yaml
modules:
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 1024      # Larger chunks for documents
      window_overlap: 100    # More overlap for context
      encoding_name: "cl100k_base"  # GPT-4 tokenizer
```

Chunking strategies:
- **Small chunks (256-512 tokens)**: Better for precise retrieval
- **Medium chunks (512-1024 tokens)**: Balanced approach
- **Large chunks (1024-2048 tokens)**: Better context preservation

## Store memory persistently

6. Configure persistent storage for your vector memory:

```yaml
modules:
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "/path/to/persistent/storage"
      
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "/path/to/persistent/memory.pkl"
```

Create the storage directory:

```bash
mkdir -p /path/to/persistent/storage
```

## Add documents to memory

7. Create a tool to add documents to agent memory:

```python
# tools/memory_tools.py
import os
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def add_document_to_memory(file_path: str, title: str = None) -> str:
    """Add a document to the agent's memory
    
    Args:
        file_path: Path to the document file
        title: Optional title for the document
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # The memory system will automatically chunk and embed this
        document_title = title or os.path.basename(file_path)
        
        # Store with metadata
        memory_entry = {
            "content": content,
            "title": document_title,
            "source": file_path,
            "type": "document"
        }
        
        # This would be handled by the memory system
        return f"Successfully added document '{document_title}' to memory"
        
    except Exception as e:
        return f"Error adding document: {str(e)}"

@tool
def search_memory(query: str, limit: int = 5) -> str:
    """Search the agent's memory for relevant information
    
    Args:
        query: Search query
        limit: Maximum number of results to return
    """
    # This would interface with the memory system
    # For now, return a placeholder
    return f"Searching memory for: '{query}' (limit: {limit})"
```

Add the tools to your agent:

```yaml
modules:
  - id: memory-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.memory_tools]
```

## Test memory functionality

8. Test your memory-enabled agent:

```bash
# Start the development server
uv run xaibo dev

# Add a document to memory
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "memory-agent",
    "messages": [
      {"role": "user", "content": "Add the file README.md to your memory with title \"Project Documentation\""}
    ]
  }'

# Search memory
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "memory-agent", 
    "messages": [
      {"role": "user", "content": "What do you remember about the project documentation?"}
    ]
  }'
```

## Configure memory for conversations

9. Set up memory to store conversation history:

```yaml
modules:
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "./conversation_memory.pkl"
      auto_store_conversations: true
      conversation_chunk_size: 256
      max_conversation_history: 1000
```

This automatically stores and indexes conversation turns for later retrieval.

## Optimize memory performance

10. Configure memory settings for better performance:

```yaml
modules:
  # Use faster embedder for real-time applications
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: "all-MiniLM-L6-v2"  # Faster model
      model_kwargs:
        device: "cuda"  # Use GPU if available
        
  # Optimize chunking for your content
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 384      # Smaller for faster processing
      window_overlap: 32    # Less overlap for speed
      
  # Configure vector index for performance
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./fast_storage"
      cache_size: 10000     # Cache more vectors in memory
```

## Handle large document collections

11. Configure memory for large-scale document storage:

```yaml
modules:
  # Use high-quality embedder for large collections
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: "text-embedding-3-large"
      dimensions: 3072
      
  # Larger chunks for document collections
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 1024
      window_overlap: 128
      
  # Persistent storage for large collections
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "/data/large_collection"
      
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "/data/large_collection/memory.pkl"
      similarity_threshold: 0.7  # Higher threshold for relevance
      max_results: 10           # Return more results
```

## Monitor memory usage

12. Create monitoring tools for memory system:

```python
# tools/memory_monitoring.py
import os
import pickle
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def get_memory_stats() -> dict:
    """Get statistics about the agent's memory system"""
    try:
        memory_file = "./agent_memory.pkl"
        storage_dir = "./memory_storage"
        
        stats = {
            "memory_file_exists": os.path.exists(memory_file),
            "storage_dir_exists": os.path.exists(storage_dir),
        }
        
        if stats["memory_file_exists"]:
            stats["memory_file_size"] = os.path.getsize(memory_file)
            
        if stats["storage_dir_exists"]:
            files = os.listdir(storage_dir)
            stats["storage_files"] = len(files)
            stats["total_storage_size"] = sum(
                os.path.getsize(os.path.join(storage_dir, f)) 
                for f in files
            )
            
        return stats
        
    except Exception as e:
        return {"error": str(e)}

@tool
def clear_memory() -> str:
    """Clear all stored memory (use with caution!)"""
    try:
        memory_file = "./agent_memory.pkl"
        storage_dir = "./memory_storage"
        
        if os.path.exists(memory_file):
            os.remove(memory_file)
            
        if os.path.exists(storage_dir):
            import shutil
            shutil.rmtree(storage_dir)
            os.makedirs(storage_dir)
            
        return "Memory cleared successfully"
        
    except Exception as e:
        return f"Error clearing memory: {str(e)}"
```

## Best practices

### Embedding model selection
- Use OpenAI embeddings for highest quality
- Use local models for privacy and cost control
- Choose model size based on performance requirements

### Chunking strategy
- Smaller chunks for precise retrieval
- Larger chunks for better context
- Adjust overlap based on content type

### Storage management
- Use persistent storage for production
- Monitor storage size and performance
- Implement cleanup strategies for old data

### Performance optimization
- Use GPU acceleration when available
- Cache frequently accessed vectors
- Batch process large document collections

## Troubleshooting

### Memory not persisting
- Check file permissions for storage directories
- Verify storage paths are absolute and accessible
- Ensure sufficient disk space

### Poor retrieval quality
- Experiment with different embedding models
- Adjust similarity thresholds
- Review chunking strategy for your content

### Performance issues
- Monitor memory usage and optimize chunk sizes
- Use faster embedding models for real-time applications
- Consider GPU acceleration for large collections

### Import errors
- Verify all memory dependencies are installed
- Check that storage directories exist
- Ensure proper module configuration in agent YAML