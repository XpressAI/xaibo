"""Claude's shape of a reasoning level, in both modules that speak it.

`LLMOptions.reasoning_effort` is one field; how Claude hears it is not one
shape — `output_config.effort` on adaptive-thinking models (4.6+),
`thinking.budget_tokens` on budget-based ones (4.5 and earlier, 400-rejected by
4.7+). Bedrock's Converse API carries the same fields in
`additionalModelRequestFields`, so both providers are tested against one
mapping and their own request builders.

Request-builder tests: no key, no network. The failure being guarded is silent
either way — a level configured, displayed and then dropped on the way out, or
sent in a shape the model rejects.
"""
import pytest

from xaibo.core.models.llm import LLMMessage, LLMOptions, ReasoningEffort
from xaibo.primitives.modules.llm import claude_thinking
from xaibo.primitives.modules.llm.claude_thinking import thinking_kwargs


# ------------------------------------------------------- the mapping itself

def test_unset_sends_nothing():
    # a model not asked how much to think uses its own default; inventing a
    # value here would make every frontend's "default" a lie
    assert thinking_kwargs(None) == {}
    assert thinking_kwargs(None, "budget") == {}


def test_effort_shape():
    assert thinking_kwargs("high") == {
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "high"},
    }
    # `none` is Claude's disabled thinking, not an effort level
    assert thinking_kwargs("none")["thinking"] == {"type": "disabled"}
    # `minimal` has no rung on Claude's ladder and must not be dropped
    assert thinking_kwargs("minimal")["output_config"]["effort"] == "low"
    # the enum and its string mean the same thing
    assert thinking_kwargs(ReasoningEffort.MAX) == thinking_kwargs("max")


def test_budget_shape_raises_the_ceiling():
    """Budget-based thinking is billed against `max_tokens` and must be strictly
    below it, so a level has to move the ceiling or the request truncates."""
    kwargs = thinking_kwargs("high", "budget", max_tokens=1024)
    assert kwargs["thinking"]["type"] == "enabled"
    assert kwargs["thinking"]["budget_tokens"] == claude_thinking.BUDGETS["high"]
    assert kwargs["max_tokens"] > kwargs["thinking"]["budget_tokens"]

    # an explicit ceiling with room for the budget is left alone
    assert "max_tokens" not in thinking_kwargs("low", "budget", max_tokens=100_000)
    # 1024 is the documented minimum budget, and the rungs above high share
    # high's budget: this shape has no ladder past it
    assert claude_thinking.BUDGETS["minimal"] == 1024
    assert claude_thinking.BUDGETS["xhigh"] == claude_thinking.BUDGETS["high"]


# ------------------------------------------------------------ AnthropicLLM

@pytest.fixture(scope="module")
def anthropic_llm():
    pytest.importorskip("anthropic")
    from xaibo.primitives.modules.llm.anthropic import AnthropicLLM
    return AnthropicLLM({"api_key": "test-key", "model": "claude-opus-5"})


def _kwargs(llm, options):
    return llm._prepare_request_kwargs([{"role": "user", "content": "hi"}],
                                       None, None, options)


def test_module_sends_the_level(anthropic_llm):
    kwargs = _kwargs(anthropic_llm, LLMOptions(reasoning_effort="high"))
    assert kwargs["output_config"] == {"effort": "high"}
    assert kwargs["thinking"] == {"type": "adaptive"}


def test_default_is_the_current_shape(anthropic_llm):
    """An unconfigured module speaks the shape current models accept — the
    deprecated budget form is the opt-in, not the default."""
    assert anthropic_llm.reasoning_mode == "effort"
    kwargs = _kwargs(anthropic_llm, LLMOptions())
    assert "thinking" not in kwargs and "output_config" not in kwargs


def test_budget_mode_from_config():
    pytest.importorskip("anthropic")
    from xaibo.primitives.modules.llm.anthropic import AnthropicLLM
    llm = AnthropicLLM({"api_key": "test-key", "model": "claude-sonnet-4-5",
                        "reasoning_mode": "budget"})
    kwargs = _kwargs(llm, LLMOptions(reasoning_effort="medium"))
    assert kwargs["thinking"]["type"] == "enabled"
    assert kwargs["max_tokens"] > kwargs["thinking"]["budget_tokens"]
    # `reasoning_mode` is a module setting, not something sent to the API
    assert "reasoning_mode" not in kwargs


def test_config_can_still_pin_thinking_explicitly():
    """A hand-set `thinking` in the config outranks the level: someone who wrote
    it meant it, and the level is the last thing applied."""
    pytest.importorskip("anthropic")
    from xaibo.primitives.modules.llm.anthropic import AnthropicLLM
    llm = AnthropicLLM({"api_key": "test-key", "model": "claude-opus-5",
                        "thinking": {"type": "enabled", "budget_tokens": 4096}})
    kwargs = _kwargs(llm, LLMOptions(reasoning_effort="high"))
    assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 4096}
    assert kwargs["output_config"] == {"effort": "high"}


# ------------------------------------------------------------------ Bedrock

def _bedrock(**config):
    pytest.importorskip("boto3")
    from xaibo.primitives.modules.llm.bedrock import BedrockLLM
    return BedrockLLM({"aws_access_key_id": "test", "aws_secret_access_key": "test",
                       "region_name": "us-east-1", **config})


def test_bedrock_sends_the_level_and_the_ceiling():
    llm = _bedrock(model="anthropic.claude-opus-5")
    request = llm._prepare_converse_request([LLMMessage.user("hi")],
                                            LLMOptions(reasoning_effort="high"))
    fields = request["additionalModelRequestFields"]
    assert fields["thinking"] == {"type": "adaptive"}
    assert fields["output_config"] == {"effort": "high"}

    # budget mode on Converse: the ceiling lives in inferenceConfig, spelled
    # maxTokens, and a level may only ever raise it
    budgeted = _bedrock(model="anthropic.claude-sonnet-4-5", reasoning_mode="budget")
    req = budgeted._prepare_converse_request([LLMMessage.user("hi")],
                                             LLMOptions(reasoning_effort="high"))
    assert req["additionalModelRequestFields"]["thinking"]["budget_tokens"] \
        == claude_thinking.BUDGETS["high"]
    assert req["inferenceConfig"]["maxTokens"] > \
        req["additionalModelRequestFields"]["thinking"]["budget_tokens"]


def test_bedrock_off_mode_sends_nothing():
    """A non-Claude model on the same endpoint has no thinking dial to be told
    about; `off` is the config answer, and it must not invent fields."""
    llm = _bedrock(model="mistral.large", reasoning_mode="off")
    req = llm._prepare_converse_request([LLMMessage.user("hi")],
                                        LLMOptions(reasoning_effort="high"))
    assert "additionalModelRequestFields" not in req


def test_bedrock_vendor_specific_still_wins():
    llm = _bedrock()
    options = LLMOptions(reasoning_effort="high",
                         vendor_specific={"thinking": {"type": "disabled"}})
    request = llm._prepare_converse_request([LLMMessage.user("hi")], options)
    assert request["additionalModelRequestFields"]["thinking"] == {"type": "disabled"}
