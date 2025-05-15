from typing import BinaryIO

from xaibo.core.models import Response
from xaibo.core.exchange import Exchange


class Agent:
    def __init__(self, id: str, exchange: Exchange):
        self.id = id
        self.exchange = exchange

    def __str__(self) -> str:
        """Get a string representation of the agent.
        
        Returns:
            str: A string describing the agent and its modules
        """
        return f"Agent '{self.id}'"

    def get_entry_point_ids(self):
        return self.exchange.get_entry_point_ids()

    def _get_entry_module(self, entry_point_id='__entry__'):
        module = self.exchange.get_module(entry_point_id, caller_id=f"agent:{self.id}")
        return module

    def _get_response_module(self):
        module = self.exchange.get_module("__response__", caller_id=f"agent:{self.id}")
        return module

    async def handle_text(self, text: str, entry_point='__entry__') -> Response:
        """Handle an incoming text message by delegating to the entry module.
        
        Args:
            text: The text message to handle
            
        Returns:
            Response: The response from handling the text message
            
        Raises:
            AttributeError: If entry module doesn't implement TextMessageHandlerProtocol
        """
        entry_module = self._get_entry_module(entry_point)
        if not hasattr(entry_module, "handle_text"):
            raise AttributeError("Entry module does not implement TextMessageHandlerProtocol")
        await entry_module.handle_text(text)
        return await self._get_response_module().get_response()

    async def handle_image(self, image: BinaryIO, entry_point='__entry__') -> Response:
        """Handle an incoming image by delegating to the entry module.
        
        Args:
            image: The image data to handle
            
        Returns:
            Response: The response from handling the image
            
        Raises:
            AttributeError: If entry module doesn't implement ImageMessageHandlerProtocol
        """
        entry_module = self._get_entry_module(entry_point)
        if not hasattr(entry_module, "handle_image"):
            raise AttributeError("Entry module does not implement ImageMessageHandlerProtocol")
        await entry_module.handle_image(image)
        return await self._get_response_module().get_response()

    async def handle_audio(self, audio: BinaryIO, entry_point='__entry__') -> Response:
        """Handle incoming audio by delegating to the entry module.
        
        Args:
            audio: The audio data to handle
            
        Returns:
            Response: The response from handling the audio
            
        Raises:
            AttributeError: If entry module doesn't implement AudioMessageHandlerProtocol
        """
        entry_module = self._get_entry_module(entry_point)
        if not hasattr(entry_module, "handle_audio"):
            raise AttributeError("Entry module does not implement AudioMessageHandlerProtocol")
        await entry_module.handle_audio(audio)
        return await self._get_response_module().get_response()

    async def handle_video(self, video: BinaryIO, entry_point='__entry__') -> Response:
        """Handle incoming video by delegating to the entry module.
        
        Args:
            video: The video data to handle
            
        Returns:
            Response: The response from handling the video
            
        Raises:
            AttributeError: If entry module doesn't implement VideoMessageHandlerProtocol
        """
        entry_module = self._get_entry_module(entry_point)
        if not hasattr(entry_module, "handle_video"):
            raise AttributeError("Entry module does not implement VideoMessageHandlerProtocol")
        await entry_module.handle_video(video)
        return await self._get_response_module().get_response()