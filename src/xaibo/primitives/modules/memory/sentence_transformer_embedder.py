from typing import Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from xaibo.core.protocols.memory import EmbeddingProtocol



class SentenceTransformerEmbedder(EmbeddingProtocol):
    """
    Implementation of EmbeddingProtocol using SentenceTransformer models.
    Provides text embedding functionality with configurable model selection.
    Supports CLIP models for multimodal (text and image) embeddings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SentenceTransformerEmbedder with configuration parameters.
        
        Args:
            config: Dictionary containing configuration parameters:
                - model_name: Name of the sentence-transformer model to use 
                  (default: "all-MiniLM-L6-v2")
                  For multimodal support, use a CLIP model like "clip-ViT-B-32"
                - model_kwargs: Optional dictionary of keyword arguments to pass to SentenceTransformer
                  constructor (e.g., cache_folder, device, etc.)
        """
        self.model_name = config.get("model_name", "all-MiniLM-L6-v2")
        model_kwargs = config.get("model_kwargs", {})
        self.model = SentenceTransformer(self.model_name, **model_kwargs)
        self.is_clip_model = "clip" in self.model_name.lower()

    async def text_to_embedding(self, text: str) -> np.ndarray:
        """
        Convert text into vector embedding using the SentenceTransformer model.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array representing the vector embedding
        """
        if not text.strip():
            # Return zero vector with correct dimensionality if text is empty
            embedding_dim = self.model.get_sentence_embedding_dimension()
            return np.zeros(embedding_dim)
        
        return self.model.encode(text, convert_to_numpy=True)
    
    async def image_to_embedding(self, image_data: bytes) -> np.ndarray:
        """
        Convert image data into vector embedding using CLIP model.
        
        Args:
            image_data: Raw image bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
        
        Raises:
            NotImplementedError: If not using a CLIP model
        """
        if not self.is_clip_model:
            raise NotImplementedError("Image embedding requires a CLIP model like 'clip-ViT-B-32'")
        from PIL import Image
        import io
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Encode the image
        return self.model.encode(image, convert_to_numpy=True)
    
    async def audio_to_embedding(self, audio_data: bytes) -> np.ndarray:
        """
        Convert audio data into vector embedding.
        
        Args:
            audio_data: Raw audio bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
        
        Raises:
            NotImplementedError: This method is not implemented for this embedder
        """
        raise NotImplementedError("Audio embedding not implemented for SentenceTransformerEmbedder")