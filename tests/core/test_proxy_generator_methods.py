import pytest

from xaibo.core.exchange import Proxy
from xaibo.core.models.events import Event, EventType
from xaibo.primitives.modules.llm.mock import MockLLM
from xaibo.core.models.llm import LLMMessage


class DummyStreamer:
    async def stream_method(self, count, prefix="chunk"):
        for i in range(count):
            yield f"{prefix}-{i}"

    async def failing_stream(self):
        yield "first"
        raise ValueError("stream broke")

    def sync_stream(self, count):
        for i in range(count):
            yield i

    async def typed_stream(self):
        yield {"type": "text_delta", "text": "Hello"}
        yield {"type": "usage", "total_tokens": 5}

    async def empty_stream(self):
        return
        yield  # pragma: no cover - makes this an async generator

    async def regular_method(self):
        return "hello"


@pytest.mark.asyncio
async def test_proxy_async_generator_streams_chunks():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    chunks = [chunk async for chunk in proxy.stream_method(3, prefix="foo")]
    assert chunks == ["foo-0", "foo-1", "foo-2"]

    # One CALL, one YIELD per chunk, one RESULT
    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.YIELD, EventType.YIELD, EventType.YIELD, EventType.RESULT]

    call_event = events[0]
    assert call_event.module_class == "DummyStreamer"
    assert call_event.method_name == "stream_method"
    assert call_event.arguments == {"args": (3,), "kwargs": {"prefix": "foo"}}
    assert call_event.agent_id == "test-agent"

    yield_events = events[1:4]
    assert [e.result for e in yield_events] == ["foo-0", "foo-1", "foo-2"]
    assert all(e.call_id == call_event.call_id for e in yield_events)
    assert yield_events[0].event_name.endswith("stream_method.yield")

    result_event = events[4]
    assert result_event.result == {"stream": True, "chunks": 3}
    assert result_event.call_id == call_event.call_id


@pytest.mark.asyncio
async def test_proxy_async_generator_without_listeners():
    obj = DummyStreamer()
    proxy = Proxy(obj)

    chunks = [chunk async for chunk in proxy.stream_method(2)]
    assert chunks == ["chunk-0", "chunk-1"]


@pytest.mark.asyncio
async def test_proxy_async_generator_exception_mid_stream():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    received = []
    with pytest.raises(ValueError, match="stream broke"):
        async for chunk in proxy.failing_stream():
            received.append(chunk)

    assert received == ["first"]

    # The chunk that made it out is observable before the exception
    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.YIELD, EventType.EXCEPTION]
    assert events[1].result == "first"
    assert "stream broke" in events[2].exception


@pytest.mark.asyncio
async def test_proxy_async_generator_early_close():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    gen = proxy.stream_method(10)
    assert await anext(gen) == "chunk-0"
    await gen.aclose()

    # Early close is not an error; the RESULT still closes out the call
    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.YIELD, EventType.RESULT]
    assert events[2].result == {"stream": True, "chunks": 1, "closed_early": True}


@pytest.mark.asyncio
async def test_proxy_sync_generator():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    chunks = list(proxy.sync_stream(3))
    assert chunks == [0, 1, 2]

    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.YIELD, EventType.YIELD, EventType.YIELD, EventType.RESULT]
    assert [e.result for e in events[1:4]] == [0, 1, 2]
    assert events[4].result == {"stream": True, "chunks": 3}


@pytest.mark.asyncio
async def test_proxy_async_generator_typed_chunks():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    chunks = [chunk async for chunk in proxy.typed_stream()]
    assert len(chunks) == 2

    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.YIELD, EventType.YIELD, EventType.RESULT]
    assert events[1].result == {"type": "text_delta", "text": "Hello"}
    assert events[2].result == {"type": "usage", "total_tokens": 5}
    assert events[3].result == {"stream": True, "chunks": 2}


@pytest.mark.asyncio
async def test_proxy_async_generator_empty_stream():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    chunks = [chunk async for chunk in proxy.empty_stream()]
    assert chunks == []

    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.RESULT]
    assert events[1].result == {"stream": True, "chunks": 0}


@pytest.mark.asyncio
async def test_proxy_regular_method_unchanged():
    events = []

    def event_handler(event: Event):
        events.append(event)

    obj = DummyStreamer()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    result = await proxy.regular_method()
    assert result == "hello"

    event_types = [e.event_type for e in events]
    assert event_types == [EventType.CALL, EventType.RESULT]
    assert events[1].result == "hello"


@pytest.mark.asyncio
async def test_proxy_llm_generate_stream():
    """The flagship case: LLMProtocol.generate_stream through the observability proxy."""
    events = []

    def event_handler(event: Event):
        events.append(event)

    llm = MockLLM({"responses": [{"content": "Hello World"}], "streaming_chunk_size": 5})
    proxy = Proxy(llm, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")

    messages = [LLMMessage.user("Hi")]
    chunks = [chunk async for chunk in proxy.generate_stream(messages)]

    assert "".join(chunks) == "Hello World"
    yield_events = [e for e in events if e.event_type == EventType.YIELD]
    # Every chunk that crossed the module boundary is on the event log
    assert [e.result for e in yield_events] == chunks
    assert events[0].event_type == EventType.CALL
    assert events[-1].event_type == EventType.RESULT
    assert events[-1].result == {"stream": True, "chunks": len(chunks)}
