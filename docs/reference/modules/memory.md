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
| `memory_file_path` | `str` | Required | Path to pickle file for storing memories |

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
| `cl100k_base` | GPT-4, gpt-4.1-nano | OpenAI models |
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
| `device` | `str` | `"cuda" if available, else "cpu"` | Device to run model on |
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
| `api_key` | `str` | `None` | OpenAI API key (falls back to OPENAI_API_KEY env var) |
| `base_url` | `str` | `"https://api.openai.com/v1"` | OpenAI API base URL |
| `timeout` | `float` | `60.0` | Request timeout in seconds |


### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: "text-embedding-3-large"
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
| `storage_dir` | `str` | Required | Directory for storing vector and attribute files |

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
├── vectors/             # Directory containing individual vector files
│   ├── vector_0.npy     # Individual vector embeddings
│   ├── vector_1.npy
│   └── ...
└── attributes.pkl       # Pickled metadata attributes
```

### Features

- **Simple Implementation**: Easy to understand and debug
- **Persistent Storage**: Saves vectors to disk
- **Cosine Similarity**: Uses cosine similarity for search
- **Memory Efficient**: Loads vectors on demand

## MemoryToolProvider

Tool provider that exposes memory functionality through tools.

**Source**: [`src/xaibo/primitives/modules/memory/memory_provider.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/memory/memory_provider.py)

**Module Path**: `xaibo.primitives.modules.memory.MemoryToolProvider`

**Dependencies**: None

**Protocols**: Provides [`ToolProviderProtocol`](../protocols/tools.md), Uses [`MemoryProtocol`](../protocols/memory.md)

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_provider` | `MemoryProtocol` | Memory system to expose through tools |

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `dict` | `None` | Optional configuration dictionary |

### Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `store_memory` | Store a new memory in the system | `text` (string), `attributes` (object, optional) |
| `get_memory` | Retrieve a specific memory by ID | `memory_id` (string) |
| `search_memory` | Search memories semantically using a text query | `query` (string), `k` (integer, default: 10) |
| `list_memories` | List all stored memories | None |
| `delete_memory` | Delete a memory by ID | `memory_id` (string) |
| `update_memory` | Update an existing memory | `memory_id` (string), `text` (string), `attributes` (object, optional) |

### Example Configuration

```yaml
modules:
  # Memory system
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory_system
    config:
      memory_file_path: "./memories.pkl"
  
  # Memory tool provider
  - module: xaibo.primitives.modules.memory.MemoryToolProvider
    id: memory_tools

exchange:
  - module: memory_tools
    protocol: MemoryProtocol
    provider: memory_system
```

### Features

- **Tool Integration**: Exposes memory operations as tools
- **Complete API**: All memory operations available as tools
- **Error Handling**: Proper error responses for tool failures
- **Metadata Support**: Supports arbitrary metadata attributes

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

### Memory with Tool Integration

```yaml
modules:
  # Core memory components
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
      storage_dir: "./memory_index"
  
  # Memory system
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory_system
    config:
      memory_file_path: "./memories.pkl"
  
  # Memory tool provider
  - module: xaibo.primitives.modules.memory.MemoryToolProvider
    id: memory_tools

exchange:
  - module: memory_system
    protocol: ChunkingProtocol
    provider: chunker
  - module: memory_system
    protocol: EmbeddingProtocol
    provider: embedder
  - module: memory_system
    protocol: VectorIndexProtocol
    provider: vector_index
  - module: memory_tools
    protocol: MemoryProtocol
    provider: memory_system
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