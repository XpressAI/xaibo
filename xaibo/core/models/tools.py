from typing import Optional, Any, Dict, List

from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Parameter definition for a tool"""
    type: str
    description: Optional[str] = None
    required: Optional[bool] = False
    default: Optional[Any] = None
    enum: Optional[List[str]] = None


class Tool(BaseModel):
    """Definition of a tool that can be executed"""
    name: str
    description: str
    parameters: Dict[str, ToolParameter] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result of a tool execution"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
