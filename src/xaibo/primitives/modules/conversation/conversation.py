from typing import List, Optional
from xaibo.core.protocols import ConversationHistoryProtocol
from xaibo.core.models.llm import LLMMessage, LLMRole, LLMMessageContent, LLMMessageContentType


class SimpleConversation(ConversationHistoryProtocol):
    """
    A simple implementation of the ConversationHistoryProtocol that maintains
    conversation history in memory and can be initialized from OpenAI API format.
    """
    
    @classmethod
    def provides(cls):
        """
        Specifies which protocols this class implements.
        
        Returns:
            list: List of protocols provided by this class
        """
        return [ConversationHistoryProtocol]
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the SimpleConversation module.
        
        Args:
            config: Configuration dictionary with optional parameters:
                   - max_history: Maximum number of messages to keep in history
                   - initial_messages: List of messages in OpenAI format to initialize history
        """
        self.config = config or {}
        self.max_history = self.config.get('max_history', 100)
        self._history: List[LLMMessage] = []
        
        # Initialize from OpenAI format messages if provided
        initial_messages = self.config.get('initial_messages', [])
        if initial_messages:
            for msg in initial_messages:
                self._history.append(self._convert_openai_message(msg))
    
    def _convert_openai_message(self, openai_msg: dict) -> LLMMessage:
        """
        Convert an OpenAI format message to an LLMMessage.
        
        Args:
            openai_msg: Message in OpenAI format with 'role' and 'content' keys
            
        Returns:
            LLMMessage: Converted message
        """
        role_map = {
            'system': LLMRole.SYSTEM,
            'user': LLMRole.USER,
            'assistant': LLMRole.ASSISTANT,
            'function': LLMRole.FUNCTION
        }
        
        role = role_map.get(openai_msg.get('role', ''), LLMRole.USER)
        content = openai_msg.get('content', '')
        name = openai_msg.get('name', None)
        
        # Handle image type messages
        if isinstance(content, list):
            # OpenAI image messages have content as a list of objects
            message_contents = []
            for content_item in content:
                content_type = content_item.get('type')
                if content_type == 'image_url':
                    message_contents.append(
                        LLMMessageContent(
                            type=LLMMessageContentType.IMAGE,
                            image=content_item.get('image_url', {}).get('url', '')
                        )
                    )
                elif content_type == 'text':
                    message_contents.append(
                        LLMMessageContent(
                            type=LLMMessageContentType.TEXT,
                            text=content_item.get('text', '')
                        )
                    )
            
            # Use all message contents
            message_contents = message_contents if message_contents else [LLMMessageContent(
                type=LLMMessageContentType.TEXT,
                text=''
            )]
        else:
            # Regular text message
            message_contents = [LLMMessageContent(
                type=LLMMessageContentType.TEXT,
                text=content
            )]
        
        return LLMMessage(
            role=role,
            content=message_contents,
            name=name
        )
    
    async def get_history(self) -> List[LLMMessage]:
        """
        Get the current conversation history.
        
        Returns:
            List[LLMMessage]: List of messages in the conversation history,
            ordered from oldest to newest
        """
        return self._history.copy()
    
    async def add_message(self, message: LLMMessage) -> None:
        """
        Add a message to the conversation history.
        If the history exceeds max_history, the oldest messages are removed.
        
        Args:
            message: The message to add to the history
        """
        self._history.append(message)
        
        # Trim history if it exceeds the maximum length
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
    
    async def clear_history(self) -> None:
        """
        Clear the conversation history.
        """
        self._history = []
    
    @classmethod
    def from_openai_messages(cls, messages: List[dict], config: Optional[dict] = None) -> 'SimpleConversation':
        """
        Create a SimpleConversation instance from a list of OpenAI format messages.
        
        Args:
            messages: List of messages in OpenAI format
            config: Additional configuration options
            
        Returns:
            SimpleConversation: New conversation instance with the provided messages
        """
        config = config or {}
        config['initial_messages'] = messages
        return cls(config)

