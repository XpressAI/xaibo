from typing import BinaryIO

from xaibo.core.models import Response


class Agent:
    def __init__(self, id: str, modules: dict[str, any]):
        self.id = id
        self.modules = modules

    def __str__(self) -> str:
        """Get a string representation of the agent.
        
        Returns:
            str: A string describing the agent and its modules
        """
        module_list = "\n".join(f"  - {module_id}" for module_id in self.modules.keys())
        return f"Agent '{self.id}' with modules:\n{module_list}"

    async def handle_text(self, text: str) -> Response:
        """Handle an incoming text message by delegating to the entry module.
        
        Args:
            text: The text message to handle
            
        Returns:
            Response: The response from handling the text message
            
        Raises:
            AttributeError: If entry module doesn't implement TextMessageHandlerProtocol
        """
        if not hasattr(self.modules["__entry__"], "handle_text"):
            raise AttributeError("Entry module does not implement TextMessageHandlerProtocol")
        await self.modules["__entry__"].handle_text(text)
        return self.modules["__response__"].get_response()

    async def handle_image(self, image: BinaryIO) -> Response:
        """Handle an incoming image by delegating to the entry module.
        
        Args:
            image: The image data to handle
            
        Returns:
            Response: The response from handling the image
            
        Raises:
            AttributeError: If entry module doesn't implement ImageMessageHandlerProtocol
        """
        if not hasattr(self.modules["__entry__"], "handle_image"):
            raise AttributeError("Entry module does not implement ImageMessageHandlerProtocol")
        await self.modules["__entry__"].handle_image(image)
        return self.modules["__response__"].get_response()

    async def handle_audio(self, audio: BinaryIO) -> Response:
        """Handle incoming audio by delegating to the entry module.
        
        Args:
            audio: The audio data to handle
            
        Returns:
            Response: The response from handling the audio
            
        Raises:
            AttributeError: If entry module doesn't implement AudioMessageHandlerProtocol
        """
        if not hasattr(self.modules["__entry__"], "handle_audio"):
            raise AttributeError("Entry module does not implement AudioMessageHandlerProtocol")
        await self.modules["__entry__"].handle_audio(audio)
        return self.modules["__response__"].get_response()

    async def handle_video(self, video: BinaryIO) -> Response:
        """Handle incoming video by delegating to the entry module.
        
        Args:
            video: The video data to handle
            
        Returns:
            Response: The response from handling the video
            
        Raises:
            AttributeError: If entry module doesn't implement VideoMessageHandlerProtocol
        """
        if not hasattr(self.modules["__entry__"], "handle_video"):
            raise AttributeError("Entry module does not implement VideoMessageHandlerProtocol")
        await self.modules["__entry__"].handle_video(video)
        return self.modules["__response__"].get_response()