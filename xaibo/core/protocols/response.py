from typing import Protocol, List, Optional, BinaryIO, runtime_checkable
from enum import Enum

class FileType(Enum):
    """Enum for different types of file attachments"""
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"


class FileAttachment:
    """Model for file attachments in responses"""
    content: BinaryIO
    type: FileType

    def __init__(self, content: BinaryIO, type: FileType) -> None:
        self.content = content
        self.type = type


class Response:
    """Model for responses that can include text and file attachments"""
    text: Optional[str] = None
    attachments: List[FileAttachment] = []

    def __init__(self, text: Optional[str] = None, attachments: Optional[List[FileAttachment]] = None) -> None:
        self.text = text
        self.attachments = attachments or []

@runtime_checkable
class ResponseProtocol(Protocol):
    """Protocol for sending responses."""

    def get_response(self) -> Response:
        """Get the current response object.

        Returns:
            Response: The current response object containing text and/or attachments
        """
        ...

    async def respond_text(self, response: str) -> None:
        """Send a response.

        Args:
            response: The response text to send
        """
        ...

    async def respond_image(self, iolike: BinaryIO) -> None:
        """Send an image response.

        Args:
            iolike: IO object containing the image data
        """
        ...

    async def respond_audio(self, iolike: BinaryIO) -> None:
        """Send an audio response.

        Args:
            iolike: IO object containing the audio data
        """
        ...

    async def respond_file(self, iolike: BinaryIO) -> None:
        """Send a file response.

        Args:
            iolike: IO object containing the file data
        """
        ...

    async def respond(self, response: Response) -> None:
        """Send a complex response containing text and/or file attachments.

        Args:
            response: Response object containing text and attachments
        """
        ...