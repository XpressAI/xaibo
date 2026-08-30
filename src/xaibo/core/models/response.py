from enum import Enum
from typing import BinaryIO, Optional, List, Any, Dict, Literal, Union

from pydantic import BaseModel

from xaibo.core.models.llm import LLMUsage


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


class ToolCallEvent(BaseModel):
    """A tool is about to be executed"""
    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResultEvent(BaseModel):
    """A tool execution finished"""
    type: Literal["tool_result"] = "tool_result"
    id: str
    name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class UsageEvent(LLMUsage):
    """Token usage reported by an LLM call"""
    type: Literal["usage"] = "usage"


ResponseEvent = Union[
    ToolCallEvent,
    ToolResultEvent,
    UsageEvent,
]


class Response:
    """Model for responses that can include text, file attachments and structured events"""
    text: Optional[str] = None
    attachments: List[FileAttachment] = []
    events: List[ResponseEvent]

    def __init__(self, text: Optional[str] = None, attachments: Optional[List[FileAttachment]] = None,
                 events: Optional[List[ResponseEvent]] = None) -> None:
        self.text = text
        self.attachments = attachments or []
        self.events = events or []
