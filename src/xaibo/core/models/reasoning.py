"""Provider spellings of one `ReasoningEffort`.

Every vendor names the thinking dial differently, and — the part that bites —
the *same vendor* changed the spelling between model generations: Anthropic's
`thinking.budget_tokens` is deprecated on Claude 4.6 and rejected by 4.7+, which
take `output_config.effort` instead. So a level cannot be mapped from the option
alone; a provider module also needs to know which shape its model speaks. That is
why the mapping lives here once and each module takes a `reasoning_mode` config
key, defaulting to the shape current models accept.

Three rules every mapping here obeys:

- **unset sends nothing.** A model not told how much to think uses its own
  default; inventing a value would make a UI's "default" a lie.
- **a level the model cannot express is lowered, never dropped.** `xhigh` on a
  Gemini model whose ladder stops at `HIGH` sends `HIGH`: the user asked for more
  thinking, and silently sending none is the wrong direction of error.
- **where a model has no off switch, say so in the mapping.** Gemini 3 cannot
  disable thinking at all, so `none` takes its lowest rung rather than sending a
  budget of 0 that a 3.x model rejects.
"""

from typing import Any, Dict, Optional

from .llm import ReasoningEffort

# Anthropic's effort ladder (`output_config.effort`). `minimal` is not on it, and
# `none` is expressed as `thinking: {type: "disabled"}` instead.
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")

# Token budgets for the budget-based shape: Claude 4.5 and earlier, and Gemini
# 2.5, where depth is only expressible as a number of thinking tokens. The two
# rungs above `high` take high's budget — a model that speaks this shape has no
# ladder past high, so the levels above it can only mean "at least this much".
BUDGETS = {
    "minimal": 1024,     # Anthropic's documented minimum for budget_tokens
    "low": 2048,
    "medium": 8192,
    "high": 16384,
    "xhigh": 16384,
    "max": 16384,
}

# Thinking tokens count toward `max_tokens`, so a budget needs answer room on
# top of it or the response comes back truncated — Anthropic rejects a budget
# that is not strictly below `max_tokens`.
ANSWER_ROOM = 1024

# Gemini's `thinkingLevel` enum (the SDK's values are uppercase). `minimal` is
# only on some models, so it takes `LOW`, the rung every thinking Gemini has;
# `none` has no rung at all on Gemini 3 (thinking cannot be switched off), and
# anything above HIGH clamps to it.
GEMINI_LEVELS = {
    "none": "LOW", "minimal": "LOW", "low": "LOW",
    "medium": "MEDIUM", "high": "HIGH", "xhigh": "HIGH", "max": "HIGH",
}


def _value(effort) -> Optional[str]:
    """The level as a string, from either the enum or a raw config value."""
    if effort is None:
        return None
    return effort.value if isinstance(effort, ReasoningEffort) else str(effort)


def anthropic_kwargs(effort, mode: str = "effort",
                     max_tokens: Optional[int] = None) -> Dict[str, Any]:
    """Request fields for an Anthropic-shaped body — the Messages API and
    Bedrock's `additionalModelRequestFields` take the same ones.

    `mode="effort"` (adaptive thinking, Claude 4.6 onward) sends the level as
    `output_config.effort`, which shapes the whole response and needs no budget
    arithmetic. `mode="budget"` (Claude 4.5 and earlier) sends
    `thinking: {type: "enabled", budget_tokens: N}` and raises `max_tokens`
    above the budget, because thinking is billed against it.
    """
    level = _value(effort)
    if not level:
        return {}
    if level == "none":
        return {"thinking": {"type": "disabled"}}

    if mode == "effort":
        return {
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": level if level in EFFORT_LEVELS else "low"},
        }

    budget = BUDGETS.get(level, BUDGETS["high"])
    kwargs: Dict[str, Any] = {"thinking": {"type": "enabled", "budget_tokens": budget}}
    if max_tokens is None or max_tokens <= budget:
        kwargs["max_tokens"] = budget + ANSWER_ROOM
    return kwargs


def gemini_thinking(effort, mode: str = "level") -> Dict[str, Any]:
    """`thinkingConfig` fields for the Gemini API.

    `mode="level"` (Gemini 3+, the recommended shape) sends the `thinkingLevel`
    enum; `mode="budget"` (Gemini 2.5 and earlier) sends `thinking_budget`
    tokens, where 0 is the documented off switch.
    """
    level = _value(effort)
    if not level:
        return {}
    if mode == "budget":
        return {"thinking_budget": 0 if level == "none" else BUDGETS.get(level, BUDGETS["high"])}
    return {"thinking_level": GEMINI_LEVELS.get(level, "HIGH")}
