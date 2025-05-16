import pytest
import asyncio
from xaibo.primitives.modules.memory.token_chunker import TokenChunker


def test_init_with_default_config():
    """Test initialization with default configuration."""
    chunker = TokenChunker({})
    assert chunker.window_size == 512
    assert chunker.window_overlap == 50
    assert chunker.encoding_name == "cl100k_base"
    
def test_init_with_custom_config():
    """Test initialization with custom configuration."""
    config = {
        "window_size": 256,
        "window_overlap": 25,
        "encoding_name": "p50k_base"
    }
    chunker = TokenChunker(config)
    assert chunker.window_size == 256
    assert chunker.window_overlap == 25
    assert chunker.encoding_name == "p50k_base"

@pytest.mark.asyncio
async def test_chunk_empty_text():
    """Test chunking empty text returns empty list."""
    chunker = TokenChunker({})
    result = await chunker.chunk("")
    assert result == []
    
    result = await chunker.chunk("   ")
    assert result == []

@pytest.mark.asyncio
async def test_chunk_small_text():
    """Test chunking text smaller than window size."""
    chunker = TokenChunker({"window_size": 100})
    small_text = "This is a small piece of text that should fit in one chunk."
    result = await chunker.chunk(small_text)
    assert len(result) == 1
    assert result[0] == small_text

@pytest.mark.asyncio
async def test_chunk_large_text():
    """Test chunking text larger than window size."""
    # Use a small window size to ensure chunking
    chunker = TokenChunker({"window_size": 10, "window_overlap": 2})
    # This text should generate multiple chunks
    large_text = "This is a longer piece of text that should be split into multiple chunks based on token count."
    result = await chunker.chunk(large_text)
    assert len(result) > 1
    
    # Verify that when combined, chunks contain all the original text
    # (may not be exact due to tokenization/detokenization)
    combined_text = "".join(result)
    assert len(combined_text) >= len(large_text)

@pytest.mark.asyncio
async def test_chunk_overlap():
    """Test that chunks properly overlap."""
    chunker = TokenChunker({"window_size": 10, "window_overlap": 5})
    text = "This is a text that should have overlapping chunks when tokenized properly."
    chunks = await chunker.chunk(text)
    
    # With high overlap, we should have more chunks than with no overlap
    chunker_no_overlap = TokenChunker({"window_size": 10, "window_overlap": 0})
    chunks_no_overlap = await chunker_no_overlap.chunk(text)
    
    assert len(chunks) > len(chunks_no_overlap)
