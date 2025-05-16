from typing import Dict, Any
import numpy as np
from transformers import AutoModel, AutoTokenizer, AutoFeatureExtractor, AutoProcessor
import torch
from PIL import Image
import io

from xaibo.core.protocols.memory import EmbeddingProtocol


class HuggingFaceEmbedder(EmbeddingProtocol):
    """
    Implementation of EmbeddingProtocol using Hugging Face models.
    Provides embedding functionality for text, images, and potentially audio/video
    with configurable model selection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the HuggingFaceEmbedder with configuration parameters.
        
        Args:
            config: Dictionary containing configuration parameters:
                - model_name: Name of the Hugging Face model to use 
                  (default: "sentence-transformers/all-MiniLM-L6-v2")
                - device: Device to run model on (default: "cuda" if available, else "cpu")
                - max_length: Maximum sequence length for tokenizer (default: 512)
                - pooling_strategy: How to pool token embeddings (default: "mean")
                  Options: "mean", "cls", "max"
        """
        self.model_name = config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
        self.device = config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = config.get("max_length", 512)
        self.pooling_strategy = config.get("pooling_strategy", "mean")
        
        # Load model and tokenizer
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        
        # Try to load tokenizer, but handle case where model doesn't support text
        self.tokenizer = None
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except (OSError, ValueError, AttributeError, KeyError):
            # Model might not support text tokenization
            pass
        
        # For image models, also load feature extractor if available
        self.feature_extractor = None
        try:
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(self.model_name)
        except:
            pass  # Not all models have feature extractors

        # For audio models, try to load processor if available
        self.audio_processor = None
        try:
            # Check if the model architecture is designed for audio processing
            model_config = self.model.config
            is_audio_model = hasattr(model_config, 'model_type') and model_config.model_type in [
                'wav2vec2', 'hubert', 'whisper', 'unispeech', 'wavlm', 'data2vec_audio'
            ]
            
            if is_audio_model:
                self.audio_processor = AutoProcessor.from_pretrained(self.model_name)
            else:
                self.audio_processor = None
        except (ImportError, OSError, ValueError, AttributeError):
            pass  # Not all models have audio processors or the model might not support audio
        
        # Audio processing configuration
        self.audio_sampling_rate = config.get("audio_sampling_rate", 16000)  # Default for many speech models
        self.audio_max_length = config.get("audio_max_length", 30)  # Max audio length in seconds
        self.audio_return_tensors = config.get("audio_return_tensors", "pt")  # PyTorch tensors
        
        # Set model to evaluation mode
        self.model.eval()

    def _pool_embeddings(self, token_embeddings, attention_mask=None):
        """
        Pool token embeddings based on the configured strategy.
        
        Args:
            token_embeddings: Token embeddings from model
            attention_mask: Attention mask for valid tokens
            
        Returns:
            Pooled embedding vector
        """
        if self.pooling_strategy == "cls":
            # Use [CLS] token embedding (first token)
            return token_embeddings[:, 0]
        elif self.pooling_strategy == "max":
            # Max pooling
            if attention_mask is not None:
                # Set padding tokens to large negative value
                token_embeddings[attention_mask == 0] = -1e9
            return torch.max(token_embeddings, dim=1)[0]
        else:  # Default to mean pooling
            if attention_mask is not None:
                # Apply attention mask
                token_embeddings = token_embeddings * attention_mask.unsqueeze(-1)
                # Sum and divide by number of tokens
                sum_embeddings = torch.sum(token_embeddings, dim=1)
                sum_mask = torch.sum(attention_mask, dim=1, keepdim=True)
                sum_mask = torch.clamp(sum_mask, min=1e-9)  # Prevent division by zero
                return sum_embeddings / sum_mask
            else:
                return torch.mean(token_embeddings, dim=1)

    async def text_to_embedding(self, text: str) -> np.ndarray:
        """
        Convert text into vector embedding using the Hugging Face model.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array representing the vector embedding
            
        Raises:
            NotImplementedError: If model doesn't support text embeddings
        """
        if self.tokenizer is None:
            raise NotImplementedError(
                f"Model {self.model_name} does not support text embeddings or tokenizer not available"
            )
            
        if not text.strip():
            # Return zero vector with correct dimensionality
            with torch.no_grad():
                # Get dimensionality from model config
                hidden_size = self.model.config.hidden_size
                return np.zeros(hidden_size)
        
        try:
            # Tokenize text
            inputs = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                token_embeddings = outputs.last_hidden_state
                
                # Pool embeddings
                pooled_embedding = self._pool_embeddings(
                    token_embeddings, 
                    inputs.get("attention_mask")
                )
                
                # Convert to numpy and return
                return pooled_embedding.cpu().numpy().flatten()
        except Exception as e:
            # Handle tokenization or model errors
            raise ValueError(f"Failed to generate text embedding: {str(e)}")
    
    async def image_to_embedding(self, image_data: bytes) -> np.ndarray:
        """
        Convert image data into vector embedding using the Hugging Face model.
        
        Args:
            image_data: Raw image bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
        
        Raises:
            NotImplementedError: If model doesn't support image embeddings
        """
        if self.feature_extractor is None:
            raise NotImplementedError(
                f"Model {self.model_name} does not support image embeddings or feature extractor not available"
            )
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Process image with feature extractor
        inputs = self.feature_extractor(images=image, return_tensors="pt").to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Different models output different structures
            if hasattr(outputs, "last_hidden_state"):
                # For vision transformer models
                embeddings = outputs.last_hidden_state
                pooled_embedding = self._pool_embeddings(embeddings)
            elif hasattr(outputs, "pooler_output"):
                # For models with pooler output
                pooled_embedding = outputs.pooler_output
            else:
                # Fallback to first output
                pooled_embedding = outputs[0][:, 0]  # Take CLS token
            
            # Convert to numpy and return
            return pooled_embedding.cpu().numpy().flatten()
    
    async def audio_to_embedding(self, audio_data: bytes) -> np.ndarray:
        """
        Convert audio data into vector embedding using the Hugging Face model.
        
        Args:
            audio_data: Raw audio bytes to embed
            
        Returns:
            Numpy array representing the vector embedding
        
        Raises:
            NotImplementedError: If model doesn't support audio embeddings
        """
        if self.audio_processor is None:
            raise NotImplementedError(
                f"Model {self.model_name} does not support audio embeddings or processor not available"
            )
        
        # Convert bytes to audio file
        import io
        import soundfile as sf
        import numpy as np
        
        # Load audio from bytes
        audio_array, sampling_rate = sf.read(io.BytesIO(audio_data))
        
        # Process audio with processor
        inputs = self.audio_processor(
            audio_array, 
            sampling_rate=sampling_rate, 
            return_tensors="pt"
        ).to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Different models output different structures
            if hasattr(outputs, "last_hidden_state"):
                embeddings = outputs.last_hidden_state
                pooled_embedding = self._pool_embeddings(embeddings)
            elif hasattr(outputs, "pooler_output"):
                pooled_embedding = outputs.pooler_output
            else:
                # Fallback to mean pooling over sequence dimension
                pooled_embedding = outputs[0].mean(dim=1)
            
            # Convert to numpy and return
            return pooled_embedding.cpu().numpy().flatten()