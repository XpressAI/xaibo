from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from xaibo.core.models.tools import Tool


class LLMRole(str, Enum):
    """Roles for LLM messages"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class LLMMessage(BaseModel):
    """A message in an LLM conversation"""
    role: LLMRole
    content: str
    name: Optional[str] = None


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


class LLMFunctionCall(BaseModel):
    """Function call information returned by an LLM"""
    name: str
    arguments: Dict[str, Any]


class LLMUsage(BaseModel):
    """Token usage statistics from an LLM response"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    """Response from an LLM"""
    content: str
    function_call: Optional[LLMFunctionCall] = None
    usage: Optional[LLMUsage] = None
    vendor_specific: Optional[Dict[str, Any]] = Field(default_factory=dict)
