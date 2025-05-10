import asyncio
import logging
from typing import List, Optional, AsyncIterator, Dict, Any

from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMMessageContentType, LLMOptions, LLMResponse, LLMFunctionCall, LLMUsage, LLMRole


logger = logging.getLogger(__name__)


class MockLLM(LLMProtocol):
    """Implementation of LLMProtocol for Testing Purposes

    Responds exactly with what you configure it to respond with. Will roll over if more requests are received than there are configured responses.
    """
    
    def __init__(
        self,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the  MockLLM module.
        
        Args:
            config: Configuration dictionary with the following keys:
                - streaming_delay: number in milliseconds. Defaults to 0.
                - streaming_chunk_size: number of characters per chunk when streaming. Defaults to 3.
                - responses: A list of responses you want to receive in the LLMResponse format
        """
        config = config or {}
        
        self.streaming_delay = config.get('streaming_delay') or 0
        self.streaming_chunk_size = config.get('streaming_chunk_size') or 3
        self.responses = config.get('responses') or []

        if len(self.responses) == 0:
            raise ValueError("Invalid MockLLM Configuration. No responses.")

        self.cur = 0


    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        cur_response = self.responses[self.cur]
        self.cur = (self.cur + 1) % len(self.responses)
        return LLMResponse(**cur_response)

    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        response = await self.generate(messages, options)

        total_len = len(response.content)
        cur = 0
        while cur < total_len:
            await asyncio.sleep(self.streaming_delay / 1000)
            yield response.content[cur:cur+self.streaming_chunk_size]
            cur = cur + self.streaming_chunk_size