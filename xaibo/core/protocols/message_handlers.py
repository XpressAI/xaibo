from typing import Protocol, BinaryIO, runtime_checkable


@runtime_checkable
class TextMessageHandlerProtocol(Protocol):
    """Protocol for handling text messages."""

    async def handle_text(self, text: str) -> None:
        """Handle an incoming text message.

        Args:
            text: The text message to handle
        """
        ...

@runtime_checkable
class ImageMessageHandlerProtocol(Protocol):
    """Protocol for handling image messages."""

    async def handle_image(self, image: BinaryIO) -> None:
        """Handle an incoming image message.

        Args:
            image: The image data to handle
        """
        ...

@runtime_checkable
class AudioMessageHandlerProtocol(Protocol):
    """Protocol for handling audio messages."""

    async def handle_audio(self, audio: BinaryIO) -> None:
        """Handle an incoming audio message.

        Args:
            audio: The audio data to handle
        """
        ...

@runtime_checkable
class VideoMessageHandlerProtocol(Protocol):
    """Protocol for handling video messages."""

    async def handle_video(self, video: BinaryIO) -> None:
        """Handle an incoming video message.

        Args:
            video: The video data to handle
        """
        ...
