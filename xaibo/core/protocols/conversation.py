from typing import Protocol, List, runtime_checkable
from ..models.llm import LLMMessage

@runtime_checkable
class ConversationHistoryProtocol(Protocol):
    """Protocol for accessing conversation history"""
    
    async def get_history(self) -> List[LLMMessage]:
        """Get the current conversation history
        
        Returns:
            List[LLMMessage]: List of messages in the conversation history, 
            ordered from oldest to newest
        """
        ...

    async def add_message(self, message: LLMMessage) -> None:
        """Add a message to the conversation history
        
        Args:
            message: The message to add to the history
        """
        ...

    async def clear_history(self) -> None:
        """Clear the conversation history"""
        ...



