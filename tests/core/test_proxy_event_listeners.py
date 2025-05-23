import pytest

from xaibo.core.exchange import Proxy
from xaibo.core.models.events import Event, EventType

class DummyClass:
    async def test_method(self, arg1, arg2=None):
        return f"{arg1}-{arg2}"
    
    async def another_method(self):
        return "hello"

@pytest.mark.asyncio
async def test_proxy_event_listeners():
    events = []
    
    def event_handler(event: Event):
        events.append(event)
        
    obj = DummyClass()
    proxy = Proxy(obj, event_listeners=[("", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")
    
    # Test method call events
    result = await proxy.test_method("foo", arg2="bar")
    assert result == "foo-bar"
    
    # Should have generated 2 events (call and result)
    assert len(events) == 2

    call_event = events[0]
    assert call_event.event_type == EventType.CALL
    assert call_event.module_class == "DummyClass"
    assert call_event.method_name == "test_method"
    assert call_event.arguments == {"args": ("foo",), "kwargs": {"arg2": "bar"}}
    assert call_event.agent_id == "test-agent"
    
    result_event = events[1]
    assert result_event.event_type == EventType.RESULT
    assert result_event.module_class == "DummyClass" 
    assert result_event.method_name == "test_method"
    assert result_event.result == "foo-bar"
    assert result_event.call_id == call_event.call_id
    assert result_event.agent_id == "test-agent"

@pytest.mark.asyncio
async def test_proxy_event_filtering():
    events = []
    
    def event_handler(event: Event):
        events.append(event)
        
    obj = DummyClass()
    # Only listen for test_method events
    proxy = Proxy(obj, event_listeners=[(f"{DummyClass.__module__}.DummyClass.test_method", event_handler)], agent_id="test-agent", caller_id="test-caller", module_id="test-module")
    
    await proxy.test_method("foo")  # Should generate events
    await proxy.another_method()    # Should not generate events
    
    assert len(events) == 2  # Only test_method call+result
    assert all(e.method_name == "test_method" for e in events)
    assert all(e.agent_id == "test-agent" for e in events)

@pytest.mark.asyncio
async def test_multiple_event_listeners():
    events1 = []
    events2 = []
    
    def handler1(event: Event):
        events1.append(event)
        
    def handler2(event: Event):
        events2.append(event)
        
    obj = DummyClass()
    proxy = Proxy(obj, event_listeners=[
        (f"{DummyClass.__module__}.DummyClass.test_method", handler1),
        (f"{DummyClass.__module__}.DummyClass.another_method", handler2)
    ], agent_id="test-agent", caller_id="test-caller", module_id="test-module")
    
    await proxy.test_method("foo")
    await proxy.another_method()
    
    assert len(events1) == 2  # test_method call+result
    assert len(events2) == 2  # another_method call+result
    assert all(e.method_name == "test_method" for e in events1)
    assert all(e.method_name == "another_method" for e in events2)
    assert all(e.agent_id == "test-agent" for e in events1)
    assert all(e.agent_id == "test-agent" for e in events2)
