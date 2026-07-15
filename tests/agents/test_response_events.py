import pytest

from xaibo import AgentConfig, Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.core.config import ModuleConfig
from xaibo.core.models.response import (
    Response,
    ToolCallEvent,
    ToolResultEvent,
    UsageEvent,
)
from xaibo.core.models.tools import Tool, ToolResult
from xaibo.primitives.modules.conversation import SimpleConversation
from xaibo.primitives.modules.response import ResponseHandler


class StubToolProvider:
    def __init__(self, result: ToolResult):
        self.result = result
        self.calls = []

    async def list_tools(self):
        return [Tool(name="get_time", description="Gets the current time")]

    async def execute_tool(self, tool_name, parameters):
        self.calls.append((tool_name, parameters))
        return self.result


def make_agent(tool_provider, responses):
    config = AgentConfig(
        id="event-emitter",
        modules=[
            ModuleConfig(
                module="xaibo.primitives.modules.llm.MockLLM",
                id="llm",
                config={"responses": responses},
            ),
            ModuleConfig(
                module="xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator",
                id="orchestrator",
                config={"max_thoughts": 5},
            ),
        ],
    )
    xaibo = Xaibo()
    xaibo.register_agent(config)
    return xaibo.get_agent_with("event-emitter", ConfigOverrides(
        instances={
            "tools": tool_provider,
            "history": SimpleConversation(),
        },
        exchange=[
            ExchangeConfig(protocol="ToolProviderProtocol", provider="tools"),
            ExchangeConfig(protocol="ConversationHistoryProtocol", provider="history"),
        ],
    ))


TOOL_CALL_RESPONSE = {
    "content": "",
    "tool_calls": [{"id": "call_1", "name": "get_time", "arguments": {"timezone": "UTC"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}
FINAL_RESPONSE = {
    "content": "It is noon.",
    "usage": {"prompt_tokens": 20, "completion_tokens": 4, "total_tokens": 24},
}


@pytest.mark.asyncio
async def test_response_handler_accumulates_events():
    handler = ResponseHandler()

    await handler.respond_event(ToolCallEvent(id="call_1", name="get_time", arguments={}))
    await handler.respond_event(ToolResultEvent(id="call_1", name="get_time", success=True, result="12:00"))
    await handler.respond_text("It is noon.")

    response = await handler.get_response()
    assert response.text == "It is noon."
    assert [e.type for e in response.events] == ["tool_call", "tool_result"]


@pytest.mark.asyncio
async def test_response_handler_merges_events_from_respond():
    handler = ResponseHandler()

    await handler.respond(Response(text="done", events=[UsageEvent(prompt_tokens=1, completion_tokens=2, total_tokens=3)]))

    response = await handler.get_response()
    assert [e.type for e in response.events] == ["usage"]


@pytest.mark.asyncio
async def test_response_handler_does_not_replay_events_across_turns():
    handler = ResponseHandler()

    await handler.respond_event(ToolCallEvent(id="call_1", name="get_time", arguments={}))
    first = await handler.get_response()
    assert [e.type for e in first.events] == ["tool_call"]

    await handler.respond_event(UsageEvent(prompt_tokens=1, completion_tokens=2, total_tokens=3))
    second = await handler.get_response()
    # Only the second turn's events, and the first turn's response is untouched
    assert [e.type for e in second.events] == ["usage"]
    assert [e.type for e in first.events] == ["tool_call"]


@pytest.mark.asyncio
async def test_orchestrator_emits_tool_and_usage_events():
    tools = StubToolProvider(ToolResult(success=True, result="12:00"))
    agent = make_agent(tools, [TOOL_CALL_RESPONSE, FINAL_RESPONSE])

    response = await agent.handle_text("What time is it?")

    assert response.text == "It is noon."
    assert [e.type for e in response.events] == ["usage", "tool_call", "tool_result", "usage"]

    tool_call = response.events[1]
    assert tool_call.id == "call_1"
    assert tool_call.name == "get_time"
    assert tool_call.arguments == {"timezone": "UTC"}

    tool_result = response.events[2]
    assert tool_result.id == "call_1"
    assert tool_result.success is True
    assert tool_result.result == "12:00"

    assert response.events[0].total_tokens == 15
    assert response.events[3].total_tokens == 24


@pytest.mark.asyncio
async def test_orchestrator_emits_failed_tool_result():
    tools = StubToolProvider(ToolResult(success=False, error="tool unavailable"))
    agent = make_agent(tools, [TOOL_CALL_RESPONSE, FINAL_RESPONSE])

    response = await agent.handle_text("What time is it?")

    tool_result = next(e for e in response.events if e.type == "tool_result")
    assert tool_result.success is False
    assert tool_result.error == "tool unavailable"


@pytest.mark.asyncio
async def test_orchestrator_emits_tool_result_on_exception():
    class ExplodingToolProvider(StubToolProvider):
        async def execute_tool(self, tool_name, parameters):
            raise RuntimeError("kaboom")

    tools = ExplodingToolProvider(None)
    agent = make_agent(tools, [TOOL_CALL_RESPONSE, FINAL_RESPONSE])

    response = await agent.handle_text("What time is it?")

    tool_result = next(e for e in response.events if e.type == "tool_result")
    assert tool_result.success is False
    assert "kaboom" in tool_result.error


@pytest.mark.asyncio
async def test_tool_result_event_is_json_serializable():
    from datetime import datetime

    tools = StubToolProvider(ToolResult(success=True, result={"at": datetime(2026, 7, 16, 12, 0)}))
    agent = make_agent(tools, [TOOL_CALL_RESPONSE, FINAL_RESPONSE])

    response = await agent.handle_text("What time is it?")

    tool_result = next(e for e in response.events if e.type == "tool_result")
    # Non-JSON-serializable values are coerced (via repr), so events can go on the wire
    tool_result.model_dump_json()
    assert "2026" in tool_result.result["at"]
