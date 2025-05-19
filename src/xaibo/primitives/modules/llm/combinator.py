import asyncio
import logging
from typing import List, Optional, AsyncIterator, Dict, Any

from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMMessageContentType, LLMOptions, LLMResponse, LLMFunctionCall, LLMUsage, \
    LLMRole, LLMMessageContent

logger = logging.getLogger(__name__)


class LLMCombinator(LLMProtocol):
    """Combines multiple language models and executes them sequentially with specialized prompts.
    
    This class allows chaining multiple LLMs together, with each LLM receiving a specialized prompt
    and the outputs of previous LLMs in the chain. The final result combines the outputs of all LLMs.
    """

    def __init__(
            self,
            llms: list[LLMProtocol],
            config: Dict[str, Any] = None
    ):
        """
        Initialize the LLMCombinator module.

        Args:
            llms: List of LLM instances that implement the LLMProtocol
            config: Configuration dictionary with the following keys:
                - prompts: list of specialized prompts, one for each LLM. Each prompt will be appended
                  to the system message for its corresponding LLM.

        Raises:
            ValueError: If the number of prompts doesn't match the number of LLMs
        """
        config = config or {}
        self.lmms = llms
        self.prompts = config.get('prompts') or []

        if len(self.prompts) != len(llms):
            raise ValueError(f"Number of prompts ({len(self.prompts)}) does not match number of LLMs ({len(llms)})")

    async def generate(
            self,
            messages: list[LLMMessage],
            options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response by sequentially calling each LLM in the chain.

        Args:
            messages: List of input messages
            options: Optional generation options that will be passed to each LLM

        Returns:
            A merged LLMResponse containing the combined outputs of all LLMs
        """
        results = []
        for (llm, prompt) in zip(self.lmms, self.prompts):
            messages = self._adapt_system_prompt(messages, prompt, results)
            response = await llm.generate(messages, options)
            results.append(response)
        return LLMResponse.merge(*results)

    async def generate_stream(
            self,
            messages: list[LLMMessage],
            options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Stream responses from each LLM in sequence.

        Args:
            messages: List of input messages
            options: Optional generation options that will be passed to each LLM

        Yields:
            Text chunks from each LLM in sequence
        """
        results = []
        for (llm, prompt) in zip(self.lmms, self.prompts):
            messages = self._adapt_system_prompt(messages, prompt, results)
            chunks = []
            async for chunk in llm.generate_stream(messages, options):
                chunks.append(chunk)
                yield chunk
            content = ''.join(chunks)
            results.append(LLMResponse(content=content))

    def _adapt_system_prompt(self, messages: list[LLMMessage], prompt: str, intermediate: list[LLMResponse]) -> list[
        LLMMessage]:
        """Adapt the message list by appending the specialized prompt and intermediate results.

        Args:
            messages: Original list of messages
            prompt: Specialized prompt to append to system message
            intermediate: List of intermediate responses from previous LLMs

        Returns:
            Modified list of messages with updated system prompt and intermediate responses
        """
        found_prompt = False
        new_messages = []
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                found_prompt = True
                new_messages.append(
                    LLMMessage(role=LLMRole.SYSTEM,
                               content=msg.content + [
                                   LLMMessageContent(type=LLMMessageContentType.TEXT,
                                                     text=prompt)
                               ],
                               name=msg.name)
                )
            else:
                new_messages.append(msg)

        if not found_prompt:
            new_messages.insert(0, LLMMessage.system(prompt))
        for r in intermediate:
            new_messages.append(LLMMessage.assistant(r.content))
        return new_messages
