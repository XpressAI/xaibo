from typing import Dict, Any
import os

from .openai import OpenAILLM

class RelayLLM(OpenAILLM):
    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        config['base_url'] = 'https://relay.public.cloud.xpress.ai/v1/'
        config['api_key'] = config.get('api_key') or os.environ.get("XPRESSAI_API_TOKEN")
        super().__init__(config)