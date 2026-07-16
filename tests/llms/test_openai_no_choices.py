"""A completion response without choices must raise a useful error.

Some OpenAI-compatible gateways return upstream error bodies (rate limits,
provider failures) with HTTP 200. The SDK constructs those leniently, leaving
`choices` as None/absent, and `response.choices[0]` then raised a bare
"'NoneType' object is not subscriptable" that hid the actual upstream error.
"""
from types import SimpleNamespace

import pytest
from openai.types.chat import ChatCompletion

from xaibo.primitives.modules.llm.openai import OpenAILLM


def test_none_choices_raises_with_body_detail():
    response = SimpleNamespace(
        choices=None,
        model_dump_json=lambda exclude_none: '{"code": "rate_limit_daily", "message": "Error code: 429"}',
    )
    with pytest.raises(RuntimeError) as exc:
        OpenAILLM._require_choices(response)
    assert "without choices" in str(exc.value)
    assert "rate_limit_daily" in str(exc.value)


def test_empty_choices_list_raises():
    response = SimpleNamespace(
        choices=[],
        model_dump_json=lambda exclude_none: "{}",
    )
    with pytest.raises(RuntimeError):
        OpenAILLM._require_choices(response)


def test_real_sdk_lenient_construction_raises():
    # What the SDK actually produces for an error body returned with 200:
    # construct() doesn't validate, so `choices` is simply absent.
    response = ChatCompletion.construct(code="rate_limit_daily", message="Error code: 429 - {...}")
    with pytest.raises(RuntimeError) as exc:
        OpenAILLM._require_choices(response)
    assert "rate_limit_daily" in str(exc.value)


def test_detail_falls_back_to_repr_when_dump_fails():
    class Undumpable:
        choices = None

        def model_dump_json(self, **kwargs):
            raise ValueError("nope")

        def __repr__(self):
            return "<weird body>"

    with pytest.raises(RuntimeError) as exc:
        OpenAILLM._require_choices(Undumpable())
    assert "<weird body>" in str(exc.value)


def test_normal_response_passes():
    response = SimpleNamespace(choices=[SimpleNamespace(message=None)])
    OpenAILLM._require_choices(response)  # must not raise
