import os
import json
import logging
from typing import List, Optional, AsyncIterator, Dict, Any

import base64

from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMMessageContentType, LLMOptions, LLMResponse, LLMFunctionCall, LLMUsage, LLMRole


logger = logging.getLogger(__name__)


class BedrockLLM(LLMProtocol):
    """Implementation of LLMProtocol for AWS Bedrock"""
    
    def __init__(
        self,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the AWS Bedrock LLM client.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - aws_access_key_id: AWS access key. If not provided, will use default credentials.
                - aws_secret_access_key: AWS secret key. If not provided, will use default credentials.
                - region_name: AWS region. Default is "us-east-1".
                - model: The model to use. Default is "anthropic.claude-v2".
                - timeout: Timeout for API requests in seconds. Default is 60.0.
                - Any additional keys will be passed as arguments to the API.
        """
        import boto3
        from botocore.config import Config

        config = config or {}
        
        # Configure AWS client
        aws_config = Config(
            region_name=config.get('region_name', 'us-east-1'),
            connect_timeout=config.get('timeout', 60.0),
            read_timeout=config.get('timeout', 60.0)
        )
        
        # Create Bedrock client
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key'),
            config=aws_config
        )
        
        self.model = config.get('model', 'anthropic.claude-v2')
        
        # Store any additional parameters as default kwargs
        self.default_kwargs = {k: v for k, v in config.items() 
                             if k not in ['aws_access_key_id', 'aws_secret_access_key', 
                                        'region_name', 'model', 'timeout']}

    def _prepare_messages(self, messages: List[LLMMessage], options: LLMOptions) -> tuple[List[Dict[str, Any]], Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
        """Prepare the messages, system prompt, and tool config for the Bedrock Converse API"""
        bedrock_messages = []
        system_content = None
        tool_config = None
        
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                system_content = [{"text": msg.content[0].text}]
                continue
                
            if msg.role == LLMRole.USER:
                content = []
                for part in msg.content:
                    if part.type == LLMMessageContentType.TEXT:
                        content.append({"text": part.text})
                    elif part.type == LLMMessageContentType.IMAGE:
                        # Handle different image source formats
                        if part.image.startswith("data:"):
                            # Handle base64 encoded images
                            _, rest = part.image.split(":", 1)
                            media_type, base64_data = rest.split(";base64,", 1)
                            # Decode base64 to bytes for the SDK
                            decoded_bytes = base64.b64decode(base64_data)
                            content.append({
                                "image": {
                                    "format": media_type.split("/")[1] if "/" in media_type else "jpeg",
                                    "source": {
                                        "bytes": decoded_bytes
                                    }
                                }
                            })
                        elif part.image.startswith(("http://", "https://")):
                            # Handle URL images
                            content.append({
                                "image": {
                                    "format": "jpeg",
                                    "source": {
                                        "url": part.image
                                    }
                                }
                            })
                        else:
                            # Assume it's a file path or already base64 encoded
                            content.append({
                                "image": {
                                    "format": "jpeg",
                                    "source": {
                                        "bytes": part.image
                                    }
                                }
                            })

                bedrock_messages.append({
                    "role": "user",
                    "content": content
                })
                
            elif msg.role == LLMRole.ASSISTANT:
                content = []
                for part in msg.content:
                    if part.type == LLMMessageContentType.TEXT:
                        content.append({"text": part.text})                            
                
                bedrock_messages.append({
                    "role": "assistant",
                    "content": content
                })
                
            elif msg.role == LLMRole.FUNCTION:
                if msg.tool_results:
                    content = []
                    for result in msg.tool_results:
                        content.append({
                            "toolResult": {
                                "toolUseId": result.id,
                                "content": [{"text": result.content}],
                                "status": "success"
                            }
                        })
                    bedrock_messages.append({
                        "role": "user",
                        "content": content
                    })
                elif msg.tool_calls:
                    content = []
                    # Handle function calls in function role messages
                    for tool_call in msg.tool_calls:
                        content.append({
                            "toolUse": {
                                "toolUseId": tool_call.id,
                                "name": tool_call.name,
                                "input": tool_call.arguments
                            }
                        })
                    bedrock_messages.append({
                        "role": "assistant",
                        "content": content
                    })
        
        # Prepare tools if provided
        if options.functions:
            tools = []
            for function in options.functions:
                tool = {
                    "toolSpec": {
                        "name": function.name,
                        "description": function.description,
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                }
                
                for param_name, param in function.parameters.items():
                    tool["toolSpec"]["inputSchema"]["json"]["properties"][param_name] = {
                        "type": param.type,
                        "description": param.description
                    }
                    if param.required:
                        tool["toolSpec"]["inputSchema"]["json"]["required"].append(param_name)
                
                tools.append(tool)
            
            tool_config = {
                "tools": tools,
                "toolChoice": {"auto": {}}
            }
        
        return bedrock_messages, system_content, tool_config
    def _extract_content(self, response_body: Dict[str, Any]) -> str:
        if "output" in response_body and "message" in response_body["output"]:
            content_items = response_body["output"]["message"].get("content", [])
            text_content = ""
            for item in content_items:
                if "text" in item:
                    text_content += item.get("text", "")
            return text_content
        return ""
    
    def _extract_streaming_content(self, chunk: Dict[str, Any]) -> Optional[str]:
        if "contentBlockDelta" in chunk and "delta" in chunk["contentBlockDelta"]:
            delta = chunk["contentBlockDelta"]["delta"]
            if "text" in delta:
                return delta["text"]
        return None
    
    def _extract_tool_calls(self, response_body: Dict[str, Any]) -> Optional[List[LLMFunctionCall]]:
        if "output" in response_body and "message" in response_body["output"]:
            content_items = response_body["output"]["message"].get("content", [])
            tool_calls = []
            for item in content_items:
                if "toolUse" in item:
                    tool_use = item["toolUse"]
                    tool_calls.append(
                        LLMFunctionCall(
                            id=tool_use.get("toolUseId", ""),
                            name=tool_use.get("name", ""),
                            arguments=tool_use.get("input", {})
                        )
                    )
            return tool_calls if tool_calls else None
        return None

    def _prepare_converse_request(self, 
                                messages: List[LLMMessage], 
                                options: LLMOptions, 
                                stream: bool = False) -> Dict[str, Any]:
        """Prepare the request for the Bedrock Converse API"""
        # Get messages, system prompt, and tool config from the handler
        bedrock_messages, system_content, tool_config = self._prepare_messages(messages, options)
        
        # Build inference config
        inference_config = {
            "maxTokens": options.max_tokens or 2048,
            "temperature": options.temperature or 0.7,
            "topP": options.top_p or 1.0,
        }
        
        if options.stop_sequences:
            inference_config["stopSequences"] = options.stop_sequences
        
        # Build the request
        request = {
            "modelId": self.model,
            "messages": bedrock_messages,
            "inferenceConfig": inference_config,
            **self.default_kwargs
        }
        
        # Add system prompt if provided
        if system_content:
            request["system"] = system_content
            
        # Add tool config if provided
        if tool_config:
            request["toolConfig"] = tool_config
            
        # Add vendor specific parameters
        if options.vendor_specific:
            request["additionalModelRequestFields"] = options.vendor_specific
            
        return request

    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response from AWS Bedrock using the Converse API"""
        options = options or LLMOptions()
        
        try:
            # Prepare request
            request = self._prepare_converse_request(messages, options)
            
            # Make the API call
            response = self.client.converse(**request)
            
            # Extract content
            content = self._extract_content(response)
            
            # Extract tool calls if any
            tool_calls = self._extract_tool_calls(response)
            
            # Extract usage information
            usage = None
            if 'usage' in response:
                usage = LLMUsage(
                    prompt_tokens=response['usage'].get('inputTokens', 0),
                    completion_tokens=response['usage'].get('outputTokens', 0),
                    total_tokens=response['usage'].get('totalTokens', 0)
                )
            
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
                vendor_specific={"raw_response": response}
            )
            
        except Exception as e:
            logger.error(f"Error generating response from Bedrock: {str(e)}")
            raise

    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from AWS Bedrock using the Converse API"""
        options = options or LLMOptions()
        
        try:
            # Prepare request
            request = self._prepare_converse_request(messages, options)
            
            # Make the streaming API call
            response = self.client.converse_stream(**request)
            
            # Process streaming response
            for event in response['stream']:
                content = self._extract_streaming_content(event)
                if content:
                    yield content
                    
        except Exception as e:
            logger.error(f"Error generating streaming response from Bedrock: {str(e)}")
            raise
