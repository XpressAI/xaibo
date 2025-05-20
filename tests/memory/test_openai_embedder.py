import os
import pytest
import numpy as np
from openai import BadRequestError

from xaibo.primitives.modules.memory.openai_embedder import OpenAIEmbedder


def test_init_with_api_key():
    """Test initialization with API key in config"""
    config = {"api_key": "dummy_key", "model": "text-embedding-3-small"}

    # This will fail with an actual API call, but we can test the initialization
    embedder = OpenAIEmbedder(config)
    assert embedder.api_key == "dummy_key"
    assert embedder.model == "text-embedding-3-small"

def test_init_missing_api_key():
    """Test initialization fails when API key is missing"""
    # Temporarily clear the OPENAI_API_KEY environment variable
    original_api_key = os.environ.get("OPENAI_API_KEY")
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    try:
        with pytest.raises(ValueError, match="OpenAI API key must be provided"):
            OpenAIEmbedder()
    finally:
        # Restore the original API key if it existed
        if original_api_key is not None:
            os.environ["OPENAI_API_KEY"] = original_api_key

@pytest.mark.asyncio
async def test_image_to_embedding_not_implemented():
    """Test image_to_embedding raises NotImplementedError"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    embedder = OpenAIEmbedder()

    with pytest.raises(NotImplementedError, match="OpenAI doesn't currently support direct image embeddings"):
        await embedder.image_to_embedding(b"fake_image_data")

@pytest.mark.asyncio
async def test_audio_to_embedding_not_implemented():
    """Test audio_to_embedding raises NotImplementedError"""
    # Skip if no API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")

    embedder = OpenAIEmbedder()

    with pytest.raises(NotImplementedError, match="OpenAI doesn't currently support direct audio embeddings"):
        await embedder.audio_to_embedding(b"fake_audio_data")


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY environment variable not set")
async def test_integration_text_to_embedding():
    """Integration test for text_to_embedding with actual API"""
    embedder = OpenAIEmbedder()
    
    # Get embedding for test text
    embedding = await embedder.text_to_embedding("This is a test sentence for embedding.")
    
    # Verify the embedding
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] > 0  # Should have some dimensions
    assert not np.all(embedding == 0)  # Should not be all zeros


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY environment variable not set")
async def test_text_to_embedding_with_custom_model():
    """Test text_to_embedding with custom model"""
    embedder = OpenAIEmbedder({
        "model": "text-embedding-3-small"
    })
    
    # Get embedding for test text
    embedding = await embedder.text_to_embedding("This is a test sentence for embedding.")
    
    # Verify the embedding
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] > 0
    assert not np.all(embedding == 0)


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY environment variable not set")
async def test_text_to_embedding_with_additional_params():
    """Test text_to_embedding with additional parameters"""
    embedder = OpenAIEmbedder({
        "model": "text-embedding-3-small",
        "dimensions": 512,  # Specify reduced dimensions
        "encoding_format": "float"
    })
    
    # Get embedding for test text
    embedding = await embedder.text_to_embedding("This is a test sentence for embedding.")
    
    # Verify the embedding
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] == 512  # Should match the requested dimensions
    assert not np.all(embedding == 0)


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY environment variable not set")
async def test_empty_text_embedding():
    """Test embedding of empty text"""
    embedder = OpenAIEmbedder()
    
    # Get embedding for empty text
    embedding = await embedder.text_to_embedding("")
    
    # Verify the embedding
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] > 0
    # Empty text should still produce a valid embedding


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY environment variable not set")
async def test_long_text_embedding():
    """Test that embedding of long text fails with BadRequestError due to token limit exceeded"""
    embedder = OpenAIEmbedder()

    # Create a long text (over 8000 tokens)
    long_text = "This is a test. " * 2000

    # Should raise BadRequestError due to token limit
    with pytest.raises(BadRequestError, match="maximum context length is 8192 tokens"):
        await embedder.text_to_embedding(long_text)
