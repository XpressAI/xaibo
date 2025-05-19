from typing import List, Dict, Any, Optional
import numpy as np
import os
import pickle
from xaibo.core.protocols.memory import VectorIndexProtocol, VectorSearchResult

class NumpyVectorIndex(VectorIndexProtocol):
    """
    Implementation of VectorIndexProtocol using NumPy for vector storage and similarity search.
    Uses dot product for similarity calculation with normalized vectors (equivalent to cosine similarity).
    Stores vectors as individual numpy files and attributes in a pickle file.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the NumpyVectorIndex with configuration parameters.
        
        Args:
            config: Dictionary containing configuration parameters:
                - storage_dir: Directory path for storing vector and attribute files
        """
        if "storage_dir" not in config:
            raise ValueError("storage_dir is required in config")
            
        self.storage_dir = config["storage_dir"]
        self.vectors_dir = os.path.join(self.storage_dir, "vectors")
        self.attributes_file = os.path.join(self.storage_dir, "attributes.pkl")
        
        # Create directories if they don't exist
        os.makedirs(self.vectors_dir, exist_ok=True)
        
        # Load existing attributes if file exists
        if os.path.exists(self.attributes_file):
            with open(self.attributes_file, 'rb') as f:
                self.attributes = pickle.load(f)
        else:
            self.attributes = []
        
        # Track vector dimension
        self.vector_dimension = None
    
    def _save_attributes(self):
        """Save attributes to disk using pickle"""
        with open(self.attributes_file, 'wb') as f:
            pickle.dump(self.attributes, f)
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector to unit length"""
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm
        return vector
    
    async def add_vectors(self, vectors: List[np.ndarray], attributes: Optional[List[dict]] = None) -> None:
        """
        Add vectors to the index with optional attributes
        
        Args:
            vectors: List of vector embeddings to add to index
            attributes: Optional list of attribute dictionaries, one per vector
            
        Raises:
            ValueError: If vectors have inconsistent dimensions
        """
        if attributes is None:
            attributes = [{} for _ in vectors]
        
        if len(vectors) != len(attributes):
            raise ValueError("Number of vectors and attributes must match")
        
        # Check vector dimensions
        for vector in vectors:
            if self.vector_dimension is None:
                self.vector_dimension = vector.shape[0]
            elif vector.shape[0] != self.vector_dimension:
                raise ValueError(f"Vector dimension mismatch. Expected {self.vector_dimension}, got {vector.shape[0]}")
        
        # Get current index count
        start_idx = len(self.attributes)
        
        # Add each vector and its attributes
        for i, (vector, attr) in enumerate(zip(vectors, attributes)):
            idx = start_idx + i
            
            # Normalize vector
            normalized_vector = self._normalize_vector(vector)
            
            # Save vector to file
            vector_file = os.path.join(self.vectors_dir, f"vector_{idx}.npy")
            np.save(vector_file, normalized_vector)
            
            # Add attributes with reference to vector file
            attr_with_ref = attr.copy()
            attr_with_ref["vector_file"] = vector_file
            attr_with_ref["vector_id"] = idx
            self.attributes.append(attr_with_ref)
        
        # Save updated attributes
        self._save_attributes()
    
    async def search(self, query_vector: np.ndarray, k: int = 10) -> List[VectorSearchResult]:
        """
        Search for similar vectors given a query vector
        
        Args:
            query_vector: Vector embedding to search for
            k: Number of results to return (default: 10)
            
        Returns:
            List of VectorSearchResult objects containing search results with similarity scores and attributes
            
        Raises:
            ValueError: If query vector dimension doesn't match the index vectors
        """
        if not self.attributes:
            return []
        
        # Check query vector dimension
        if self.vector_dimension is not None and query_vector.shape[0] != self.vector_dimension:
            raise ValueError(f"Query vector dimension mismatch. Expected {self.vector_dimension}, got {query_vector.shape[0]}")
        
        # Normalize query vector
        query_vector = self._normalize_vector(query_vector)
        
        results = []
        
        # Calculate similarity for each vector
        for attr in self.attributes:
            vector_file = attr["vector_file"]
            
            # Load vector
            vector = np.load(vector_file)
            
            # Calculate similarity (dot product for normalized vectors = cosine similarity)
            similarity = np.dot(query_vector, vector)
            
            results.append((similarity, attr))
        
        # Sort by similarity (highest first)
        results.sort(reverse=True, key=lambda x: x[0])
        
        # Return top k results
        return [
            VectorSearchResult(
                vector_id=str(attr["vector_id"]),
                similarity_score=float(sim),
                attributes=attr
            )
            for sim, attr in results[:k]
        ]
