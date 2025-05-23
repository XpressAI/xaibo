# Event System APIs

## Event Listeners

Xaibo provides a comprehensive event system for monitoring agent operations:

### DebugEventListener

**Module:** [`xaibo.primitives.event_listeners.DebugEventListener`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/event_listeners/debug_event_listener.py)

```yaml
modules:
  - module: xaibo.primitives.event_listeners.DebugEventListener
    id: debug-listener
```

**Events Captured:**
- Module method calls and responses
- Tool executions
- LLM interactions
- Memory operations
- Error conditions

### Custom Event Listeners

```python
from xaibo.core.models.events import Event

class CustomEventListener:
    def on_event(self, event: Event) -> None:
        # Handle event
        print(f"Event: {event.type} - {event.data}")
```

## Event Types

- `module.call.start` - Module method call started
- `module.call.end` - Module method call completed
- `module.call.error` - Module method call failed
- `tool.call.start` - Tool execution started
- `tool.call.end` - Tool execution completed
- `llm.generate.start` - LLM generation started
- `llm.generate.end` - LLM generation completed