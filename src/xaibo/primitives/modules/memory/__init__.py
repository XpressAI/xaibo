from .numpy_vector_index import *
from .vector_memory import *
from .memory_provider import *

# The modules below pull heavy optional dependencies (tiktoken, torch,
# sentence-transformers, openai). Importing them eagerly makes every import
# of this package pay their cost — e.g. the config loader imports a memory
# submodule while parsing agent configs, which used to drag torch (and its
# NumPy-version warning wall) into agents that never embed anything.
# PEP 562 lazy loading defers each import until the class is first accessed.
_LAZY_EXPORTS = {
    "TokenChunker": ".token_chunker",
    "SentenceTransformerEmbedder": ".sentence_transformer_embedder",
    "HuggingFaceEmbedder": ".huggingface_embedder",
    "OpenAIEmbedder": ".openai_embedder",
}


def __getattr__(name):
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib
    try:
        module = importlib.import_module(target, __name__)
    except ImportError as e:
        # Same visible behavior as the old guarded eager imports: when the
        # optional dependency is missing, the name does not exist here.
        raise AttributeError(f"{name} is unavailable: {e}") from e
    return getattr(module, name)


def __dir__():
    return sorted(set(globals()) | set(_LAZY_EXPORTS))
