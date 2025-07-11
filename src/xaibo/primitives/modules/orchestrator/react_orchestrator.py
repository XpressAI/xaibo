from xaibo.core.protocols import TextMessageHandlerProtocol, ResponseProtocol, LLMProtocol, ToolProviderProtocol, \
    ConversationHistoryProtocol
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMRole, LLMFunctionResult, LLMMessageContentType, LLMMessageContent, LLMFunctionCall
from xaibo.core.models.tools import Tool

import json
from enum import Enum
from typing import List, Dict, Any, Optional


class ReActPhase(str, Enum):
    """Phases of the ReAct cycle"""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"


class ReActOrchestrator(TextMessageHandlerProtocol):
    """
    A ReAct (Reasoning and Acting) orchestrator that follows explicit Thought-Action-Observation cycles.
    
    This orchestrator implements the ReAct pattern where the LLM:
    1. THOUGHT: Reasons about what to do next
    2. ACTION: Executes a tool or provides a final answer
    3. OBSERVATION: Processes the results and decides next steps
    
    The process continues until a final answer is reached or max iterations are hit.
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
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ReActOrchestrator.
        
        Args:
            response: Protocol for sending responses back to the user
            llm: Protocol for generating text using a language model
            tool_provider: Protocol for accessing and executing tools
            history: A conversation History for some context
            config: Configuration dictionary with optional parameters:
                   - system_prompt: Base system prompt for ReAct behavior
                   - thought_prompt: Prompt for generating thoughts about next steps
                   - action_prompt: Prompt for taking actions (tools or final answer)
                   - observation_prompt: Prompt for processing tool results and observations
                   - error_prompt: Prompt template for handling errors (use {error} placeholder)
                   - max_iterations_prompt: Prompt template for max iterations (use {max_iterations} placeholder)
                   - max_iterations: Maximum number of Thought-Action-Observation cycles
                   - show_reasoning: Whether to show intermediate reasoning steps to users
                   - reasoning_temperature: Temperature setting for reasoning generation
        """
        self.config: Dict[str, Any] = config or {}
        self.system_prompt: str = self.config.get('system_prompt', self._get_default_system_prompt())
        self.thought_prompt: str = self.config.get('thought_prompt',
            "Generate your THOUGHT about what to do next. Consider the user's request and what information or actions you need.")
        self.action_prompt: str = self.config.get('action_prompt',
            """Now take ACTION based on your thought. You have two options:
1. Call a tool if you need more information or capabilities
2. Provide FINAL_ANSWER: [your complete answer] if you have sufficient information

Choose the appropriate action.""")
        self.observation_prompt: str = self.config.get('observation_prompt',
            """Analyze the OBSERVATION from the tool results. What did you learn?
Do you have enough information to provide a final answer, or do you need to take more actions?
Provide your OBSERVATION and reasoning.""")
        self.error_prompt: str = self.config.get('error_prompt',
            """An error occurred: {error}

Please provide a FINAL_ANSWER based on the information you have gathered so far,
or explain what went wrong and what you were trying to accomplish.""")
        self.max_iterations_prompt: str = self.config.get('max_iterations_prompt',
            """You have reached the maximum number of iterations ({max_iterations}).
Please provide a FINAL_ANSWER based on the information and reasoning you have gathered so far.""")
        self.max_iterations: int = self.config.get('max_iterations', 10)
        self.show_reasoning: bool = self.config.get('show_reasoning', True)
        self.reasoning_temperature: float = self.config.get('reasoning_temperature', 0.7)
        
        self.response: ResponseProtocol = response
        self.llm: LLMProtocol = llm
        self.tool_provider: ToolProviderProtocol = tool_provider
        self.history = history
        
        # State tracking
        self.current_phase = ReActPhase.THOUGHT
        self.iteration_count = 0

    def _get_default_system_prompt(self) -> str:
        """
        Get the default system prompt for ReAct behavior.
        
        Returns:
            str: Default system prompt that guides ReAct pattern
        """
        return """You are an AI assistant that follows the ReAct (Reasoning and Acting) pattern. You must think step by step and follow this exact format:

THOUGHT: [Your reasoning about what to do next, what information you need, or what action to take]

ACTION: [Either call a tool with specific parameters, or provide FINAL_ANSWER if you have enough information]

OBSERVATION: [After receiving tool results, analyze what you learned and decide next steps]

Rules:
1. Always start with THOUGHT to reason about the situation
2. Use ACTION to either call tools or provide FINAL_ANSWER
3. After tool execution, use OBSERVATION to analyze results
4. Continue the cycle until you can provide a FINAL_ANSWER
5. Be explicit about your reasoning process
6. If you need to use multiple tools, do them one at a time
7. When you have sufficient information, use ACTION: FINAL_ANSWER: [your complete answer]

Available tools will be provided to you. Use them when you need additional information or capabilities."""

    async def handle_text(self, text: str) -> None:
        """
        Process a user text message using the ReAct pattern.
        
        This method implements the complete ReAct cycle:
        1. Initialize conversation with system prompt and user message
        2. Enter Thought-Action-Observation loop
        3. Generate thoughts about next steps
        4. Execute actions (tools or final answer)
        5. Process observations from tool results
        6. Continue until final answer or max iterations
        
        Args:
            text: The user's input text message
        """
        # Initialize conversation with system prompt and history
        conversation = [m for m in await self.history.get_history()]
        if self.system_prompt:
            conversation.insert(0, LLMMessage.system(self.system_prompt))
        
        # Add user message
        conversation.append(LLMMessage.user(text))
        
        # Get available tools
        tools = await self.tool_provider.list_tools()
        
        # Reset state for new conversation
        self.current_phase = ReActPhase.THOUGHT
        self.iteration_count = 0
        
        # Main ReAct loop
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            
            try:
                if self.current_phase == ReActPhase.THOUGHT:
                    await self._generate_thought(conversation, tools)
                elif self.current_phase == ReActPhase.ACTION:
                    final_answer = await self._execute_action(conversation, tools)
                    if final_answer:
                        # Final answer reached, exit loop
                        break
                elif self.current_phase == ReActPhase.OBSERVATION:
                    await self._process_observation(conversation, tools)
                    
            except Exception as e:
                # Handle errors with reasoning-based recovery
                await self._handle_error(conversation, str(e))
                break
        
        # If we've reached max iterations without a final answer
        if self.iteration_count >= self.max_iterations:
            await self._handle_max_iterations(conversation)
        
        # Send the final response
        final_message = conversation[-1]
        if final_message.content and len(final_message.content) > 0 and final_message.content[0].text:
            await self.response.respond_text(final_message.content[0].text)

    async def _generate_thought(self, conversation: List[LLMMessage], tools: List[Tool]) -> None:
        """
        Generate reasoning about next steps (THOUGHT phase).
        
        Args:
            conversation: Current conversation history
            tools: Available tools
        """
        # Use configurable thought prompt
        thought_prompt = self.thought_prompt
        
        if self.show_reasoning:
            await self.response.respond_text("🤔 **THINKING...**")
        
        # Generate thought with reasoning temperature
        options = LLMOptions(
            temperature=self.reasoning_temperature,
            functions=None  # No tools during thought phase
        )
        
        conversation.append(LLMMessage.system(thought_prompt))
        llm_response = await self.llm.generate(conversation, options)
        
        # Add thought to conversation
        thought_message = LLMMessage.assistant(llm_response.content)
        conversation.append(thought_message)
        
        if self.show_reasoning:
            await self.response.respond_text(f"💭 **THOUGHT:** {llm_response.content}")
        
        # Move to action phase
        self.current_phase = ReActPhase.ACTION

    async def _execute_action(self, conversation: List[LLMMessage], tools: List[Tool]) -> bool:
        """
        Execute actions based on reasoning (ACTION phase).
        
        Args:
            conversation: Current conversation history
            tools: Available tools
            
        Returns:
            bool: True if final answer was provided, False if tool was executed
        """
        # Use configurable action prompt
        action_prompt = self.action_prompt
        
        if self.show_reasoning:
            await self.response.respond_text("⚡ **TAKING ACTION...**")
        
        # Generate action with tools available
        options = LLMOptions(
            temperature=0.3,  # Lower temperature for more focused actions
            functions=tools
        )
        
        conversation.append(LLMMessage.system(action_prompt))
        llm_response = await self.llm.generate(conversation, options)
        
        # Check if this is a final answer
        if "FINAL_ANSWER:" in llm_response.content.upper():
            # Extract final answer
            final_answer = llm_response.content
            if self.show_reasoning:
                await self.response.respond_text(f"✅ **FINAL ANSWER:** {final_answer}")
            
            # Add final answer to conversation
            conversation.append(LLMMessage.assistant(final_answer))
            return True
        
        # Add action message to conversation
        action_message = LLMMessage(
            role=LLMRole.FUNCTION if llm_response.tool_calls else LLMRole.ASSISTANT,
            content=[LLMMessageContent(
                type=LLMMessageContentType.TEXT,
                text=llm_response.content
            )],
            tool_calls=llm_response.tool_calls
        )
        conversation.append(action_message)
        
        if self.show_reasoning:
            await self.response.respond_text(f"🔧 **ACTION:** {llm_response.content}")
        
        # Execute tools if any were called
        if llm_response.tool_calls and len(llm_response.tool_calls) > 0:
            await self._execute_tools(conversation, llm_response.tool_calls)
            # Move to observation phase
            self.current_phase = ReActPhase.OBSERVATION
        else:
            # No tools called, continue thinking
            self.current_phase = ReActPhase.THOUGHT
        
        return False

    async def _execute_tools(self, conversation: List[LLMMessage], tool_calls: List[LLMFunctionCall]) -> None:
        """
        Execute the requested tools and add results to conversation.
        
        Args:
            conversation: Current conversation history
            tool_calls: List of tool calls to execute
        """
        tool_results: List[Dict[str, Any]] = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.name
            tool_args = tool_call.arguments
            
            if self.show_reasoning:
                await self.response.respond_text(f"🛠️ **EXECUTING TOOL:** {tool_name} with args: {json.dumps(tool_args, indent=2)}")
            
            try:
                tool_result = await self.tool_provider.execute_tool(tool_name, tool_args)
                
                if tool_result.success:
                    result_content = json.dumps(tool_result.result, default=repr)
                    tool_results.append({
                        "id": tool_call.id,
                        "name": tool_name,
                        "result": result_content
                    })
                    
                    if self.show_reasoning:
                        await self.response.respond_text(f"✅ **TOOL SUCCESS:** {tool_name} returned: {result_content[:200]}...")
                else:
                    error_content = f"Error: {tool_result.error}"
                    tool_results.append({
                        "id": tool_call.id,
                        "name": tool_name,
                        "error": error_content
                    })
                    
                    if self.show_reasoning:
                        await self.response.respond_text(f"❌ **TOOL ERROR:** {tool_name} failed: {error_content}")
                        
            except Exception as e:
                error_content = f"Exception: {str(e)}"
                tool_results.append({
                    "id": tool_call.id,
                    "name": tool_name,
                    "error": error_content
                })
                
                if self.show_reasoning:
                    await self.response.respond_text(f"💥 **TOOL EXCEPTION:** {tool_name} threw: {error_content}")
        
        # Add tool results to conversation
        conversation.append(LLMMessage(
            role=LLMRole.FUNCTION,
            tool_results=[
                LLMFunctionResult(
                    id=tool_result.get("id", ""),
                    name=tool_result.get("name", ""),
                    content=tool_result.get("result", tool_result.get("error", ""))
                ) for tool_result in tool_results
            ]
        ))

    async def _process_observation(self, conversation: List[LLMMessage], tools: List[Tool]) -> None:
        """
        Process tool results and decide next steps (OBSERVATION phase).
        
        Args:
            conversation: Current conversation history
            tools: Available tools
        """
        # Use configurable observation prompt
        observation_prompt = self.observation_prompt
        
        if self.show_reasoning:
            await self.response.respond_text("👁️ **OBSERVING RESULTS...**")
        
        # Generate observation with reasoning temperature
        options = LLMOptions(
            temperature=self.reasoning_temperature,
            functions=None  # No tools during observation phase
        )
        
        conversation.append(LLMMessage.system(observation_prompt))
        llm_response = await self.llm.generate(conversation, options)
        
        # Add observation to conversation
        observation_message = LLMMessage.assistant(llm_response.content)
        conversation.append(observation_message)
        
        if self.show_reasoning:
            await self.response.respond_text(f"🔍 **OBSERVATION:** {llm_response.content}")
        
        # Move back to thought phase for next iteration
        self.current_phase = ReActPhase.THOUGHT

    async def _handle_error(self, conversation: List[LLMMessage], error: str) -> None:
        """
        Handle errors with reasoning-based recovery.
        
        Args:
            conversation: Current conversation history
            error: Error message
        """
        error_prompt = self.error_prompt.format(error=error)
        
        if self.show_reasoning:
            await self.response.respond_text(f"⚠️ **ERROR OCCURRED:** {error}")
        
        options = LLMOptions(temperature=0.3, functions=None)
        conversation.append(LLMMessage.system(error_prompt))
        llm_response = await self.llm.generate(conversation, options)
        
        # Add error recovery response
        conversation.append(LLMMessage.assistant(llm_response.content))

    async def _handle_max_iterations(self, conversation: List[LLMMessage]) -> None:
        """
        Handle reaching maximum iterations without a final answer.
        
        Args:
            conversation: Current conversation history
        """
        max_iterations_prompt = self.max_iterations_prompt.format(max_iterations=self.max_iterations)
        
        if self.show_reasoning:
            await self.response.respond_text(f"⏰ **MAX ITERATIONS REACHED:** Providing best answer with available information...")
        
        options = LLMOptions(temperature=0.3, functions=None)
        conversation.append(LLMMessage.system(max_iterations_prompt))
        llm_response = await self.llm.generate(conversation, options)
        
        # Add final response
        conversation.append(LLMMessage.assistant(llm_response.content))