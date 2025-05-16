from typing import List, Dict, Optional
import tiktoken
from xaibo.core.protocols.memory import ChunkingProtocol


class TokenChunker(ChunkingProtocol):
    """
    A text chunker that uses tiktoken to split text into chunks based on token count.
    Implements the ChunkingProtocol.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the TokenChunker with configuration parameters.
        
        Args:
            config: Dictionary containing configuration parameters:
                - window_size: Maximum number of tokens per chunk (default: 512)
                - window_overlap: Number of tokens to overlap between chunks (default: 50)
                - encoding_name: Name of the tiktoken encoding to use (default: "cl100k_base")
        """
        config = config or {}
        self.window_size = config.get("window_size", 512)
        self.window_overlap = config.get("window_overlap", 50)
        self.encoding_name = config.get("encoding_name", "cl100k_base")
        self.encoding = tiktoken.get_encoding(self.encoding_name)
    
    async def chunk(self, text: str) -> List[str]:
        """
        Chunk text into smaller chunks for embedding based on token count.
        
        Args:
            text: Input text to be split into chunks
            
        Returns:
            List of text chunks suitable for embedding
        """
        if not text.strip():
            return []
        
        # Encode the text into tokens
        tokens = self.encoding.encode(text)
        
        # If text is smaller than window size, return it as a single chunk
        if len(tokens) <= self.window_size:
            return [text]
        
        # Create overlapping chunks
        chunks = []
        i = 0
        
        while i < len(tokens):
            # Get chunk tokens
            chunk_tokens = tokens[i:i + self.window_size]
            
            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move forward by (window_size - window_overlap)
            i += max(1, self.window_size - self.window_overlap)
        
        return chunks
