from typing import Protocol, List, Optional, BinaryIO
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


class Response:
    """Model for responses that can include text and file attachments"""
    text: Optional[str] = None
    attachments: List[FileAttachment] = []


class ResponseProtocol(Protocol):
    """Protocol for sending responses."""

    def respond_text(self, response: str) -> None:
        """Send a response.

        Args:
            response: The response text to send
        """
        ...

    def respond_image(self, iolike: BinaryIO) -> None:
        """Send an image response.

        Args:
            iolike: IO object containing the image data
        """
        ...

    def respond_audio(self, iolike: BinaryIO) -> None:
        """Send an audio response.

        Args:
            iolike: IO object containing the audio data
        """
        ...

    def respond_file(self, iolike: BinaryIO) -> None:
        """Send a file response.

        Args:
            iolike: IO object containing the file data
        """
        ...

    def respond(self, response: Response) -> None:
        """Send a complex response containing text and/or file attachments.

        Args:
            response: Response object containing text and attachments
        """
        ...