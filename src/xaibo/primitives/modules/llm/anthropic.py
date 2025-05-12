import os
import logging
from typing import List, Optional, AsyncIterator, Dict, Any


from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMMessageContentType, LLMOptions, LLMResponse, LLMFunctionCall, LLMUsage, LLMRole

logger = logging.getLogger(__name__)


class AnthropicLLM(LLMProtocol):
    """Implementation of LLMProtocol for Anthropic API"""
    
    def __init__(
        self,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the Anthropic LLM client.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - api_key: Anthropic API key. If not provided, will try to get from ANTHROPIC_API_KEY env var.
                - model: The model to use for generation. Default is "claude-3-opus-20240229".
                - base_url: Base URL for the Anthropic API.
                - timeout: Timeout for API requests in seconds. Default is 60.0.
                - Any additional keys will be passed as arguments to the API.
        """
        from anthropic import AsyncAnthropic

        config = config or {}
        
        self.api_key = config.get('api_key') or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided or set as ANTHROPIC_API_KEY environment variable")
        
        self.model = config.get('model', "claude-3-opus-20240229")
        
        # Extract known configuration parameters
        base_url = config.get('base_url')
        timeout = config.get('timeout', 60.0)
        
        # Create client with core parameters
        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = AsyncAnthropic(**client_kwargs)
        
        # Store any additional parameters as default kwargs
        self.default_kwargs = {k: v for k, v in config.items() 
                              if k not in ['api_key', 'model', 'base_url', 'timeout']}
    
    def _prepare_messages(self, messages: List[LLMMessage]) -> tuple[list, Optional[str]]:
        """Convert our messages to Anthropic format and extract system message if present"""
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                # System messages are handled separately in Anthropic
                # Combine all text content entries
                system_texts = [c.text for c in msg.content if c.type == LLMMessageContentType.TEXT]
                system_message = " ".join(system_texts) if system_texts else None
                continue
                
            if msg.role == LLMRole.FUNCTION:
                if msg.tool_calls:
                    # This is the message that originally called for tool execution
                    message = {
                        "role": "assistant",
                        "content": []                        
                    }
                    if msg.content:
                        # Add all text content entries
                        for content in msg.content:
                            if content.type == LLMMessageContentType.TEXT:
                                message["content"].append({
                                    "type": "text",
                                    "text": content.text
                                })
                    for tool_call in msg.tool_calls:
                        message["content"].append({
                            "type": "tool_use",
                            "id": tool_call.id,
                            "name": tool_call.name,
                            "input": tool_call.arguments
                        })                        
                    anthropic_messages.append(message)
                elif msg.tool_results:
                    # This is the message that contains the tool execution results
                    message = {
                        "role": "user",
                        "content": []
                    }                                        
                    for result in msg.tool_results:
                        message["content"].append({
                            "type": "tool_result",
                            "tool_use_id": result.id,
                            "content": result.content
                        })
                    anthropic_messages.append(message)
                else:
                    # This is a malformed message
                    logger.warning("Malformed function message - missing both tool_calls and tool_results")
            else:
                # Handle text and image content
                message = {
                    "role": "assistant" if msg.role == LLMRole.ASSISTANT else "user",
                    "content": [
                        {"type": "text", "text": c.text} if c.type == LLMMessageContentType.TEXT
                        else self._prepare_image_content(c.image)
                        for c in msg.content
                    ],
                    **({"name": msg.name} if msg.name else {})
                }
                anthropic_messages.append(message)
        return anthropic_messages, system_message
    
    def _prepare_image_content(self, image_path: str) -> Dict[str, Any]:
        """Helper method to prepare image content for Anthropic API"""
        if image_path.startswith("data:"):
            # Handle base64 encoded images
            # Extract media type and data from data URL
            _, rest = image_path.split(":", 1)
            media_type, base64_data = rest.split(";base64,", 1)
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data
                }
            }
        else:
            # Handle URL images
            return {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_path
                }
            }
    
    def _prepare_tools(self, options: LLMOptions) -> Optional[List[Dict[str, Any]]]:
        """Prepare tool calling if needed"""
        if not options.functions:
            return None
            
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        param_name: {
                            "type": param.type,
                            "description": param.description + (f" Default: {param.default}" if param.default is not None else ""),
                            **({"enum": param.enum} if param.enum else {})
                        }
                        for param_name, param in tool.parameters.items()
                    },
                    "required": [
                        param_name for param_name, param in tool.parameters.items()
                        if param.required
                    ]
                }
            }
            for tool in options.functions
        ]
    
    def _prepare_request_kwargs(self, 
                               anthropic_messages: List[Dict[str, Any]], 
                               system_message: Optional[str], 
                               tools: Optional[List[Dict[str, Any]]], 
                               options: LLMOptions, 
                               stream: bool = False) -> Dict[str, Any]:
        """Prepare kwargs for the Anthropic API request"""
        kwargs = {
            "model": self.model,
            "messages": anthropic_messages,
            "temperature": options.temperature,
            "top_p": options.top_p,
            "max_tokens": options.max_tokens or 1024,
            **self.default_kwargs,
            **options.vendor_specific
        }
        
        # Add stream parameter if streaming
        if stream:
            kwargs["stream"] = True
            
        # Add system message if present
        if system_message:
            kwargs["system"] = system_message
            
        # Add tools if present
        if tools:
            kwargs["tools"] = tools
            
        # Add stop sequences if present
        if options.stop_sequences:
            kwargs["stop_sequences"] = options.stop_sequences
            
        return kwargs
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response from the Anthropic API"""
        options = options or LLMOptions()
        
        try:
            # Prepare request components
            anthropic_messages, system_message = self._prepare_messages(messages)
            tools = self._prepare_tools(options)
            kwargs = self._prepare_request_kwargs(anthropic_messages, system_message, tools, options)

            # Make the API call
            response = await self.client.messages.create(**kwargs)
            
            # Process the response - accumulate all text content
            content_parts = []
            function_call = None
            
            for content_item in response.content:
                if content_item.type == "text":
                    content_parts.append(content_item.text)
                elif content_item.type == "tool_use":
                    function_call = LLMFunctionCall(
                        id=content_item.id,
                        name=content_item.name,
                        arguments=content_item.input
                    )
            
            # Join all text parts
            content = "".join(content_parts)
            
            # Handle usage statistics
            usage = None
            if hasattr(response, 'usage'):
                usage = LLMUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
                )
            
            return LLMResponse(
                content=content,
                tool_calls=[function_call] if function_call else None,
                usage=usage,
                vendor_specific={"id": response.id, "model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Error generating response from Anthropic: {str(e)}")
            raise
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the Anthropic API"""
        options = options or LLMOptions()
        
        try:
            # Prepare request components
            anthropic_messages, system_message = self._prepare_messages(messages)
            tools = self._prepare_tools(options)
            kwargs = self._prepare_request_kwargs(anthropic_messages, system_message, tools, options)
            
            # Make the streaming API call
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:                
                    yield text
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from Anthropic: {str(e)}")
            raise
