"""`LLMOptions.reasoning_effort` reaches the wire as the API's own field.

A reasoning level is the one dial users of thinking models actually turn, and
the failure mode of getting it wrong is silent: a provider that never sees the
field answers at its own default while the caller believes it asked for `high`.
So the contract is checked offline, at the request-builder, with no gateway and
no key — `_prepare_request_kwargs` is where the value either lands or vanishes.
"""
import pytest

from xaibo.core.models.llm import LLMOptions, ReasoningEffort
from xaibo.primitives.modules.llm.openai import OpenAILLM


def _llm(config=None) -> OpenAILLM:
    # a key is required by the constructor; nothing here makes a request
    return OpenAILLM({**(config or {}), "api_key": "test-key", "model": "gpt-5-mini"})


def _kwargs(llm, options) -> dict:
    return llm._prepare_request_kwargs([{"role": "user", "content": "hi"}], None, options)


def test_levels_are_the_union_the_providers_share():
    # `none` is the explicit off switch, `minimal`..`max` the ladder; these
    # strings go on the wire, so renaming one is a breaking change
    assert [e.value for e in ReasoningEffort] == [
        "none", "minimal", "low", "medium", "high", "xhigh", "max"]


def test_level_defaults_to_unset():
    assert LLMOptions().reasoning_effort is None


@pytest.mark.parametrize("raw", ["low", ReasoningEffort.LOW])
def test_level_accepts_its_string_or_the_enum(raw):
    assert LLMOptions(reasoning_effort=raw).reasoning_effort is ReasoningEffort.LOW


def test_unknown_level_is_rejected_at_the_model():
    # failing here, at construction, is what keeps a typo from becoming a
    # request the provider silently answers at its own default
    with pytest.raises(Exception):
        LLMOptions(reasoning_effort="very_hard_please")


def test_openai_sends_the_field_only_when_set():
    llm = _llm()

    assert "reasoning_effort" not in _kwargs(llm, LLMOptions())
    assert _kwargs(llm, LLMOptions(reasoning_effort="medium"))["reasoning_effort"] == "medium"
    # `none` is a real instruction, not an absent one — it must survive the
    # builder's None-stripping pass
    assert _kwargs(llm, LLMOptions(reasoning_effort="none"))["reasoning_effort"] == "none"


def test_openai_streaming_carries_the_same_field():
    llm = _llm()
    kwargs = llm._prepare_request_kwargs([{"role": "user", "content": "hi"}], None,
                                         LLMOptions(reasoning_effort="high"), stream=True)
    assert kwargs["reasoning_effort"] == "high"
    assert kwargs["stream"] is True


def test_agent_config_can_pin_a_level_as_yaml():
    # the config path people actually use: a level declared in an agent YAML
    # must arrive as a string the option accepts, not as something to convert
    from xaibo.core.config import AgentConfig

    cfg = AgentConfig.model_validate({
        "id": "thinker",
        "modules": [{"module": "xaibo.primitives.modules.llm.MockLLM", "id": "llm",
                     "config": {"responses": [{"content": "ok"}],
                                 "reasoning_effort": "high"}}],
    })
    level = cfg.modules[0].config["reasoning_effort"]
    assert LLMOptions(reasoning_effort=level).reasoning_effort is ReasoningEffort.HIGH
