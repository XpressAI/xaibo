from xaibo.core.protocols import TextMessageHandlerProtocol, ResponseProtocol, LLMProtocol, ToolProviderProtocol, \
    ConversationHistoryProtocol
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMRole, LLMFunctionResult, LLMMessageContentType, LLMMessageContent

import json

class StressingToolUser(TextMessageHandlerProtocol):
    """
    A text message handler that uses tools with increasing stress levels on failures.
    
    This handler processes user messages by leveraging an LLM to generate responses
    and potentially use tools. If tool execution fails, it increases the temperature
    (stress level) for subsequent LLM calls, simulating cognitive stress.
    """
    
    @classmethod
    def provides(cls):
        """
        Specifies which protocols this class implements.
        
        Returns:
            list: List of protocols provided by this class
        """
        return [TextMessageHandlerProtocol]

    def __init__(self,
                 response: ResponseProtocol,
                 llm: LLMProtocol,
                 tool_provider: ToolProviderProtocol,
                 history: ConversationHistoryProtocol,
                 config: dict = None):
        """
        Initialize the StressingToolUser.
        
        Args:
            response: Protocol for sending responses back to the user
            llm: Protocol for generating text using a language model
            tool_provider: Protocol for accessing and executing tools
            history: A conversation History for some context
            config: Configuration dictionary with optional parameters:
                   - system_prompt: Initial system prompt for the conversation
                   - max_thoughts: Maximum number of tool usage iterations
        """
        self.config: dict = config or {}
        self.system_prompt = self.config.get('system_prompt', '')
        self.max_thoughts = self.config.get('max_thoughts', 10)
        self.response: ResponseProtocol = response
        self.llm: LLMProtocol = llm
        self.tool_provider: ToolProviderProtocol = tool_provider
        self.history = history

    async def handle_text(self, text: str) -> None:
        """
        Process a user text message, potentially using tools to generate a response.
        
        This method:
        1. Initializes a conversation with the system prompt and user message
        2. Retrieves available tools from the tool provider
        3. Iteratively generates responses and executes tools as needed
        4. Increases stress level (temperature) if tool execution fails
        5. Sends the final response back to the user
        
        Args:
            text: The user's input text message
        """
        # Initialize conversation with system prompt
        conversation = [m for m in await self.history.get_history()]
        if self.system_prompt:
            conversation.insert(0, LLMMessage.system(self.system_prompt))
        
        # Add user message
        conversation.append(LLMMessage.user(text))
        
        # Get available tools
        tools = await self.tool_provider.list_tools()
        
        thoughts = 0
        stress_level = 0.0  # Raise temperature if there are failures
        
        while thoughts < self.max_thoughts:
            thoughts += 1
            
            # If max thoughts reached, disable tools
            if thoughts == self.max_thoughts:
                conversation.append(LLMMessage.system("Maximum tool usage reached. Tools Unavailable"))
            
            # Generate response with current stress level
            options = LLMOptions(
                temperature=stress_level,
                functions=tools if thoughts < self.max_thoughts else None
            )
            
            llm_response = await self.llm.generate(conversation, options)
            
            # Add assistant response to conversation
            assistant_message = LLMMessage(
                role=LLMRole.FUNCTION if llm_response.tool_calls else LLMRole.ASSISTANT,
                content=[LLMMessageContent(
                    type=LLMMessageContentType.TEXT,
                    text=llm_response.content
                )],
                tool_calls=llm_response.tool_calls
            )
            conversation.append(assistant_message)
            
            # Check if tool was called and we haven't reached max thoughts
            if thoughts < self.max_thoughts and llm_response.tool_calls and len(llm_response.tool_calls) > 0:
                # Execute all tools and collect results
                tool_results = []
                
                for tool_call in llm_response.tool_calls:
                    tool_name = tool_call.name
                    tool_args = tool_call.arguments
                    
                    try:
                        tool_result = await self.tool_provider.execute_tool(tool_name, tool_args)
                        
                        if tool_result.success:
                            tool_results.append({
                                "id": tool_call.id,
                                "name": tool_name,
                                "result": json.dumps(tool_result.result, default=repr)
                            })
                        else:
                            # Tool execution failed
                            tool_results.append({
                                "id": tool_call.id,
                                "name": tool_name,
                                "error": f"Error: {tool_result.error}"
                            })
                            stress_level += 0.1
                    except Exception as e:
                        # Handle any exceptions during tool execution
                        tool_results.append({
                            "id": tool_call.id,
                            "name": tool_name,
                            "error": f"Error: {str(e)}"
                        })
                        stress_level += 0.1

                conversation.append(LLMMessage(
                    role=LLMRole.FUNCTION,                        
                    tool_results=[
                        LLMFunctionResult(
                            id=tool_result.get("id"),
                            name=tool_result.get("name"),
                            content=tool_result.get("result", tool_result.get("error"))
                        ) for tool_result in tool_results
                    ]

                ))
                    
            else:
                # No tool call or max thoughts reached, end the conversation
                break
        
        # Send the final response
        await self.response.respond_text(conversation[-1].content[0].text)