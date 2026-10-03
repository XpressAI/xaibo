"""Gemini's shape of a reasoning level.

Gemini changed the spelling between generations like Claude did — a
`thinkingLevel` enum on 3+ (`reasoning_mode="level"`, the default) and a
`thinking_budget` in tokens on 2.5 and earlier (`"budget"`) — but its enum has
no rung above HIGH and, on 3.x, no way to switch thinking off at all. These
assert how the option survives those gaps; the request-builder half needs the
`google` extra and skips without it.
"""
import pytest

from xaibo.core.models.llm import LLMOptions, ReasoningEffort


def _thinking(effort, mode="level"):
    """The mapping through a GoogleLLM that never built a client (no key, no SDK
    call needed — `_thinking_config` touches only the mode and the level)."""
    pytest.importorskip("google.genai")
    from xaibo.primitives.modules.llm.google import GoogleLLM
    llm = GoogleLLM.__new__(GoogleLLM)
    llm.reasoning_mode = mode
    return llm._thinking_config(effort)


def test_unset_sends_nothing():
    assert _thinking(None) == {}
    assert _thinking(None, "budget") == {}


def test_level_shape_clamps_upward_to_downward():
    assert _thinking(ReasoningEffort.MEDIUM) == {"thinking_level": "MEDIUM"}
    # the enum stops at HIGH: the rungs above it take HIGH rather than vanishing
    # — the user asked for more thinking, not less
    assert _thinking(ReasoningEffort.XHIGH) == {"thinking_level": "HIGH"}
    assert _thinking("max") == {"thinking_level": "HIGH"}
    # Gemini 3 cannot disable thinking, so `none` is its lowest rung
    assert _thinking("none") == {"thinking_level": "LOW"}
    assert _thinking("minimal") == {"thinking_level": "LOW"}


def test_budget_shape_has_a_real_off_switch():
    assert _thinking("none", "budget") == {"thinking_budget": 0}
    from xaibo.primitives.modules.llm import google
    assert _thinking("low", "budget") == {"thinking_budget": google.BUDGETS["low"]}
    # above high this shape has no ladder either
    assert google.BUDGETS["xhigh"] == google.BUDGETS["high"]


def test_module_puts_a_real_thinking_config_on_the_request():
    # the SDK's `types` module is the namespace ThinkingConfig lives in
    types = pytest.importorskip("google.genai.types")
    from xaibo.primitives.modules.llm.google import GoogleLLM
    llm = GoogleLLM({"api_key": "test-key", "model": "gemini-3.8-flash"})
    config = llm._prepare_config(LLMOptions(reasoning_effort="medium"))
    assert isinstance(config.thinking_config, types.ThinkingConfig)
    assert config.thinking_config.thinking_level == "MEDIUM"
    # unset leaves no thinking_config behind
    assert llm._prepare_config(LLMOptions()).thinking_config is None


def test_budget_mode_reaches_the_sdk_config():
    pytest.importorskip("google.genai")
    from xaibo.primitives.modules.llm.google import GoogleLLM
    llm = GoogleLLM({"api_key": "test-key", "model": "gemini-2.5-pro",
                     "reasoning_mode": "budget"})
    config = llm._prepare_config(LLMOptions(reasoning_effort="none"))
    assert config.thinking_config.thinking_budget == 0


def test_vendor_specific_thinking_config_still_wins():
    pytest.importorskip("google.genai")
    from xaibo.primitives.modules.llm.google import GoogleLLM
    llm = GoogleLLM({"api_key": "test-key", "model": "gemini-3.8-flash"})
    options = LLMOptions(reasoning_effort="high",
                         vendor_specific={"thinking_config": {"thinking_budget": 4096}})
    assert llm._prepare_config(options).thinking_config.thinking_budget == 4096
