import json

import httpx
import pytest
from openai import AsyncOpenAI

from xaibo.cli import get_default_model_for_provider
from xaibo.core.models.llm import LLMMessage, LLMOptions
from xaibo.core.models.tools import Tool
from xaibo.primitives.modules.llm import openai as openai_module


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config", "vendor_specific", "expected_host", "expected_model", "token_field"),
    [
        ({}, {}, "api.openai.com", "gpt-5.6-luna", "max_completion_tokens"),
        ({"base_url": None}, {}, "api.openai.com", "gpt-5.6-luna", "max_completion_tokens"),
        ({}, {"model": "gpt-4.1-mini"}, "api.openai.com", "gpt-4.1-mini", "max_tokens"),
        ({"model": "gpt-4.1-mini"}, {}, "api.openai.com", "gpt-4.1-mini", "max_tokens"),
        ({"base_url": "https://gateway.example/v1", "model": "gpt-5.6-luna"}, {},
         "gateway.example", "gpt-5.6-luna", "max_tokens"),
    ],
)
async def test_openai_model_payload(monkeypatch, config, vendor_specific, expected_host, expected_model, token_field):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    requests = []

    def mock_response(request):
        assert request.url.host == expected_host
        assert request.url.path == "/v1/chat/completions"
        payload = json.loads(request.content)
        requests.append(payload)
        response = {"id": "test", "created": 0, "model": payload["model"]}
        if payload.get("stream"):
            chunk = {**response, "object": "chat.completion.chunk",
                     "choices": [{"index": 0, "delta": {"content": "hello"}, "finish_reason": None}]}
            return httpx.Response(200, headers={"content-type": "text/event-stream"},
                                  text=f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n")
        response.update(object="chat.completion", choices=[
            {"index": 0, "message": {"role": "assistant", "content": "hello"}, "finish_reason": "stop"}
        ])
        return httpx.Response(200, json=response)

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_response)) as http_client:
        monkeypatch.setattr(openai_module, "AsyncOpenAI", lambda **kw: AsyncOpenAI(http_client=http_client, **kw))
        llm = openai_module.OpenAILLM({"api_key": "not-a-real-key", **config})
        opts = LLMOptions(max_tokens=32, temperature=0.5, vendor_specific=vendor_specific, functions=[
            Tool(name="get_weather", description="Read a sample weather result", parameters={})
        ])
        messages = [LLMMessage.user("Check the weather")]
        assert (await llm.generate(messages, opts)).content == "hello"
        assert [s async for s in llm.generate_stream(messages, opts)] == ["hello"]

    assert [req.get("stream", False) for req in requests] == [False, True]
    for payload in requests:
        assert payload["model"] == expected_model
        assert payload[token_field] == 32
        assert payload["tools"][0]["function"]["name"] == "get_weather"
        assert payload["temperature"] == 0.5
        if token_field == "max_completion_tokens":
            assert payload["reasoning_effort"] == "none"
            assert "max_tokens" not in payload
        else:
            assert "reasoning_effort" not in payload
            assert "max_completion_tokens" not in payload


def test_openai_scaffold_model_matches_runtime_default():
    assert get_default_model_for_provider("openai") == ("OpenAILLM", openai_module.DEFAULT_OPENAI_MODEL)
