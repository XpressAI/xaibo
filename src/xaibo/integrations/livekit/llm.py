import asyncio
import uuid
from typing import Any

from livekit.agents import llm
from livekit.agents.llm import (
    ChatChunk,
    ChatContext,
    ChoiceDelta,
    CompletionUsage,
    FunctionTool,
    RawFunctionTool,
)
from livekit.agents.types import APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr
from livekit.agents.llm.tool_context import ToolChoice

from xaibo import ConfigOverrides, ExchangeConfig
from xaibo.core.xaibo import Xaibo
from xaibo.core.models.response import Response
from xaibo.primitives.modules.conversation.conversation import SimpleConversation
from xaibo.core.models.llm import LLMMessage, LLMRole, LLMMessageContent, LLMMessageContentType

from .log import logger


class XaiboLLM(llm.LLM):
    """
    Xaibo LLM implementation that integrates with Xaibo's agent system.
    
    This class bridges LiveKit's LLM interface with Xaibo's agent-based
    conversational AI system, allowing Xaibo agents to be used as LLM
    providers in LiveKit applications.
    
    The implementation converts LiveKit's ChatContext directly to Xaibo's
    native LLMMessage format and injects it as conversation history via
    ConfigOverrides, enabling conversation-aware modules while still
    providing text-based processing for the last user message.
    """

    def __init__(
        self,
        *,
        xaibo: Xaibo,
        agent_id: str,
    ) -> None:
        """
        Initialize the Xaibo LLM.

        Args:
            xaibo: The Xaibo instance to use for agent management
            agent_id: The ID of the Xaibo agent to use for processing
        """
        super().__init__()
        self._xaibo = xaibo
        self._agent_id = agent_id

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: list[FunctionTool | RawFunctionTool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> 'XaiboLLMStream':
        """
        Create a chat stream for the given context.

        Args:
            chat_ctx: The chat context containing the conversation history
            tools: Function tools available for the agent (currently not used)
            conn_options: Connection options for the stream
            parallel_tool_calls: Whether to allow parallel tool calls (currently not used)
            tool_choice: Tool choice strategy (currently not used)
            extra_kwargs: Additional keyword arguments (currently not used)

        Returns:
            XaiboLLMStream: A stream for processing the chat
        """
        # Convert LiveKit ChatContext to Xaibo conversation
        conversation = self._convert_chat_context_to_conversation(chat_ctx)
        
        # Create agent with conversation history injected
        agent_with_conversation = self._xaibo.get_agent_with(
            self._agent_id,
            ConfigOverrides(
                instances={
                    '__conversation_history__': conversation
                },
                exchange=[ExchangeConfig(
                    protocol='ConversationHistoryProtocol',
                    provider='__conversation_history__'
                )]
            )
        )
        
        return XaiboLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            agent=agent_with_conversation,
        )

    def _convert_chat_context_to_conversation(self, chat_ctx: ChatContext) -> SimpleConversation:
        """
        Convert LiveKit ChatContext directly to Xaibo's SimpleConversation format.
        
        Args:
            chat_ctx: The LiveKit chat context
            
        Returns:
            SimpleConversation: Populated conversation instance
        """
        conversation = SimpleConversation()
        
        # Role mapping from LiveKit to Xaibo
        role_map = {
            "system": LLMRole.SYSTEM,
            "user": LLMRole.USER,
            "assistant": LLMRole.ASSISTANT,
            "developer": LLMRole.SYSTEM,  # Map developer to system
        }
        
        for item in chat_ctx.items:
            if item.type == "message":
                role = role_map.get(item.role, LLMRole.USER)
                content = item.text_content
                
                if content:
                    # Create LLMMessage with text content
                    message = LLMMessage(
                        role=role,
                        content=[LLMMessageContent(
                            type=LLMMessageContentType.TEXT,
                            text=content
                        )]
                    )
                    conversation._history.append(message)
                    
            elif item.type == "function_call":
                # Handle function calls as assistant messages with tool calls
                # For now, convert to text representation
                function_text = f"Function Call: {item.name}({item.arguments})"
                message = LLMMessage(
                    role=LLMRole.ASSISTANT,
                    content=[LLMMessageContent(
                        type=LLMMessageContentType.TEXT,
                        text=function_text
                    )]
                )
                conversation._history.append(message)
                
            elif item.type == "function_call_output":
                # Handle function outputs as function result messages
                output_text = f"Function Output: {item.output}"
                message = LLMMessage(
                    role=LLMRole.FUNCTION,
                    content=[LLMMessageContent(
                        type=LLMMessageContentType.TEXT,
                        text=output_text
                    )]
                )
                conversation._history.append(message)
        
        return conversation


class XaiboLLMStream(llm.LLMStream):
    """
    Xaibo LLM stream implementation that handles streaming responses from Xaibo agents.
    
    This class works with Xaibo agents that have conversation history injected via ConfigOverrides.
    It extracts the last user message for text-based processing while the agent can access
    the full conversation history through conversation-aware modules.
    """

    def __init__(
        self,
        llm: XaiboLLM,
        *,
        chat_ctx: ChatContext,
        tools: list[FunctionTool | RawFunctionTool],
        conn_options: APIConnectOptions,
        agent,
    ) -> None:
        """
        Initialize the Xaibo LLM stream.

        Args:
            llm: The parent XaiboLLM instance
            chat_ctx: The chat context to process
            tools: Available function tools
            conn_options: Connection options
            agent: The Xaibo agent instance that already has conversation history injected
        """
        super().__init__(llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._agent = agent
        self._request_id = str(uuid.uuid4())

    async def _run(self) -> None:
        """
        Main execution method that processes the chat context and streams responses.
        
        This method:
        1. Uses the agent that already has conversation history injected
        2. Extracts the last user message for text-based processing
        3. Sends the text to the Xaibo agent
        4. Processes the response and converts it to ChatChunk format
        5. Handles both streaming and non-streaming responses
        """
        try:
            # Extract the last user message for text-based processing
            # The agent already has full conversation history via ConfigOverrides
            text_input = self._convert_chat_context_to_text(self._chat_ctx)
            
            logger.debug(
                f"Sending text to Xaibo agent {self._agent.id}: {text_input[:100]}..."
            )

            # Send text to Xaibo agent and get response
            # The agent will use both the conversation history (for conversation-aware modules)
            # and the text input (for text-based processing)
            response: Response = await self._agent.handle_text(text_input)
            
            # Process the response
            await self._process_response(response)

        except Exception as e:
            logger.error(f"Error in XaiboLLMStream._run: {e}", exc_info=True)
            raise

    def _convert_chat_context_to_text(self, chat_ctx: ChatContext) -> str:
        """
        Convert LiveKit ChatContext to a text string, extracting the last user message.
        This is used as a fallback for agents that only handle text-based processing.
        
        Args:
            chat_ctx: The LiveKit chat context
            
        Returns:
            str: The last user message text, or empty string if none found
        """
        # Extract the last user message from the ChatContext
        last_user_message = ""
        
        for item in reversed(chat_ctx.items):
            if item.type == "message" and item.role == "user":
                content = item.text_content
                if content:
                    last_user_message = content
                    break
        
        return last_user_message

    async def _process_response(self, response: Response) -> None:
        """
        Process a Xaibo Response and convert it to LiveKit ChatChunk format.
        
        Args:
            response: The response from the Xaibo agent
        """
        if response.text:
            # Simulate streaming by breaking the response into words
            words = response.text.split()
            total_tokens = len(words)
            
            # Send chunks word by word to simulate streaming
            for i, word in enumerate(words):
                # Create a chat chunk with incremental content
                chunk = ChatChunk(
                    id=self._request_id,
                    delta=ChoiceDelta(
                        role="assistant" if i == 0 else None,  # Only set role on first chunk
                        content=word + (" " if i < len(words) - 1 else ""),
                        tool_calls=[],
                    ),
                )
                
                # Send the chunk through the event channel
                self._event_ch.send_nowait(chunk)
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
            
            logger.debug(f"Sent {len(words)} streaming chunks for response: {response.text[:100]}...")
            
            # Send final usage chunk
            usage_chunk = ChatChunk(
                id=self._request_id,
                delta=None,
                usage=CompletionUsage(
                    completion_tokens=total_tokens,
                    prompt_tokens=0,  # We don't have this info from Xaibo
                    total_tokens=total_tokens,
                ),
            )
            self._event_ch.send_nowait(usage_chunk)
        
        # Handle file attachments if present
        if response.attachments:
            logger.warning(
                f"Xaibo response contains {len(response.attachments)} attachments, "
                "but file attachments are not yet supported in LiveKit LLM integration"
            )
