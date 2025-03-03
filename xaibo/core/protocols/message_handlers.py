from typing import Protocol, BinaryIO


class TextMessageHandlerProtocol(Protocol):
    """Protocol for handling text messages."""

    def handle_text(self, text: str) -> None:
        """Handle an incoming text message.

        Args:
            text: The text message to handle
        """
        ...


class ImageMessageHandlerProtocol(Protocol):
    """Protocol for handling image messages."""

    def handle_image(self, image: BinaryIO) -> None:
        """Handle an incoming image message.

        Args:
            image: The image data to handle
        """
        ...


class AudioMessageHandlerProtocol(Protocol):
    """Protocol for handling audio messages."""

    def handle_audio(self, audio: BinaryIO) -> None:
        """Handle an incoming audio message.

        Args:
            audio: The audio data to handle
        """
        ...


class VideoMessageHandlerProtocol(Protocol):
    """Protocol for handling video messages."""

    def handle_video(self, video: BinaryIO) -> None:
        """Handle an incoming video message.

        Args:
            video: The video data to handle
        """
        ...
