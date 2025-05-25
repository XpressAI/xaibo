from typing import AsyncIterator, Dict, List, Optional, Any
import logging

from google import genai
from google.genai import types

import base64

from xaibo.core.models.llm import LLMMessage, LLMMessageContentType, LLMOptions, LLMResponse, LLMFunctionCall, LLMUsage, LLMRole
from xaibo.core.protocols.llm import LLMProtocol

logger = logging.getLogger(__name__)


class GoogleLLM(LLMProtocol):
    """Implementation of LLMProtocol for Google's Gemini API"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Gemini LLM client.
        
        Args:
            config: Dictionary containing configuration parameters.
                Required:
                    - api_key: API key for Google Gemini API
                Optional:
                    - model: Default model to use (default: 'gemini-2.0-flash-001')
                    - vertexai: Whether to use Vertex AI (default: False)
                    - project: Project ID for Vertex AI
                    - location: Location for Vertex AI (default: 'us-central1')
        """
        self.model = config.get("model", "gemini-2.0-flash-001")
        
        # Initialize the client based on configuration
        if config.get("vertexai", False):
            self.client = genai.Client(
                vertexai=True,
                project=config.get("project"),
                location=config.get("location", "us-central1")
            )
        else:
            self.client = genai.Client(api_key=config.get("api_key"))

    def _convert_messages_to_contents(self, messages: List[LLMMessage]) -> List[types.Content]:
        """Convert LLMMessages to Google Gemini API format"""
        contents = []
        
        for msg in messages:
            if msg.role == LLMRole.FUNCTION:
                if msg.tool_calls:
                    # This is the message that originally called for tool execution
                    content = types.Content(
                        role="model",
                        parts=[]
                    )
                    if msg.content:
                        for content_item in msg.content:
                            if content_item.text:
                                content.parts.append(types.Part.from_text(text=content_item.text))
                    for tool_call in msg.tool_calls:
                        content.parts.append(types.Part.from_function_call(
                            name=tool_call.name,
                            args=tool_call.arguments
                        ))
                    contents.append(content)
                elif msg.tool_results:
                    # This is the message that contains the tool execution results
                    for result in msg.tool_results:
                        contents.append(types.Content(
                            role="function",
                            parts=[types.Part.from_function_response(
                                name=result.name,
                                response={"result": result.content}
                            )]
                        ))
                else:
                    # This is a malformed message
                    logger.warning("Malformed function message - missing both tool_calls and tool_results")
            else:
                role = "user" if msg.role == LLMRole.USER else "model"
                if msg.role == LLMRole.SYSTEM:
                    continue
                
                parts = []
                for content_item in msg.content:
                    if content_item.type == LLMMessageContentType.TEXT and content_item.text:
                        parts.append(types.Part.from_text(text=content_item.text))
                    elif content_item.type == LLMMessageContentType.IMAGE and content_item.image:
                        parts.append(self._convert_image(content_item.image))
                
                content = types.Content(
                    role=role,
                    parts=parts
                )
                if msg.name:
                    content.name = msg.name
                    
                contents.append(content)
                
        return contents

    def _convert_image(self, image: str) -> types.Part:
        """Convert image URL or data URI to Google Part"""
        if image.startswith('data:'):
            # Handle data URI
            # Extract mime type and base64 data from data URI
            mime_type = image.split(';')[0].split(':')[1]
            base64_data = image.split(',')[1]            
            image_bytes = base64.b64decode(base64_data)
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        else:
            # Handle URL - assume image/jpeg if can't determine
            mime_type = 'image/jpeg'
            if image.lower().endswith('.png'):
                mime_type = 'image/png'
            elif image.lower().endswith('.gif'):
                mime_type = 'image/gif'
            elif image.lower().endswith('.webp'):
                mime_type = 'image/webp'
            return types.Part.from_uri(file_uri=image, mime_type=mime_type)

    def _prepare_config(self, options: Optional[LLMOptions]) -> types.GenerateContentConfig:
        """Prepare configuration for the API request"""
        if not options:
            return None
            
        config_dict = {}
        
        # Map standard parameters
        if options.temperature is not None:
            config_dict["temperature"] = options.temperature
        if options.top_p is not None:
            config_dict["top_p"] = options.top_p
        if options.max_tokens is not None:
            config_dict["max_output_tokens"] = options.max_tokens
        if options.stop_sequences:
            config_dict["stop_sequences"] = options.stop_sequences
            
        # Handle functions/tools
        if options.functions:
            tools = []
            for function in options.functions:
                function_declaration = types.FunctionDeclaration(
                    name=function.name,
                    description=function.description,
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            param_name: types.Schema(
                                type=param.type,
                                description=param.description,
                                enum=param.enum,
                                default=param.default
                            )
                            for param_name, param in function.parameters.items()
                        }
                    )
                )
                tools.append(types.Tool(function_declarations=[function_declaration]))
            config_dict["tools"] = tools
            
        # Add any vendor-specific parameters
        if options.vendor_specific:
            config_dict.update(options.vendor_specific)
            
        return types.GenerateContentConfig(**config_dict)

    def _extract_system_instruction(self, messages: List[LLMMessage]) -> Optional[str]:
        """Extract system instructions from messages"""
        system_messages = [
            content.text 
            for msg in messages 
            if msg.role == LLMRole.SYSTEM
            for content in msg.content
            if content.type == LLMMessageContentType.TEXT and content.text
        ]
        if system_messages:
            return "\n".join(system_messages)
        return None
    
    def _process_response(self, response) -> LLMResponse:
        """Process the API response into LLMResponse format"""
        # Extract function call and content if present
        function_call = None
        content = ""
        
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        function_call = LLMFunctionCall(
                            id=part.function_call.id or f"call_{hash(part.function_call.name)}",
                            name=part.function_call.name,
                            arguments=part.function_call.args
                        )
                    elif hasattr(part, "text"):
                        content += part.text
        
        # Extract usage information if available
        usage = None
        if hasattr(response, "usage_metadata"):
            usage = LLMUsage(
                prompt_tokens=getattr(response.usage_metadata, "prompt_token_count", 0),
                completion_tokens=getattr(response.usage_metadata, "candidates_token_count", 0),
                total_tokens=getattr(response.usage_metadata, "total_token_count", 0)
            )
        
        # Create the response object
        return LLMResponse(
            content=content,
            tool_calls=[function_call] if function_call is not None else None,
            usage=usage,
            vendor_specific={"raw_response": response}
        )
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response from the Google Gemini LLM"""
        contents = self._convert_messages_to_contents(messages)
        config = self._prepare_config(options)
        
        # Extract system instruction if present
        system_instruction = self._extract_system_instruction(messages)
        if system_instruction and config:
            config.system_instruction = system_instruction
        
        # Use the model specified in options if available
        model = options.vendor_specific.get("model", self.model) if options and options.vendor_specific else self.model
        
        # Make the API call
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        return self._process_response(response)
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the Google Gemini LLM"""
        contents = self._convert_messages_to_contents(messages)
        config = self._prepare_config(options)
        
        # Extract system instruction if present
        system_instruction = self._extract_system_instruction(messages)
        if system_instruction and config:
            config.system_instruction = system_instruction
        
        # Use the model specified in options if available
        model = options.vendor_specific.get("model", self.model) if options and options.vendor_specific else self.model
        
        # Make the streaming API call
        stream = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        )
        
        async for chunk in stream:
            if hasattr(chunk, "text"):
                yield chunk.text

