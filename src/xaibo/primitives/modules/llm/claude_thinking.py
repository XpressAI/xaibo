"""How Claude says "think this much" — shared by the two providers that run it.

`AnthropicLLM` speaks this shape directly; Bedrock's Converse API carries the
identical `thinking` / `output_config` fields in `additionalModelRequestFields`
for its Claude models. The mapping lives in its own module rather than inside
`anthropic.py` because a provider must not import a sibling provider to reuse
it: `llm/__init__.py` swallows the `ImportError` of any module whose SDK is
missing, so importing `anthropic` without the `anthropic` extra installed fails
even though this code needs nothing from it.

Anthropic changed the spelling between generations, which is why the shape is a
constructor choice rather than derived from the option alone:

- `output_config.effort` — adaptive thinking, Claude 4.6+, and the only shape
  4.7+ accepts (it rejects a `budget_tokens` request with a 400),
- `thinking.budget_tokens` — Claude 4.5 and earlier, deprecated on 4.6.

The rules a level obeys here are the ones `LLMOptions.reasoning_effort` asks of
every provider (see its docstring): unset sends nothing, a level the model
cannot express is lowered rather than dropped, `none` — which Claude *can*
express — becomes `thinking: {type: "disabled"}`.
"""

from typing import Any, Dict, Optional

# Anthropic's effort ladder. `minimal` is not on it and takes `low`.
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")

# Token budgets for the budget-based shape, where depth is only expressible as a
# number of thinking tokens. The rungs above `high` share its budget: a model
# that speaks this shape has no ladder past high, so they can only mean "at
# least this much". 1024 is Anthropic's documented minimum for `budget_tokens`.
BUDGETS = {
    "minimal": 1024,
    "low": 2048,
    "medium": 8192,
    "high": 16384,
    "xhigh": 16384,
    "max": 16384,
}

# Thinking tokens count toward `max_tokens` and a budget must be strictly below
# it, so a budget-shaped request needs room for the answer on top of the budget
# or the response comes back truncated.
ANSWER_ROOM = 1024


def thinking_kwargs(effort, mode: str = "effort",
                    max_tokens: Optional[int] = None) -> Dict[str, Any]:
    """Request fields carrying `reasoning_effort` for an Anthropic-shaped body.

    `mode="effort"` (adaptive thinking, Claude 4.6+) sends the level as
    `output_config.effort`, which shapes the whole response and needs no budget
    arithmetic. `mode="budget"` (Claude 4.5 and earlier) sends
    `thinking: {type: "enabled", budget_tokens: N}` and — when the caller's
    ceiling cannot hold that budget — a `max_tokens` for the sender to apply as
    its own raised ceiling.
    """
    # `ReasoningEffort` is a str enum, so a member and its name are the same key
    # here — no normalization needed between the option and a config value.
    if not effort:
        return {}
    if effort == "none":
        return {"thinking": {"type": "disabled"}}

    if mode == "effort":
        return {
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": effort if effort in EFFORT_LEVELS else "low"},
        }

    budget = BUDGETS.get(effort, BUDGETS["high"])
    kwargs: Dict[str, Any] = {"thinking": {"type": "enabled", "budget_tokens": budget}}
    if max_tokens is None or max_tokens <= budget:
        kwargs["max_tokens"] = budget + ANSWER_ROOM
    return kwargs
