from typing import Dict, Any, List, Optional

from xaibo.core.models import ToolResult, Tool, LLMRole, ToolParameter, LLMMessage, LLMMessageContent, \
    LLMMessageContentType
from xaibo.core.protocols import ToolProviderProtocol, LLMProtocol

from pydantic import BaseModel
from enum import Enum
import base64
import mimetypes

class OneShotToolParameter(BaseModel):
    name: str
    type: str
    description: str

class OneShotToolReturn(BaseModel):
    type: str
    description: str

class OneShotToolMessageType(str, Enum):
    text = 'text'
    image_url = 'image_url'

class OneShotToolConversationMessage(BaseModel):
    type: OneShotToolMessageType
    text: Optional[str] = None
    url: Optional[str] = None

class OneShotToolConversationEntry(BaseModel):
    role: LLMRole
    message: List[OneShotToolConversationMessage]

class OneShotTool(BaseModel):
    name: str
    description: str
    parameters: List[OneShotToolParameter]
    returns: OneShotToolReturn
    conversation: List[OneShotToolConversationEntry]

class OneShotConfig(BaseModel):
    tools: List[OneShotTool]

class OneShotTools(ToolProviderProtocol):
    """
    OneShotTools provides a way to define "one shot" tools that use an LLM prompt with input parameters.
    
    These tools allow processing data through an LLM by defining a conversation template where
    parameter values can be injected into the prompt using the $$params.var_name$$ syntax.
    
    Each tool is defined with:
    - A name and description
    - A list of parameters that can be referenced in the conversation
    - A return type specification
    - A conversation template that will be sent to the LLM with parameter values injected
    
    This approach enables quick creation of tools that leverage LLM capabilities without
    writing custom code for each tool implementation.
    """
    def __init__(self, llm: LLMProtocol, config: dict[str, any]):
        self.llm = llm
        config = OneShotConfig(**config)
        self.tools = {t.name: t for t in config.tools}

    async def list_tools(self) -> List[Tool]:
        return [Tool(
            name=t.name,
            description=t.description,
            parameters={p.name: ToolParameter(
                type=p.type,
                description=p.description,
                required=True,
            ) for p in t.parameters}
        ) for t in self.tools.values()]

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        tool = self.tools[tool_name]
        messages = [LLMMessage(
            role=c.role,
            content=[self._process_message_content(t, parameters) for t in c.message]
        ) for c in tool.conversation]
        response = await self.llm.generate(messages)
        # Extract the response content
        if not response.content:
            return ToolResult(
                success=False,
                error="No response generated",
            )
        
        # Process the response based on the expected return type
        try:
            return ToolResult(
                success=True,
                result=response.content
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error processing tool response: {str(e)}"                
            )

    def _process_message_content(self, message: OneShotToolConversationMessage, parameters: Dict[str, Any]) -> LLMMessageContent:
        if message.type == OneShotToolMessageType.text:
            # Replace parameter references in text with their values
            if message.text:
                processed_text = message.text
                for param_name, param_value in parameters.items():
                    placeholder = f"$$params.{param_name}$$"
                    if placeholder in processed_text:
                        processed_text = processed_text.replace(placeholder, str(param_value))
                return LLMMessageContent(type=LLMMessageContentType.TEXT, text=processed_text)
        else:  # image_url type
            # Check if URL contains parameter references
            if message.url:
                url = message.url
                for param_name, param_value in parameters.items():
                    placeholder = f"$$params.{param_name}$$"
                    if placeholder in url:
                        # Load image from path and convert to base64 data URI
                        image_path = str(param_value)
                        
                        mime_type, _ = mimetypes.guess_type(image_path)
                        if not mime_type:
                            mime_type = 'application/octet-stream'
                        
                        with open(image_path, 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        data_uri = f"data:{mime_type};base64,{img_data}"
                        return LLMMessageContent(type=LLMMessageContentType.IMAGE, image=data_uri)
                
                # If no replacements were made, use the URL as is
                return LLMMessageContent(type=LLMMessageContentType.IMAGE, image=url)
            
        # Raise error for empty messages
        if message.type == OneShotToolMessageType.text:
            raise ValueError("Empty text message content in tool conversation")
        else:  # image_url type
            raise ValueError("Empty image URL in tool conversation")
