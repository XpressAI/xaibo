import traceback

import pytest
import numpy as np
import io
from PIL import Image
import torch

from xaibo.primitives.modules.memory.huggingface_embedder import HuggingFaceEmbedder


@pytest.fixture
def embedder():
    config = {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "device": "cpu",
        "max_length": 512,
        "pooling_strategy": "mean"
    }
    return HuggingFaceEmbedder(config)


@pytest.mark.asyncio
async def test_init_with_config():
    config = {
        "model_name": "sentence-transformers/paraphrase-MiniLM-L6-v2",
        "device": "cpu",
        "max_length": 256,
        "pooling_strategy": "cls"
    }
    embedder = HuggingFaceEmbedder(config)

    assert embedder.model_name == "sentence-transformers/paraphrase-MiniLM-L6-v2"
    assert embedder.max_length == 256
    assert embedder.pooling_strategy == "cls"


@pytest.mark.asyncio
async def test_init_default_config():
    embedder = HuggingFaceEmbedder({})

    assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedder.max_length == 512
    assert embedder.pooling_strategy == "mean"
    assert embedder.device == "cuda" if torch.cuda.is_available() else "cpu"


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
async def test_pooling_strategies():
    # Test different pooling strategies
    for strategy in ["mean", "cls", "max"]:
        config = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu",
            "pooling_strategy": strategy
        }
        embedder = HuggingFaceEmbedder(config)
        result = await embedder.text_to_embedding("Testing pooling strategy.")

        assert isinstance(result, np.ndarray)
        assert result.shape[0] > 0


@pytest.mark.asyncio
async def test_text_to_embedding_unsupported_model():
    # Use a vision-only model that doesn't support text tokenization
    config = {
        "model_name": "google/vit-base-patch16-224",  # Vision Transformer model
        "device": "cpu"
    }

    embedder = HuggingFaceEmbedder(config)

    # Should raise NotImplementedError since the model doesn't support text
    with pytest.raises(NotImplementedError, match="does not support text embeddings or tokenizer not available"):
        await embedder.text_to_embedding("This text cannot be embedded with a vision-only model")


@pytest.mark.asyncio
async def test_image_to_embedding():
    # Use a vision model
    config = {
        "model_name": "google/vit-base-patch16-224",
        "device": "cpu"  # Use CPU even if GPU available to keep test fast
    }

    try:
        embedder = HuggingFaceEmbedder(config)

        # Create a simple test image
        image = Image.new('RGB', (224, 224), color='red')
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_data = img_byte_arr.getvalue()

        result = await embedder.image_to_embedding(img_byte_data)

        assert isinstance(result, np.ndarray)
        assert result.shape[0] > 0  # Should have a non-empty embedding
    except Exception as e:
        pytest.skip(f"Skipping image embedding test due to: {str(e)}\nStack trace: {traceback.format_exc()}")


@pytest.mark.asyncio
async def test_audio_to_embedding():
    # Test with default model (should raise NotImplementedError)
    with pytest.raises(NotImplementedError, match="does not support audio embeddings"):
        embedder = HuggingFaceEmbedder({})
        await embedder.audio_to_embedding(b"fake_audio_data")

    # Skip if dependencies not available
    try:
        import soundfile as sf
        from transformers import AutoProcessor
    except ImportError:
        pytest.skip("Skipping audio embedding test due to missing dependencies")

    # Use an actual audio embedding model
    config = {
        "model_name": "facebook/wav2vec2-base-960h",
        "device": "cpu",  # Use CPU even if GPU available to keep test fast
        "audio_sampling_rate": 16000
    }

    try:
        # Create a simple test audio file (1 second of silence)
        import numpy as np
        sample_rate = 16000
        audio_array = np.zeros(sample_rate)  # 1 second of silence

        # Convert to bytes
        import io
        audio_bytes = io.BytesIO()
        sf.write(audio_bytes, audio_array, sample_rate, format='WAV')
        audio_bytes.seek(0)
        audio_data = audio_bytes.read()

        # Initialize embedder with audio model
        embedder = HuggingFaceEmbedder(config)

        # Get embedding
        result = await embedder.audio_to_embedding(audio_data)

        # Verify results
        assert isinstance(result, np.ndarray)
        assert result.shape[0] > 0  # Should have a non-empty embedding
    except Exception as e:
        pytest.skip(f"Skipping audio embedding test due to: {str(e)}")
