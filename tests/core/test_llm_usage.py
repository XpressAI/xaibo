"""LLMUsage's prompt-cache count: it must survive a round-trip and a merge.

Consumers journal usage by dumping `LLMResponse` to a dict and rebuilding it
later (record/replay, adapters, ledgers). `cached_tokens` therefore has to be a
field on the declared model — an attribute bolted on by a subclass is dropped by
serialization, because pydantic validates a nested model against its
*annotated* type.
"""
import asyncio

import pytest

from xaibo.core.models.llm import LLMResponse, LLMUsage


def test_cached_tokens_default_to_zero():
    usage = LLMUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12)
    assert usage.cached_tokens == 0


def test_cached_tokens_survive_a_response_round_trip():
    response = LLMResponse(
        content="hi",
        usage=LLMUsage(prompt_tokens=1000, completion_tokens=2,
                       total_tokens=1002, cached_tokens=800),
    )
    restored = LLMResponse(**response.model_dump(mode="json"))
    assert restored.usage.cached_tokens == 800


def test_merge_sums_cached_tokens():
    a = LLMResponse(content="a", usage=LLMUsage(prompt_tokens=10, completion_tokens=1,
                                                total_tokens=11, cached_tokens=9))
    b = LLMResponse(content="b", usage=LLMUsage(prompt_tokens=20, completion_tokens=2,
                                                total_tokens=22, cached_tokens=5))
    merged = LLMResponse.merge(a, b).usage
    assert (merged.prompt_tokens, merged.completion_tokens, merged.total_tokens) == (30, 3, 33)
    assert merged.cached_tokens == 14


def test_merge_accepts_a_usage_without_the_field():
    """A response produced without the field (a plain dict) must still merge —
    cached_tokens defaults, it is not required."""
    a = LLMResponse(content="a", usage={"prompt_tokens": 3, "completion_tokens": 1,
                                        "total_tokens": 4})
    b = LLMResponse(content="b", usage=LLMUsage(prompt_tokens=3, completion_tokens=1,
                                                total_tokens=4, cached_tokens=2))
    assert LLMResponse.merge(a, b).usage.cached_tokens == 2


def test_openai_provider_reads_the_gateway_cache_report():
    """`OpenAILLM.generate` maps the usage object's nested details, which is the
    only place an OpenAI-compatible gateway reports cache hits — and the SDK
    omits `prompt_tokens_details` entirely when nothing was cached."""
    from types import SimpleNamespace

    pytest.importorskip("openai")          # openai is an extra, not a core dep
    from openai.types.chat import ChatCompletion
    from xaibo.primitives.modules.llm.openai import OpenAILLM

    def completion(details):
        return ChatCompletion(
            id="c", object="chat.completion", created=0, model="m",
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": "hi"},
                "finish_reason": "stop",
            }],
            usage={
                "prompt_tokens": 1000,
                "completion_tokens": 10,
                "total_tokens": 1010,
                **({"prompt_tokens_details": {"cached_tokens": details}} if details is not None else {}),
            },
        )

    class Completions:
        def __init__(self, body):
            self.body = body

        async def create(self, **kwargs):
            return self.body

    async def generate(body):
        llm = OpenAILLM({"model": "m", "api_key": "sk-test"})
        llm.client = SimpleNamespace(chat=SimpleNamespace(completions=Completions(body)))
        return (await llm.generate([])).usage

    assert asyncio.run(generate(completion(900))).cached_tokens == 900
    assert asyncio.run(generate(completion(None))).cached_tokens == 0
