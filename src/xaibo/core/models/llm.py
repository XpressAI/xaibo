from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from xaibo.core.models.tools import Tool

import base64

class LLMRole(str, Enum):
    """Roles for LLM messages"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

class LLMMessageContentType(str, Enum):
    """Content types for LLM messages"""
    TEXT = "text"
    IMAGE = "image"

class LLMFunctionCall(BaseModel):
    """Function call information returned by an LLM"""
    id: str
    name: str
    arguments: Dict[str, Any]

class LLMFunctionResult(BaseModel):
    """Function call result from executing a function"""
    id: str
    name: str
    content: str

class LLMMessageContent(BaseModel):
    """Content of an LLM message"""
    type: LLMMessageContentType
    text: Optional[str] = None
    image: Optional[str] = None

class LLMMessage(BaseModel):
    """A message in an LLM conversation"""
    role: LLMRole
    content: List[LLMMessageContent] = []
    name: Optional[str] = None
    tool_calls: Optional[List[LLMFunctionCall]] = None
    tool_results: Optional[List[LLMFunctionResult]] = None

    @classmethod
    def system(cls, content: str, name: Optional[str] = None) -> 'LLMMessage':
        """Create a system message"""
        return cls(role=LLMRole.SYSTEM, content=[LLMMessageContent(type=LLMMessageContentType.TEXT, text=content)], name=name)

    @classmethod
    def user(cls, content: str, name: Optional[str] = None) -> 'LLMMessage':
        """Create a user message"""
        return cls(role=LLMRole.USER, content=[LLMMessageContent(type=LLMMessageContentType.TEXT, text=content)], name=name)

    @classmethod
    def user_image(cls, image_path: str, name: Optional[str] = None) -> 'LLMMessage':
        """Create a user message with an image"""
        import mimetypes

        mime_type = mimetypes.guess_type(image_path)[0]
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # fallback to jpeg if type cannot be determined

        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            data_uri = f"data:{mime_type};base64,{base64_image}"

        return cls(role=LLMRole.USER, content=[LLMMessageContent(type=LLMMessageContentType.IMAGE, image=data_uri)], name=name)

    @classmethod
    def assistant(cls, content: str, name: Optional[str] = None) -> 'LLMMessage':
        """Create an assistant message"""
        return cls(role=LLMRole.ASSISTANT, content=[LLMMessageContent(type=LLMMessageContentType.TEXT, text=content)], name=name)

    @classmethod
    def function(cls, id: str, name: str, arguments: Dict[str, Any]) -> 'LLMMessage':
        """Create a function message"""
        return cls(role=LLMRole.FUNCTION, content=[], name=name, tool_calls=[LLMFunctionCall(id=id, name=name, arguments=arguments)])

    @classmethod
    def function_result(cls, id: str, name: str, content: str) -> 'LLMMessage':
        """Create a function result message"""
        return cls(role=LLMRole.FUNCTION, content=[], name=name, tool_results=[LLMFunctionResult(id=id, name=name, content=content)])



class LLMOptions(BaseModel):
    """Common options for LLM requests"""
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    functions: Optional[List[Tool]] = None
    vendor_specific: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError('temperature must be between 0 and 2')
        return v

    @field_validator('top_p')
    @classmethod
    def validate_top_p(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('top_p must be between 0 and 1')
        return v


class LLMUsage(BaseModel):
    """Token usage statistics from an LLM response"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    """Response from an LLM"""
    content: str
    tool_calls: Optional[List[LLMFunctionCall]] = None
    usage: Optional[LLMUsage] = None
    vendor_specific: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @classmethod
    def merge(cls, *responses: 'LLMResponse') -> 'LLMResponse':
        """Merge multiple LLM responses into a single response"""
        merged_content = "\n".join(r.content for r in responses)
        merged_tool_calls = []
        merged_usage = None
        merged_vendor_specific = {}

        for response in responses:
            if response.tool_calls:
                merged_tool_calls.extend(response.tool_calls)
            if response.usage:
                if not merged_usage:
                    merged_usage = LLMUsage(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens
                    )
                else:
                    merged_usage.prompt_tokens += response.usage.prompt_tokens
                    merged_usage.completion_tokens += response.usage.completion_tokens
                    merged_usage.total_tokens += response.usage.total_tokens
            if response.vendor_specific:
                merged_vendor_specific.update(response.vendor_specific)

        return cls(
            content=merged_content,
            tool_calls=merged_tool_calls if merged_tool_calls else None,
            usage=merged_usage,
            vendor_specific=merged_vendor_specific
        )
