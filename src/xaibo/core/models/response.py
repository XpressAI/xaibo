from enum import Enum
from typing import BinaryIO, Optional, List


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
