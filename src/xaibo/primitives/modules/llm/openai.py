import os
import json
import logging
from typing import List, Optional, AsyncIterator, Dict, Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMMessageContentType, LLMOptions, LLMResponse, LLMFunctionCall, LLMUsage, LLMRole


logger = logging.getLogger(__name__)


class OpenAILLM(LLMProtocol):
    """Implementation of LLMProtocol for OpenAI API"""
    
    def __init__(
        self,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the OpenAI LLM client.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - api_key: OpenAI API key. If not provided, will try to get from OPENAI_API_KEY env var.
                - model: The model to use for generation. Default is "gpt-4.1-nano".
                - base_url: Base URL for the OpenAI API. Default is "https://api.openai.com/v1".
                - timeout: Timeout for API requests in seconds. Default is 60.0.
                - Any additional keys will be passed as arguments to the API.
        """
        config = config or {}
        
        self.api_key = config.get('api_key') or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.model = config.get('model', "gpt-4.1-nano")
        
        # Extract known configuration parameters
        base_url = config.get('base_url', "https://api.openai.com/v1")
        timeout = config.get('timeout', 60.0)
        
        # Create client with core parameters
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=timeout
        )
        
        # Store any additional parameters as default kwargs
        self.default_kwargs = {k: v for k, v in config.items() 
                              if k not in ['api_key', 'model', 'base_url', 'timeout']}
    
    def _prepare_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert our messages to OpenAI format"""
        prepared_messages = []
        
        for msg in messages:
            if msg.role == LLMRole.FUNCTION:
                if msg.tool_calls:
                    # This is the message that originally called for tool execution
                    message = {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.name,
                                    "arguments": json.dumps(tool_call.arguments)
                                }
                            }
                            for tool_call in msg.tool_calls
                        ]
                    }
                    prepared_messages.append(message)
                elif msg.tool_results:
                    # This is the message that contains the tool execution results
                    for result in msg.tool_results:
                        message = {
                            "role": "tool",
                            "tool_call_id": result.id,
                            "content": result.content
                        }
                        prepared_messages.append(message)
                else:
                    # This is a malformed message
                    logger.warning("Malformed function message - missing both tool_calls and tool_results")
            else:
                # Handle text and image content
                content = None
                if len(msg.content) == 1 and msg.content[0].type == LLMMessageContentType.TEXT:
                    content = msg.content[0].text
                else:
                    content = [
                        {"type": "text", "text": c.text} if c.type == LLMMessageContentType.TEXT
                        else {"type": "image_url", "image_url": {"url": c.image}}
                        for c in msg.content
                    ]

                message = {
                    "role": msg.role.value,
                    "content": content,
                    **({"name": msg.name} if msg.name else {})
                }
                
                prepared_messages.append(message)
            
        return prepared_messages
    def _prepare_functions(self, options: LLMOptions) -> Optional[List[Dict[str, Any]]]:
        """Prepare function calling if needed"""
        if not options.functions:
            return None
            
        # Map Python types to JSON Schema types
        def map_type_to_json_schema(python_type: str) -> str:
            type_mapping = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
                "None": "null",
                # Add any other type mappings as needed
            }
            return type_mapping.get(python_type, python_type)
            
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            param_name: {
                                "type": map_type_to_json_schema(param.type),
                                "description": (param.description or "") + (f" Default: {param.default}" if param.default is not None else ""),
                                **({} if param.enum is None else {"enum": param.enum})
                            }
                            for param_name, param in tool.parameters.items()
                        },
                        "required": [
                            param_name for param_name, param in tool.parameters.items()
                            if param.required
                        ]
                    }
                }
            }
            for tool in options.functions
        ]

    def _prepare_request_kwargs(self, 
                               openai_messages: List[Dict[str, Any]], 
                               functions: Optional[List[Dict[str, Any]]], 
                               options: LLMOptions, 
                               stream: bool = False) -> Dict[str, Any]:
        """Prepare kwargs for the OpenAI API request"""
        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": options.temperature,
            "top_p": options.top_p,
            "max_tokens": options.max_tokens,
            "stop": options.stop_sequences,
            "tools": functions,
            **self.default_kwargs,
            **options.vendor_specific
        }
        
        
        # Add stream parameter if streaming
        if stream:
            kwargs["stream"] = True

        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        return kwargs
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response from the OpenAI API"""
        options = options or LLMOptions()
        
        try:
            # Prepare request components
            openai_messages = self._prepare_messages(messages)
            functions = self._prepare_functions(options)
            kwargs = self._prepare_request_kwargs(openai_messages, functions, options)

            # Make the API call
            response: ChatCompletion = await self.client.chat.completions.create(**kwargs)
            
            # Process the response
            message = response.choices[0].message
            
            # Handle tool calls
            tool_calls = None
            if message.tool_calls and len(message.tool_calls) > 0:
                tool_calls = [
                    LLMFunctionCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                    )
                    for tool_call in message.tool_calls
                ]

            # Handle usage statistics
            usage = None
            if response.usage:
                usage = LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens
                )
            
            return LLMResponse(
                content=message.content or "",
                tool_calls=tool_calls,
                usage=usage,
                vendor_specific={"id": response.id, "model": response.model}
            )
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            raise
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the OpenAI API"""
        options = options or LLMOptions()
        
        try:
            # Prepare request components
            openai_messages = self._prepare_messages(messages)
            functions = self._prepare_functions(options)
            kwargs = self._prepare_request_kwargs(openai_messages, functions, options, stream=True)
            
            # Make the streaming API call
            stream = await self.client.chat.completions.create(**kwargs)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from OpenAI: {str(e)}")
            raise
