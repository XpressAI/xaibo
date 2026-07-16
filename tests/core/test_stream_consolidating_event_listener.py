import pytest

from xaibo.core.exchange import Proxy
from xaibo.core.models.events import Event, EventType
from xaibo.primitives.event_listeners.stream_consolidating_event_listener import (
    StreamConsolidatingEventListener,
)


class Streamer:
    async def stream(self, count, prefix="chunk"):
        for i in range(count):
            yield f"{prefix}-{i}"

    async def failing_stream(self):
        yield "first"
        raise ValueError("stream broke")

    async def typed_stream(self):
        yield {"type": "text_delta", "text": "Hello"}
        yield {"type": "usage", "total_tokens": 5}

    async def empty_stream(self):
        return
        yield  # pragma: no cover - makes this an async generator

    async def regular(self):
        return "hello"


def make_proxy(obj, sink, extra_listeners=()):
    listener = StreamConsolidatingEventListener(sink.append)
    listeners = [("", listener.handle_event), *extra_listeners]
    return Proxy(obj, event_listeners=listeners, agent_id="test-agent", caller_id="test-caller", module_id="test-module")


@pytest.mark.asyncio
async def test_streamed_call_consolidates_to_call_and_result():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    chunks = [chunk async for chunk in proxy.stream(3, prefix="foo")]
    assert chunks == ["foo-0", "foo-1", "foo-2"]

    event_types = [e.event_type for e in sink]
    assert event_types == [EventType.CALL, EventType.RESULT]
    assert sink[1].result == {"stream": True, "chunks": 3, "content": "foo-0foo-1foo-2"}
    assert sink[1].call_id == sink[0].call_id


@pytest.mark.asyncio
async def test_non_streamed_call_passes_through_untouched():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    result = await proxy.regular()
    assert result == "hello"

    event_types = [e.event_type for e in sink]
    assert event_types == [EventType.CALL, EventType.RESULT]
    assert sink[1].result == "hello"


@pytest.mark.asyncio
async def test_empty_stream_result_forwarded_untouched():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    chunks = [chunk async for chunk in proxy.empty_stream()]
    assert chunks == []

    event_types = [e.event_type for e in sink]
    assert event_types == [EventType.CALL, EventType.RESULT]
    assert sink[1].result == {"stream": True, "chunks": 0}


@pytest.mark.asyncio
async def test_original_events_are_not_mutated():
    sink = []
    raw = []
    proxy = make_proxy(Streamer(), sink, extra_listeners=[("", raw.append)])

    [chunk async for chunk in proxy.stream(2)]

    raw_result = [e for e in raw if e.event_type == EventType.RESULT][0]
    assert "content" not in raw_result.result
    assert raw_result.result == {"stream": True, "chunks": 2}


@pytest.mark.asyncio
async def test_typed_chunks_kept_as_list():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    chunks = [chunk async for chunk in proxy.typed_stream()]
    assert len(chunks) == 2

    assert sink[1].event_type == EventType.RESULT
    assert sink[1].result == {
        "stream": True,
        "chunks": 2,
        "content": [
            {"type": "text_delta", "text": "Hello"},
            {"type": "usage", "total_tokens": 5},
        ],
    }


@pytest.mark.asyncio
async def test_early_close_keeps_partial_content_and_flag():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    gen = proxy.stream(10)
    assert await anext(gen) == "chunk-0"
    await gen.aclose()

    event_types = [e.event_type for e in sink]
    assert event_types == [EventType.CALL, EventType.RESULT]
    assert sink[1].result == {
        "stream": True,
        "chunks": 1,
        "content": "chunk-0",
        "closed_early": True,
    }


@pytest.mark.asyncio
async def test_mid_stream_exception_carries_partial_content():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    received = []
    with pytest.raises(ValueError, match="stream broke"):
        async for chunk in proxy.failing_stream():
            received.append(chunk)

    assert received == ["first"]

    event_types = [e.event_type for e in sink]
    assert event_types == [EventType.CALL, EventType.EXCEPTION]
    assert sink[1].result == {
        "stream": True,
        "chunks": 1,
        "content": "first",
        "incomplete": True,
    }
    assert "stream broke" in sink[1].exception


@pytest.mark.asyncio
async def test_interleaved_streams_do_not_cross_contaminate():
    sink = []
    proxy = make_proxy(Streamer(), sink)

    gen_a = proxy.stream(2, prefix="a")
    gen_b = proxy.stream(2, prefix="b")

    assert await anext(gen_a) == "a-0"
    assert await anext(gen_b) == "b-0"
    assert await anext(gen_a) == "a-1"
    assert await anext(gen_b) == "b-1"
    with pytest.raises(StopAsyncIteration):
        await anext(gen_a)
    with pytest.raises(StopAsyncIteration):
        await anext(gen_b)

    results = [e for e in sink if e.event_type == EventType.RESULT]
    contents = sorted(r.result["content"] for r in results)
    assert contents == ["a-0a-1", "b-0b-1"]
