"""Reasoning levels reach every provider in *its own* shape.

`LLMOptions.reasoning_effort` is one field; the wire is not one shape. Anthropic
takes `output_config.effort` on adaptive-thinking models and
`thinking.budget_tokens` on older ones (4.7+ rejects the budget form outright),
Gemini takes a `thinkingLevel` enum on 3+ and a `thinking_budget` on 2.x, Bedrock
Converse carries Anthropic's fields in `additionalModelRequestFields` under
different names for its ceiling, and OpenAI-compatible APIs take the field
verbatim (`test_reasoning_effort.py` covers that one).

These are request-builder tests, so they need no key and no network: the failure
they are guarding against is a level that is configured, displayed and then
silently dropped on the way out — or sent in a shape the model 400s on.
"""
import pytest

from xaibo.core.models.llm import LLMOptions, ReasoningEffort
from xaibo.core.models import reasoning


# --------------------------------------------------------------- the mapping

def test_unset_sends_nothing_too():
    # a model not asked how much to think uses its own default; inventing a
    # value here would make every frontend's "default" a lie
    assert reasoning.anthropic_kwargs(None) == {}
    assert reasoning.anthropic_kwargs(None, "budget") == {}
    assert reasoning.gemini_thinking(None) == {}
    assert reasoning.gemini_thinking(None, "budget") == {}


def test_anthropic_effort_shape():
    assert reasoning.anthropic_kwargs("high") == {
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    }
    # `none` is Anthropic's disabled thinking, not an effort level
    assert reasoning.anthropic_kwargs("none")["thinking"] == {"type": "disabled"}
    # `minimal` has no rung on Anthropic's ladder and must not be dropped
    assert reasoning.anthropic_kwargs("minimal")["output_config"]["effort"] == "low"
    # the enum and its string mean the same thing
    assert reasoning.anthropic_kwargs(ReasoningEffort.MAX) == \
        reasoning.anthropic_kwargs("max")


def test_anthropic_budget_shape_raises_the_ceiling():
    """Budget-based thinking is billed against `max_tokens` and must be strictly
    below it, so a level has to move the ceiling — the request is otherwise
    truncated or rejected."""
    kwargs = reasoning.anthropic_kwargs("high", "budget", max_tokens=1024)
    assert kwargs["thinking"]["type"] == "enabled"
    assert kwargs["thinking"]["budget_tokens"] == reasoning.BUDGETS["high"]
    assert kwargs["max_tokens"] > kwargs["thinking"]["budget_tokens"]

    # an explicit ceiling with room for the budget is left alone
    assert "max_tokens" not in reasoning.anthropic_kwargs("low", "budget", max_tokens=100_000)
    # the minimum Anthropic accepts for a budget is its documented 1024, and the
    # rungs above high share high's budget: a budget-based model has no ladder
    # past it, so they can only mean "at least this much"
    assert reasoning.BUDGETS["minimal"] == 1024
    assert reasoning.BUDGETS["xhigh"] == reasoning.BUDGETS["high"]


def test_gemini_level_shape_clamps_upward_to_downward():
    assert reasoning.gemini_thinking("medium") == {"thinking_level": "MEDIUM"}
    # Gemini's enum stops at HIGH: the rungs above it take HIGH rather than
    # vanishing — the user asked for more thinking, not less
    assert reasoning.gemini_thinking("xhigh") == {"thinking_level": "HIGH"}
    assert reasoning.gemini_thinking("max") == {"thinking_level": "HIGH"}
    # Gemini 3 cannot disable thinking, so `none` is its lowest rung
    assert reasoning.gemini_thinking("none") == {"thinking_level": "LOW"}


def test_gemini_budget_shape():
    assert reasoning.gemini_thinking("none", "budget") == {"thinking_budget": 0}
    assert reasoning.gemini_thinking("low", "budget") == \
        {"thinking_budget": reasoning.BUDGETS["low"]}


# ------------------------------------------------------------- provider glue
# Each provider module's request builder is exercised with a dummy key; the SDK
# is only needed to construct the client, and no request is ever made.

@pytest.fixture(scope="module")
def anthropic_llm():
    pytest.importorskip("anthropic")
    from xaibo.primitives.modules.llm.anthropic import AnthropicLLM
    return AnthropicLLM({"api_key": "test-key", "model": "claude-opus-5"})


def test_anthropic_module_sends_the_level(anthropic_llm):
    kwargs = anthropic_llm._prepare_request_kwargs(
        [{"role": "user", "content": "hi"}], None, None,
        LLMOptions(reasoning_effort="high"))
    assert kwargs["output_config"] == {"effort": "high"}
    assert kwargs["thinking"] == {"type": "adaptive"}


def test_anthropic_module_default_is_the_current_shape(anthropic_llm):
    """An unconfigured module speaks the shape current models accept — the
    deprecated budget form is the opt-in, not the default."""
    assert anthropic_llm.reasoning_mode == "effort"
    # unset: no thinking fields at all, so the model's own default stands
    kwargs = anthropic_llm._prepare_request_kwargs(
        [{"role": "user", "content": "hi"}], None, None, LLMOptions())
    assert "thinking" not in kwargs and "output_config" not in kwargs


def test_anthropic_budget_mode_from_config():
    pytest.importorskip("anthropic")
    from xaibo.primitives.modules.llm.anthropic import AnthropicLLM
    llm = AnthropicLLM({"api_key": "test-key", "model": "claude-sonnet-4-5",
                       "reasoning_mode": "budget"})
    kwargs = llm._prepare_request_kwargs(
        [{"role": "user", "content": "hi"}], None, None,
        LLMOptions(reasoning_effort="medium"))
    assert kwargs["thinking"]["type"] == "enabled"
    assert kwargs["max_tokens"] > kwargs["thinking"]["budget_tokens"]
    # `reasoning_mode` is a module setting, not something sent to the API
    assert "reasoning_mode" not in kwargs


def test_anthropic_config_can_still_pin_thinking_explicitly():
    """A hand-set `thinking` in the config outranks the level: someone who wrote
    it meant it, and the level is the last thing applied."""
    pytest.importorskip("anthropic")
    from xaibo.primitives.modules.llm.anthropic import AnthropicLLM
    llm = AnthropicLLM({"api_key": "test-key", "model": "claude-opus-5",
                       "thinking": {"type": "enabled", "budget_tokens": 4096}})
    kwargs = llm._prepare_request_kwargs(
        [{"role": "user", "content": "hi"}], None, None,
        LLMOptions(reasoning_effort="high"))
    assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 4096}
    assert kwargs["output_config"] == {"effort": "high"}


def test_gemini_module_sends_the_level():
    # the SDK's `types` module is the namespace ThinkingConfig lives in
    types = pytest.importorskip("google.genai.types")
    from xaibo.primitives.modules.llm.google import GoogleLLM
    llm = GoogleLLM({"api_key": "test-key", "model": "gemini-3.8-flash"})
    config = llm._prepare_config(LLMOptions(reasoning_effort="medium"))
    assert isinstance(config.thinking_config, types.ThinkingConfig)
    assert config.thinking_config.thinking_level == "MEDIUM"
    # unset leaves no thinking_config behind
    assert llm._prepare_config(LLMOptions()).thinking_config is None


def test_gemini_budget_mode_reaches_the_sdk_config():
    pytest.importorskip("google.genai")
    from xaibo.primitives.modules.llm.google import GoogleLLM
    llm = GoogleLLM({"api_key": "test-key", "model": "gemini-2.5-pro",
                     "reasoning_mode": "budget"})
    config = llm._prepare_config(LLMOptions(reasoning_effort="none"))
    assert config.thinking_config.thinking_budget == 0


def test_bedrock_module_sends_the_level_and_the_ceiling():
    pytest.importorskip("boto3")
    from xaibo.primitives.modules.llm.bedrock import BedrockLLM
    from xaibo.core.models.llm import LLMMessage

    llm = BedrockLLM({"aws_access_key_id": "test", "aws_secret_access_key": "test",
                      "region_name": "us-east-1", "model": "anthropic.claude-opus-5"})
    request = llm._prepare_converse_request([LLMMessage.user("hi")],
                                            LLMOptions(reasoning_effort="high"))
    fields = request["additionalModelRequestFields"]
    assert fields["thinking"] == {"type": "adaptive"}
    assert fields["output_config"] == {"effort": "high"}

    # budget mode on Converse: the ceiling lives in inferenceConfig, spelled
    # maxTokens, and a level may only ever raise it
    budgeted = BedrockLLM({"aws_access_key_id": "test", "aws_secret_access_key": "test",
                           "region_name": "us-east-1", "model": "anthropic.claude-sonnet-4-5",
                           "reasoning_mode": "budget"})
    req = budgeted._prepare_converse_request([LLMMessage.user("hi")],
                                             LLMOptions(reasoning_effort="high"))
    assert req["additionalModelRequestFields"]["thinking"]["budget_tokens"] \
        == reasoning.BUDGETS["high"]
    assert req["inferenceConfig"]["maxTokens"] > \
        req["additionalModelRequestFields"]["thinking"]["budget_tokens"]

    # a non-Anthropic model on the same endpoint: say so, and send nothing
    off = BedrockLLM({"aws_access_key_id": "test", "aws_secret_access_key": "test",
                      "region_name": "us-east-1", "model": "mistral.large",
                      "reasoning_mode": "off"})
    req = off._prepare_converse_request([LLMMessage.user("hi")],
                                        LLMOptions(reasoning_effort="high"))
    assert "additionalModelRequestFields" not in req


def test_bedrock_vendor_specific_still_wins():
    pytest.importorskip("boto3")
    from xaibo.primitives.modules.llm.bedrock import BedrockLLM
    from xaibo.core.models.llm import LLMMessage

    llm = BedrockLLM({"aws_access_key_id": "test", "aws_secret_access_key": "test",
                      "region_name": "us-east-1"})
    options = LLMOptions(reasoning_effort="high",
                         vendor_specific={"thinking": {"type": "disabled"}})
    request = llm._prepare_converse_request([LLMMessage.user("hi")], options)
    assert request["additionalModelRequestFields"]["thinking"] == {"type": "disabled"}
