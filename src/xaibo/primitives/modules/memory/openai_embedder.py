import os
import logging
import numpy as np
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from xaibo.core.protocols.memory import EmbeddingProtocol

logger = logging.getLogger(__name__)

class OpenAIEmbedder(EmbeddingProtocol):
    """Implementation of EmbeddingProtocol using OpenAI's embedding API"""
    
    def __init__(
        self,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the OpenAI embedder client.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - api_key: OpenAI API key. If not provided, will try to get from OPENAI_API_KEY env var.
                - model: The model to use for embeddings. Default is "text-embedding-ada-002".
                - base_url: Base URL for the OpenAI API. Default is "https://api.openai.com/v1".
                - timeout: Timeout for API requests in seconds. Default is 60.0.
                - Any additional keys will be passed as arguments to the API.
        """
        config = config or {}
        
        self.api_key = config.get('api_key') or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.model = config.get('model', "text-embedding-ada-002")
        
        # Extract known configuration parameters
        base_url = config.get('base_url', "https://api.openai.com/v1")
        timeout = config.get('timeout', 60.0)
        
        # Create client with core parameters
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=timeout
        )
        
        # Store any additional parameters as default kwargs
        self.default_kwargs = {k: v for k, v in config.items() 
                              if k not in ['api_key', 'model', 'base_url', 'timeout']}
    
    async def text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text into vector embedding
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array representing the vector embedding
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                **self.default_kwargs
            )
            
            # Extract the embedding from the response
            embedding = response.data[0].embedding
            
            return np.array(embedding)
        except Exception as e:
            logger.error(f"Error generating text embedding from OpenAI: {str(e)}")
            raise
    
    async def image_to_embedding(self, image_data: bytes) -> np.ndarray:
        """Convert image data into vector embedding
        
        Args:
            image_data: Raw image bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
            
        Raises:
            NotImplementedError: OpenAI doesn't currently support direct image embeddings
        """
        raise NotImplementedError("OpenAI doesn't currently support direct image embeddings")
    
    async def audio_to_embedding(self, audio_data: bytes) -> np.ndarray:
        """Convert audio data into vector embedding
        
        Args:
            audio_data: Raw audio bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
            
        Raises:
            NotImplementedError: OpenAI doesn't currently support direct audio embeddings
        """
        raise NotImplementedError("OpenAI doesn't currently support direct audio embeddings")
