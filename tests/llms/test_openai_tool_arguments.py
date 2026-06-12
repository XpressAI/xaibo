"""Tolerant parsing of model-emitted tool-call arguments.

Models emit raw control characters (literal newlines) inside JSON string
values; strict json.loads rejected those and one malformed tool call aborted
the entire agent turn.
"""
from xaibo.primitives.modules.llm.openai import OpenAILLM


def test_control_characters_inside_strings_parse():
    raw = '{"text": "line one\nline two"}'  # REAL newline inside the JSON string value
    parsed = OpenAILLM._parse_tool_arguments(raw)
    assert parsed["text"] == "line one\nline two"


def test_valid_json_unchanged():
    assert OpenAILLM._parse_tool_arguments('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_empty_arguments():
    assert OpenAILLM._parse_tool_arguments("") == {}
    assert OpenAILLM._parse_tool_arguments(None) == {}


def test_garbage_degrades_to_raw_instead_of_raising():
    parsed = OpenAILLM._parse_tool_arguments("not json at all {{{")
    assert parsed == {"_raw": "not json at all {{{"}


def test_non_object_json_wrapped():
    assert OpenAILLM._parse_tool_arguments("[1, 2]") == {"_raw": [1, 2]}
