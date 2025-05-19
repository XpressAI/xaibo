import pytest
import asyncio
import numpy as np
import os
import shutil
import tempfile
from xaibo.primitives.modules.memory.numpy_vector_index import NumpyVectorIndex
from xaibo.core.protocols.memory import VectorSearchResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def vector_index(temp_dir):
    """Create a NumpyVectorIndex instance for testing."""
    config = {"storage_dir": temp_dir}
    return NumpyVectorIndex(config)


def test_init_with_config():
    """Test initialization with configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {"storage_dir": temp_dir}
        index = NumpyVectorIndex(config)
        assert index.storage_dir == temp_dir
        assert index.vectors_dir == os.path.join(temp_dir, "vectors")
        assert index.attributes_file == os.path.join(temp_dir, "attributes.pkl")
        assert os.path.exists(index.vectors_dir)


def test_init_without_storage_dir():
    """Test initialization without required storage_dir."""
    with pytest.raises(ValueError, match="storage_dir is required in config"):
        NumpyVectorIndex({})


@pytest.mark.asyncio
async def test_add_vectors(vector_index):
    """Test adding vectors to the index."""
    vectors = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])]
    attributes = [{"name": "vector1"}, {"name": "vector2"}]
    
    await vector_index.add_vectors(vectors, attributes)
    
    assert len(vector_index.attributes) == 2
    assert vector_index.attributes[0]["name"] == "vector1"
    assert vector_index.attributes[1]["name"] == "vector2"
    assert "vector_id" in vector_index.attributes[0]
    assert "vector_file" in vector_index.attributes[0]
    assert os.path.exists(vector_index.attributes[0]["vector_file"])


@pytest.mark.asyncio
async def test_add_vectors_without_attributes(vector_index):
    """Test adding vectors without attributes."""
    vectors = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])]
    
    await vector_index.add_vectors(vectors)
    
    assert len(vector_index.attributes) == 2
    assert vector_index.attributes[0] == {"vector_id": 0, "vector_file": os.path.join(vector_index.vectors_dir, "vector_0.npy")}


@pytest.mark.asyncio
async def test_add_vectors_mismatch_length(vector_index):
    """Test adding vectors with mismatched attributes length."""
    vectors = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])]
    attributes = [{"name": "vector1"}]
    
    with pytest.raises(ValueError, match="Number of vectors and attributes must match"):
        await vector_index.add_vectors(vectors, attributes)


@pytest.mark.asyncio
async def test_search_empty_index(vector_index):
    """Test searching an empty index."""
    query_vector = np.array([1.0, 0.0, 0.0])
    results = await vector_index.search(query_vector)
    assert results == []


@pytest.mark.asyncio
async def test_search(vector_index):
    """Test searching for similar vectors."""
    # Add vectors
    vectors = [
        np.array([1.0, 0.0, 0.0]),  # Vector 1
        np.array([0.0, 1.0, 0.0]),  # Vector 2
        np.array([0.5, 0.5, 0.0]),  # Vector 3
    ]
    attributes = [
        {"name": "vector1"},
        {"name": "vector2"},
        {"name": "vector3"},
    ]
    
    await vector_index.add_vectors(vectors, attributes)
    
    # Search with a query vector similar to vector 1
    query_vector = np.array([0.9, 0.1, 0.0])
    results = await vector_index.search(query_vector, k=2)
    
    assert len(results) == 2
    assert isinstance(results[0], VectorSearchResult)
    assert results[0].attributes["name"] == "vector1"
    assert results[1].attributes["name"] == "vector3"
    assert results[0].similarity_score > results[1].similarity_score


@pytest.mark.asyncio
async def test_vector_normalization(vector_index):
    """Test that vectors are properly normalized."""
    # Add a vector with different magnitudes
    vectors = [
        np.array([2.0, 0.0, 0.0]),  # Will be normalized to [1.0, 0.0, 0.0]
        np.array([0.0, 0.5, 0.0]),  # Will be normalized to [0.0, 1.0, 0.0]
    ]
    
    await vector_index.add_vectors(vectors)
    
    # Search with a normalized vector
    query_vector = np.array([1.0, 0.0, 0.0])
    results = await vector_index.search(query_vector)
    
    # The first vector should have similarity 1.0 (exact match after normalization)
    assert results[0].similarity_score == 1.0
    assert results[0].attributes["vector_id"] == 0


@pytest.mark.asyncio
async def test_zero_vector_normalization(vector_index):
    """Test handling of zero vectors during normalization."""
    # Add a zero vector
    vectors = [np.array([0.0, 0.0, 0.0])]
    
    await vector_index.add_vectors(vectors)
    
    # Search with a non-zero vector
    query_vector = np.array([1.0, 0.0, 0.0])
    results = await vector_index.search(query_vector)
    
    # The similarity should be 0.0
    assert results[0].similarity_score == 0.0

@pytest.mark.asyncio
async def test_large_vector_collection(vector_index):
    """Test handling of a larger collection of vectors."""
    # Create a larger set of vectors
    num_vectors = 100
    dimension = 3
    vectors = [np.random.rand(dimension) for _ in range(num_vectors)]
    attributes = [{"name": f"vector{i}"} for i in range(num_vectors)]
    
    await vector_index.add_vectors(vectors, attributes)
    
    # Verify the index size
    assert len(vector_index.attributes) == num_vectors
    
    # Search with a random query vector
    query_vector = np.random.rand(dimension)
    results = await vector_index.search(query_vector, k=10)
    
    assert len(results) == 10
    assert all(isinstance(result, VectorSearchResult) for result in results)
    assert all(0 <= result.similarity_score <= 1.0 for result in results)
    assert all(result.similarity_score >= next_result.similarity_score 
               for result, next_result in zip(results, results[1:]))


@pytest.mark.asyncio
async def test_duplicate_vectors(vector_index):
    """Test handling of duplicate vectors."""
    # Add the same vector multiple times
    vector = np.array([0.5, 0.5, 0.5])
    vectors = [vector, vector.copy(), vector.copy()]
    attributes = [
        {"name": "original"},
        {"name": "duplicate1"},
        {"name": "duplicate2"}
    ]
    
    await vector_index.add_vectors(vectors, attributes)
    
    # Search with the same vector
    results = await vector_index.search(vector, k=3)
    
    # All should have perfect similarity scores
    assert len(results) == 3
    assert all((result.similarity_score - 1.0) < 1e-8 for result in results)
    assert {result.attributes["name"] for result in results} == {"original", "duplicate1", "duplicate2"}


@pytest.mark.asyncio
async def test_vector_dimension_mismatch(vector_index):
    """Test error handling when vector dimensions don't match."""
    # Add a vector with the correct dimension
    await vector_index.add_vectors([np.array([1.0, 0.0, 0.0])])
    
    # Try to search with a vector of different dimension
    query_vector = np.array([1.0, 0.0])
    with pytest.raises(ValueError):
        await vector_index.search(query_vector)
    
    # Try to add vectors with different dimensions
    with pytest.raises(ValueError):
        await vector_index.add_vectors([np.array([1.0, 0.0])])
