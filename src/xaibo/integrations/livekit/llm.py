import asyncio
import uuid
from typing import Any
from asyncio import Queue, create_task, wait_for, TimeoutError

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
        
        return XaiboLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            xaibo=self._xaibo,
            agent_id=self._agent_id,
            conversation=conversation,
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
        xaibo: Xaibo,
        agent_id: str,
        conversation: SimpleConversation,
    ) -> None:
        """
        Initialize the Xaibo LLM stream.

        Args:
            llm: The parent XaiboLLM instance
            chat_ctx: The chat context to process
            tools: Available function tools
            conn_options: Connection options
            xaibo: The Xaibo instance
            agent_id: The agent ID to use
            conversation: The conversation history
        """
        super().__init__(llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._xaibo = xaibo
        self._agent_id = agent_id
        self._conversation = conversation
        self._request_id = str(uuid.uuid4())
        self._streaming_timeout = 10.0  # Timeout for waiting for chunks

    async def _run(self) -> None:
        """
        Main execution method that processes the chat context and streams responses.
        
        This method:
        1. Creates a streaming response handler with a queue
        2. Creates the agent with both conversation history and streaming handler
        3. Runs the agent in a background task
        4. Streams chunks from the queue as they become available
        5. Converts chunks to LiveKit ChatChunk format in real-time
        """
        try:
            # Extract the last user message for text-based processing
            text_input = self._convert_chat_context_to_text(self._chat_ctx)
            
            logger.debug(
                f"Sending text to Xaibo agent {self._agent_id}: {text_input[:100]}..."
            )

            # Create streaming queue and response handler
            chunk_queue = Queue()
            streaming_response = self._create_streaming_response_handler(chunk_queue)
            
            # Create agent with both conversation history and streaming response handler
            agent = self._xaibo.get_agent_with(
                self._agent_id,
                ConfigOverrides(
                    instances={
                        '__conversation_history__': self._conversation,
                        '__response__': streaming_response
                    },
                    exchange=[
                        ExchangeConfig(
                            protocol='ConversationHistoryProtocol',
                            provider='__conversation_history__'
                        )
                    ]
                )
            )
            
            # Start agent processing in background task
            agent_task = create_task(agent.handle_text(text_input))
            
            # Send initial empty chunk to establish the stream
            initial_chunk = ChatChunk(
                id=self._request_id,
                delta=ChoiceDelta(
                    role="assistant",
                    content="",
                    tool_calls=[],
                ),
            )
            self._event_ch.send_nowait(initial_chunk)
            
            # Stream chunks as they become available
            await self._stream_chunks_from_queue(chunk_queue, agent_task)

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

    def _create_streaming_response_handler(self, chunk_queue: Queue):
        """
        Create a streaming response handler that puts chunks into a queue.
        
        Args:
            chunk_queue: The queue to put streaming chunks into
            
        Returns:
            StreamingResponse: A response handler that streams to the queue
        """
        class StreamingResponse:
            async def respond_text(self, text: str) -> None:
                """Handle streaming text chunks from the agent"""
                await chunk_queue.put(text)

            async def get_response(self):
                """Return None as we handle streaming via respond_text"""
                return None

        return StreamingResponse()
    
    async def _stream_chunks_from_queue(self, chunk_queue: Queue, agent_task) -> None:
        """
        Stream chunks from the queue as they become available.
        
        Args:
            chunk_queue: The queue containing streaming text chunks
            agent_task: The background task running the agent
        """
        total_content = ""
        
        while True:
            try:
                # Check if agent task is done
                if agent_task.done():
                    # Check for agent task exceptions
                    if agent_task.exception():
                        logger.error(f"Agent task failed: {agent_task.exception()}")
                        raise agent_task.exception()
                    
                    # Send final usage chunk and exit
                    await self._send_final_usage_chunk(total_content)
                    break

                # Wait for next chunk with timeout
                try:
                    chunk_text = await wait_for(chunk_queue.get(), timeout=self._streaming_timeout)
                    
                    # Create and send chat chunk
                    chunk = ChatChunk(
                        id=self._request_id,
                        delta=ChoiceDelta(
                            role=None,  # Role already set in initial chunk
                            content=chunk_text,
                            tool_calls=[],
                        ),
                    )
                    
                    self._event_ch.send_nowait(chunk)
                    total_content += chunk_text
                    
                    logger.debug(f"Sent streaming chunk: {chunk_text[:50]}...")
                    
                except TimeoutError:
                    # Continue checking if agent is done on timeout
                    continue
                    
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}", exc_info=True)
                raise
    
    async def _send_final_usage_chunk(self, total_content: str) -> None:
        """
        Send the final usage chunk with token information.
        
        Args:
            total_content: The complete response content for token counting
        """
        # Estimate tokens (rough approximation)
        estimated_tokens = len(total_content.split())
        
        usage_chunk = ChatChunk(
            id=self._request_id,
            delta=None,
            usage=CompletionUsage(
                completion_tokens=estimated_tokens,
                prompt_tokens=0,  # We don't have this info from Xaibo
                total_tokens=estimated_tokens,
            ),
        )
        self._event_ch.send_nowait(usage_chunk)
        
        logger.debug(f"Sent final usage chunk with {estimated_tokens} estimated tokens")
