from typing import Protocol, List, Optional, AsyncIterator, runtime_checkable

from ..models.llm import LLMMessage, LLMOptions, LLMResponse


@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol for interacting with LLM models"""
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        ...
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM"""
        yield ...
