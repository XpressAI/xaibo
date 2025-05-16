import pytest
import numpy as np
import io
from PIL import Image

from xaibo.primitives.modules.memory.sentence_transformer_embedder import SentenceTransformerEmbedder


@pytest.fixture
def embedder():
    config = {
        "model_name": "all-MiniLM-L6-v2",
        "model_kwargs": {"device": "cpu"}
    }
    return SentenceTransformerEmbedder(config)


@pytest.fixture
def clip_embedder():
    config = {
        "model_name": "clip-ViT-B-32",
        "model_kwargs": {"device": "cpu"}
    }
    return SentenceTransformerEmbedder(config)


@pytest.mark.asyncio
async def test_init_with_config():
    config = {
        "model_name": "paraphrase-MiniLM-L6-v2",
        "model_kwargs": {"device": "cpu"}
    }
    embedder = SentenceTransformerEmbedder(config)

    assert embedder.model_name == "paraphrase-MiniLM-L6-v2"
    assert embedder.is_clip_model is False


@pytest.mark.asyncio
async def test_init_default_config():
    embedder = SentenceTransformerEmbedder({})

    assert embedder.model_name == "all-MiniLM-L6-v2"
    assert embedder.is_clip_model is False


@pytest.mark.asyncio
async def test_text_to_embedding(embedder):
    result = await embedder.text_to_embedding("This is a test sentence.")

    assert isinstance(result, np.ndarray)
    assert result.shape[0] > 0  # Should have a non-empty embedding


@pytest.mark.asyncio
async def test_text_to_embedding_empty_text(embedder):
    result = await embedder.text_to_embedding("   ")

    assert isinstance(result, np.ndarray)
    assert result.shape[0] > 0  # Should have correct dimensionality
    assert np.all(result == 0)  # All zeros for empty text


@pytest.mark.asyncio
async def test_text_to_embedding_different_texts(embedder):
    embedding1 = await embedder.text_to_embedding("Hello world")
    embedding2 = await embedder.text_to_embedding("Completely different text")

    # Different texts should have different embeddings
    assert not np.array_equal(embedding1, embedding2)


@pytest.mark.asyncio
async def test_text_to_embedding_similar_texts(embedder):
    embedding1 = await embedder.text_to_embedding("The cat sat on the mat")
    embedding2 = await embedder.text_to_embedding("A cat is sitting on a mat")

    # Calculate cosine similarity
    similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

    # Similar texts should have relatively high similarity
    assert similarity > 0.7


@pytest.mark.asyncio
async def test_image_to_embedding_non_clip_model(embedder):
    with pytest.raises(NotImplementedError, match="Image embedding requires a CLIP model"):
        await embedder.image_to_embedding(b"fake_image_data")


@pytest.mark.asyncio
async def test_image_to_embedding_clip_model(clip_embedder):
    # Create a simple test image
    image = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_data = img_byte_arr.getvalue()

    result = await clip_embedder.image_to_embedding(img_byte_data)

    assert isinstance(result, np.ndarray)
    assert result.shape[0] > 0  # Should have a non-empty embedding


@pytest.mark.asyncio
async def test_audio_to_embedding(embedder):
    with pytest.raises(NotImplementedError, match="Audio embedding not implemented"):
        await embedder.audio_to_embedding(b"fake_audio_data")
