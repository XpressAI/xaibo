"""Tolerant parsing of model-emitted tool-call arguments.

Models emit raw control characters (literal newlines) inside JSON string
values; strict json.loads rejects those and the otherwise-valid tool call got
skipped. Parameterless tools arrive with empty arguments, which strict parsing
also rejects — those must become {} rather than dropping the call. Only
irrecoverable arguments return None (the caller skips that call with a warning).
"""
from xaibo.primitives.modules.llm.openai import OpenAILLM


def test_control_characters_inside_strings_parse():
    raw = '{"text": "line one\nline two"}'  # REAL newline inside the JSON string value
    parsed = OpenAILLM._parse_tool_arguments(raw)
    assert parsed == {"text": "line one\nline two"}


def test_valid_json_unchanged():
    assert OpenAILLM._parse_tool_arguments('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_empty_arguments_mean_no_parameters():
    assert OpenAILLM._parse_tool_arguments("") == {}
    assert OpenAILLM._parse_tool_arguments(None) == {}


def test_garbage_returns_none_for_skip():
    assert OpenAILLM._parse_tool_arguments("not json at all {{{") is None


def test_non_dict_json_returns_none_for_skip():
    # A bare list/number can't be passed as kwargs to any tool.
    assert OpenAILLM._parse_tool_arguments("[1, 2]") is None
    assert OpenAILLM._parse_tool_arguments("42") is None
