# How to set up vector memory for agents

This guide shows you how to enable your Xaibo agents to store and retrieve information using vector embeddings, allowing them to remember and search through previous conversations and documents.

## Install memory dependencies

Install the required dependencies for local embeddings:

```bash
pip install xaibo[local]
```

This includes sentence-transformers, tiktoken, and other memory-related packages.

## Configure basic vector memory

Add vector memory to your agent configuration:

```yaml
# agents/memory_agent.yml
id: memory-agent
description: An agent with vector memory capabilities
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
      
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

Configure OpenAI embeddings for higher quality vectors:

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

## Configure Hugging Face embeddings

Use Hugging Face models for embeddings:

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

Configure chunking strategy for your content:

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

Configure persistent storage for your vector memory:

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