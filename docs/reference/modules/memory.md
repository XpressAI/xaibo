# Memory Modules Reference

Memory modules provide implementations of the memory protocols for storing, retrieving, and searching information. They support vector-based semantic search, text chunking, and multi-modal embeddings.

## VectorMemory

General-purpose memory system using vector embeddings for semantic search.

**Source**: [`src/xaibo/primitives/modules/memory/vector_memory.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/vector_memory.py)

**Module Path**: `xaibo.primitives.modules.memory.VectorMemory`

**Dependencies**: None

**Protocols**: Provides [`MemoryProtocol`](../protocols/memory.md)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `chunker` | `ChunkingProtocol` | Text chunking implementation |
| `embedder` | `EmbeddingProtocol` | Embedding generation implementation |
| `vector_index` | `VectorIndexProtocol` | Vector storage and search implementation |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `memory_file_path` | `str` | `None` | Path to pickle file for storing memories |

### Example Configuration

```yaml
modules:
  # Chunking component
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 512
      window_overlap: 50
  
  # Embedding component
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: "all-MiniLM-L6-v2"
  
  # Vector index component
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./memory_index"
  
  # Complete memory system
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "./memories.pkl"

exchange:
  - module: memory
    protocol: ChunkingProtocol
    provider: chunker
  - module: memory
    protocol: EmbeddingProtocol
    provider: embedder
  - module: memory
    protocol: VectorIndexProtocol
    provider: vector_index
```

### Features

- **Semantic Search**: Vector-based similarity search
- **Automatic Chunking**: Splits large texts into manageable chunks
- **Metadata Support**: Stores arbitrary metadata with memories
- **Persistence**: Saves memories to disk for persistence
- **Deduplication**: Handles similar content intelligently

## TokenChunker

Splits text based on token counts for optimal embedding.

**Source**: [`src/xaibo/primitives/modules/memory/token_chunker.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/token_chunker.py)

**Module Path**: `xaibo.primitives.modules.memory.TokenChunker`

**Dependencies**: `local` dependency group (for `tiktoken`)

**Protocols**: Provides [`ChunkingProtocol`](../protocols/memory.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `window_size` | `int` | `512` | Maximum number of tokens per chunk |
| `window_overlap` | `int` | `50` | Number of tokens to overlap between chunks |
| `encoding_name` | `str` | `"cl100k_base"` | Tiktoken encoding to use |

### Supported Encodings

| Encoding | Description | Used By |
|----------|-------------|---------|
| `cl100k_base` | GPT-4, GPT-3.5-turbo | OpenAI models |
| `p50k_base` | GPT-3 (davinci, curie, etc.) | Legacy OpenAI models |
| `r50k_base` | GPT-3 (ada, babbage) | Legacy OpenAI models |
| `gpt2` | GPT-2 | GPT-2 models |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 1024
      window_overlap: 100
      encoding_name: "cl100k_base"
```

### Features

- **Token-Aware**: Respects model token limits
- **Overlap Support**: Maintains context between chunks
- **Multiple Encodings**: Supports various tokenization schemes
- **Efficient**: Fast tokenization using tiktoken

## SentenceTransformerEmbedder

Uses Sentence Transformers for text embeddings.

**Source**: [`src/xaibo/primitives/modules/memory/sentence_transformer_embedder.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/sentence_transformer_embedder.py)

**Module Path**: `xaibo.primitives.modules.memory.SentenceTransformerEmbedder`

**Dependencies**: `local` dependency group (for `sentence-transformers`)

**Protocols**: Provides [`EmbeddingProtocol`](../protocols/memory.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | `"all-MiniLM-L6-v2"` | Sentence Transformer model name |
| `model_kwargs` | `dict` | `{}` | Additional model constructor arguments |

### Popular Models

| Model | Dimensions | Performance | Speed | Description |
|-------|------------|-------------|-------|-------------|
| `all-MiniLM-L6-v2` | 384 | Good | Fast | Balanced performance and speed |
| `all-mpnet-base-v2` | 768 | Best | Medium | Highest quality embeddings |
| `all-MiniLM-L12-v2` | 384 | Better | Medium | Better than L6, slower |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Good | Medium | Multilingual support |
| `multi-qa-MiniLM-L6-cos-v1` | 384 | Good | Fast | Optimized for Q&A |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: "all-mpnet-base-v2"
      model_kwargs:
        cache_folder: "./model_cache"
        device: "cuda"
```

### Features

- **High Quality**: State-of-the-art embedding quality
- **Multiple Models**: Wide selection of pre-trained models
- **GPU Support**: Automatic GPU acceleration when available
- **Caching**: Model caching for faster startup

## HuggingFaceEmbedder

Leverages Hugging Face models for embeddings with multi-modal support.

**Source**: [`src/xaibo/primitives/modules/memory/huggingface_embedder.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/huggingface_embedder.py)

**Module Path**: `xaibo.primitives.modules.memory.HuggingFaceEmbedder`

**Dependencies**: `local` dependency group (for `transformers`)

**Protocols**: Provides [`EmbeddingProtocol`](../protocols/memory.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | `"sentence-transformers/all-MiniLM-L6-v2"` | Hugging Face model name |
| `device` | `str` | `"auto"` | Device to run model on |
| `max_length` | `int` | `512` | Maximum sequence length |
| `pooling_strategy` | `str` | `"mean"` | Token pooling strategy |
| `audio_sampling_rate` | `int` | `16000` | Audio sampling rate |
| `audio_max_length` | `int` | `30` | Maximum audio length in seconds |
| `audio_return_tensors` | `str` | `"pt"` | Audio tensor format |

### Pooling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `mean` | Average of all token embeddings | General text embedding |
| `cls` | Use [CLS] token embedding | Classification tasks |
| `max` | Max pooling over token embeddings | Capturing important features |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.HuggingFaceEmbedder
    id: embedder
    config:
      model_name: "microsoft/DialoGPT-medium"
      device: "cuda"
      max_length: 1024
      pooling_strategy: "mean"
      audio_sampling_rate: 22050
```

### Features

- **Multi-Modal**: Supports text, image, and audio embeddings
- **Flexible Models**: Use any Hugging Face transformer model
- **Custom Pooling**: Multiple pooling strategies
- **Audio Support**: Built-in audio processing capabilities

## OpenAIEmbedder

Utilizes OpenAI's embedding models.

**Source**: [`src/xaibo/primitives/modules/memory/openai_embedder.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/openai_embedder.py)

**Module Path**: `xaibo.primitives.modules.memory.OpenAIEmbedder`

**Dependencies**: `openai` dependency group

**Protocols**: Provides [`EmbeddingProtocol`](../protocols/memory.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"text-embedding-ada-002"` | OpenAI embedding model |
| `api_key` | `str` | `None` | OpenAI API key (falls back to env var) |
| `base_url` | `str` | `"https://api.openai.com/v1"` | OpenAI API base URL |
| `timeout` | `float` | `60.0` | Request timeout in seconds |
| `dimensions` | `int` | `None` | Embedding dimensions (for supported models) |
| `encoding_format` | `str` | `"float"` | Encoding format |

### Available Models

| Model | Dimensions | Max Input | Cost per 1K tokens |
|-------|------------|-----------|-------------------|
| `text-embedding-3-large` | 3072 | 8191 | $0.00013 |
| `text-embedding-3-small` | 1536 | 8191 | $0.00002 |
| `text-embedding-ada-002` | 1536 | 8191 | $0.00010 |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: "text-embedding-3-large"
      dimensions: 1024  # Reduced dimensions for efficiency
      timeout: 30.0
```

### Features

- **High Quality**: State-of-the-art embedding quality
- **Scalable**: Cloud-based, no local compute required
- **Configurable Dimensions**: Adjust dimensions for performance/quality trade-off
- **Rate Limiting**: Built-in rate limiting and retry logic

## NumpyVectorIndex

Simple vector index using NumPy for storage and retrieval.

**Source**: [`src/xaibo/primitives/modules/memory/numpy_vector_index.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/numpy_vector_index.py)

**Module Path**: `xaibo.primitives.modules.memory.NumpyVectorIndex`

**Dependencies**: `numpy` (core dependency)

**Protocols**: Provides [`VectorIndexProtocol`](../protocols/memory.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `storage_dir` | `str` | `None` | Directory for storing vector and attribute files |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./vector_storage"
```

### Storage Format

The index stores data in the specified directory:

```
vector_storage/
├── vectors.npy          # Vector embeddings
├── attributes.json      # Metadata attributes
└── index_metadata.json # Index configuration
```

### Features

- **Simple Implementation**: Easy to understand and debug
- **Persistent Storage**: Saves vectors to disk
- **Cosine Similarity**: Uses cosine similarity for search
- **Memory Efficient**: Loads vectors on demand

## MemoryProvider

High-level memory provider that combines multiple memory systems.

**Source**: [`src/xaibo/primitives/modules/memory/memory_provider.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/memory_provider.py)

**Module Path**: `xaibo.primitives.modules.memory.MemoryProvider`

**Dependencies**: None

**Protocols**: Provides [`MemoryProtocol`](../protocols/memory.md), Uses [`MemoryProtocol`](../protocols/memory.md) (list)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `memories` | `List[MemoryProtocol]` | List of memory systems to aggregate |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_strategy` | `str` | `"merge"` | How to combine results from multiple memories |
| `max_results_per_memory` | `int` | `10` | Maximum results from each memory system |

### Search Strategies

| Strategy | Description |
|----------|-------------|
| `merge` | Merge and re-rank results from all memories |
| `round_robin` | Alternate results from each memory |
| `best_first` | Take best results from highest-scoring memory |

### Example Configuration

```yaml
modules:
  # Short-term memory (recent conversations)
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: short_term_memory
    config:
      memory_file_path: "./short_term.pkl"
  
  # Long-term memory (knowledge base)
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: long_term_memory
    config:
      memory_file_path: "./long_term.pkl"
  
  # Combined memory provider
  - module: xaibo.primitives.modules.memory.MemoryProvider
    id: memory
    config:
      search_strategy: "merge"
      max_results_per_memory: 5

exchange:
  - module: memory
    protocol: MemoryProtocol
    provider: [short_term_memory, long_term_memory]
```

### Features

- **Multi-Memory**: Combines multiple memory systems
- **Flexible Search**: Multiple search strategies
- **Result Merging**: Intelligent result combination
- **Load Balancing**: Distributes queries across memories

## Common Configuration Patterns

### Basic Memory Setup

```yaml
modules:
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 512
      window_overlap: 50
  
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: "all-MiniLM-L6-v2"
  
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./memory"
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory

exchange:
  - module: memory
    protocol: ChunkingProtocol
    provider: chunker
  - module: memory
    protocol: EmbeddingProtocol
    provider: embedder
  - module: memory
    protocol: VectorIndexProtocol
    provider: vector_index
```

### High-Performance Setup

```yaml
modules:
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 1024
      window_overlap: 100
  
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: "text-embedding-3-large"
      dimensions: 1536
  
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./high_perf_memory"
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
```

### Multi-Modal Memory

```yaml
modules:
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
  
  - module: xaibo.primitives.modules.memory.HuggingFaceEmbedder
    id: embedder
    config:
      model_name: "microsoft/DialoGPT-medium"
      device: "cuda"
      audio_sampling_rate: 22050
  
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./multimodal_memory"
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
```

### Hierarchical Memory

```yaml
modules:
  # Working memory (small, fast)
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: working_memory
    config:
      memory_file_path: "./working.pkl"
  
  # Episodic memory (medium, recent events)
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: episodic_memory
    config:
      memory_file_path: "./episodic.pkl"
  
  # Semantic memory (large, knowledge base)
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: semantic_memory
    config:
      memory_file_path: "./semantic.pkl"
  
  # Combined memory system
  - module: xaibo.primitives.modules.memory.MemoryProvider
    id: memory
    config:
      search_strategy: "merge"

exchange:
  - module: memory
    protocol: MemoryProtocol
    provider: [working_memory, episodic_memory, semantic_memory]
```

## Performance Considerations

### Embedding Performance

1. **Model Selection**: Choose appropriate model for quality/speed trade-off
2. **Batch Processing**: Process multiple texts together
3. **GPU Acceleration**: Use GPU for local embedding models
4. **Caching**: Cache embeddings for repeated content

### Vector Index Performance

1. **Index Size**: Monitor index size and performance
2. **Search Optimization**: Use approximate search for large indices
3. **Memory Usage**: Consider memory requirements for large vector sets
4. **Persistence**: Balance persistence frequency with performance

### Memory Management

1. **Chunk Size**: Optimize chunk size for embedding model
2. **Overlap Strategy**: Balance context preservation with storage
3. **Cleanup**: Implement memory cleanup for old entries
4. **Compression**: Consider vector compression for storage

## Monitoring and Debugging

### Memory Metrics

```python
# Monitor memory usage
memory_stats = await memory.get_stats()
print(f"Total memories: {memory_stats['total_memories']}")
print(f"Total chunks: {memory_stats['total_chunks']}")
print(f"Index size: {memory_stats['index_size']}")
```

### Search Quality

```python
# Test search quality
results = await memory.search_memory("test query", k=10)
for result in results:
    print(f"Score: {result.similarity_score:.3f}")
    print(f"Content: {result.content[:100]}...")
```

### Performance Profiling

```python
import time

# Profile embedding performance
start_time = time.time()
embedding = await embedder.text_to_embedding("test text")
embedding_time = time.time() - start_time
print(f"Embedding time: {embedding_time:.3f}s")

# Profile search performance
start_time = time.time()
results = await memory.search_memory("test query")
search_time = time.time() - start_time
print(f"Search time: {search_time:.3f}s")