import json
import logging
import uuid
from typing import AsyncIterator, List, Optional

from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMResponse, LLMFunctionCall, LLMRole, LLMMessageContent, \
    LLMMessageContentType
from xaibo.core.models.tools import Tool

logger = logging.getLogger(__name__)

class TextBasedToolCallAdapter(LLMProtocol):
    """
    A wrapper for LLM modules that transforms input/output to enable tool usage
    for LLMs that don't natively support function calling capabilities.
    """

    def __init__(self, llm: LLMProtocol, config: dict = None):
        """
        Initialize the adapter with an LLM that follows the LLMProtocol.
        
        Args:
            llm: The LLM to wrap
        """
        self.llm = llm
    
    def _make_tools_prompt(self, tools: List[Tool]) -> str:
        """
        Create a prompt describing the available tools.
        
        Args:
            tools: List of tools to include in the prompt
            
        Returns:
            A formatted string describing the tools
        """
        prompt = "Available tools:\n\n"
        
        for tool in tools:
            prompt += f"{tool.name}: {tool.description}\n"
            
            # Add parameter details if available
            if tool.parameters:
                prompt += "Parameters:\n"
                for param_name, param in tool.parameters.items():
                    required = " (required)" if param.required else ""
                    prompt += f"  - {param_name}{required}: {param.description}\n"
                prompt += "\n"
        
        prompt += ("\nTo use a tool, write TOOL: followed by the tool name and JSON arguments on a single line. "
                   "Whenever you say 'I will now...' , you must follow that up with the appropriate TOOL: invocation.\n")
        prompt += "Example: TOOL: get_weather {\"location\": \"San Francisco, CA\"}\n"
        
        return prompt
    
    def _extract_tool_call(self, content: str) -> Optional[LLMFunctionCall]:
        """
        Extract a tool call from the LLM's response if present.
        
        Args:
            content: The content to parse for tool calls
            
        Returns:
            A LLMFunctionCall object if a tool call was found, None otherwise
        """
        lines = content.split("\n")
        
        for line in lines:
            if line.startswith("TOOL:"):
                # Extract the tool call
                command = line.split(":", 1)[1].strip()
                
                try:
                    # Parse tool name and arguments
                    parts = command.split(" ", 1)
                    tool_name = parts[0].strip()
                    
                    # Parse arguments if provided
                    arguments = {}
                    if len(parts) > 1:
                        args_text = parts[1].strip()
                        try:
                            arguments = json.loads(args_text)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse tool arguments as JSON: {args_text}")
                            # Use the raw text as a fallback
                            arguments = {"raw_input": args_text}
                    
                    return LLMFunctionCall(id=uuid.uuid4().hex, name=tool_name, arguments=arguments)
                except Exception as e:
                    logger.error(f"Error extracting tool call: {str(e)}")
                    return None
        
        return None
    
    def _modify_messages_with_tools(self, messages: List[LLMMessage], tools: List[Tool]) -> List[LLMMessage]:
        """
        Modify the messages to include tool descriptions in the system message.
        
        Args:
            messages: The original messages
            tools: The tools to include
            
        Returns:
            Modified messages with tool descriptions
        """
        if not tools:
            return messages.copy()
        
        tools_prompt = self._make_tools_prompt(tools)
        modified_messages = []
        
        # Find system message if it exists
        system_message_found = False
        for message in messages:
            if message.role == LLMRole.SYSTEM:
                # Append tools prompt to existing system message
                modified_messages.append(
                    LLMMessage(role=LLMRole.SYSTEM, content=message.content + [LLMMessageContent(type=LLMMessageContentType.TEXT, text=tools_prompt)], name=message.name)
                )
                system_message_found = True
            else:
                modified_messages.append(message)
        
        # Add a new system message if none exists
        if not system_message_found:
            modified_messages.insert(0, LLMMessage.system(tools_prompt))
        
        return modified_messages
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM with tool calling support.
        
        Args:
            messages: The messages to send to the LLM
            options: Options for the LLM
            
        Returns:
            A response with tool calling information if detected
        """
        options = options or LLMOptions()
        tools = options.functions or []
        
        # Modify messages to include tool descriptions
        modified_messages = self._modify_messages_with_tools(messages, tools)
        
        # Create a new options object without functions to avoid duplication
        clean_options = LLMOptions(
            temperature=options.temperature,
            top_p=options.top_p,
            max_tokens=options.max_tokens,
            vendor_specific=options.vendor_specific
        )
        
        # Generate response from the wrapped LLM
        response = await self.llm.generate(modified_messages, clean_options)
        
        # Extract tool call if present
        if tools and response.content:
            function_call = self._extract_tool_call(response.content)
            if function_call:
                # Clean up the response content by removing the tool call line
                lines = response.content.split("\n")
                cleaned_lines = [line for line in lines if not line.startswith("TOOL:")]
                cleaned_content = "\n".join(cleaned_lines).strip()
                
                return LLMResponse(
                    content=cleaned_content,
                    tool_calls=[function_call],
                    usage=response.usage,
                    vendor_specific=response.vendor_specific
                )
        
        return response
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.
        Note: Tool calling detection is not supported in streaming mode.
        
        Args:
            messages: The messages to send to the LLM
            options: Options for the LLM
            
        Returns:
            An async iterator of response chunks
        """
        options = options or LLMOptions()
        tools = options.functions or []
        
        # Modify messages to include tool descriptions
        modified_messages = self._modify_messages_with_tools(messages, tools)
        
        # Create a new options object without functions to avoid duplication
        clean_options = LLMOptions(
            temperature=options.temperature,
            top_p=options.top_p,
            max_tokens=options.max_tokens,
            vendor_specific=options.vendor_specific
        )
        
        # Stream response from the wrapped LLM
        async for chunk in self.llm.generate_stream(modified_messages, clean_options):
            yield chunk
