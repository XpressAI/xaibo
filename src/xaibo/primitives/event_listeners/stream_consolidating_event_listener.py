from typing import Callable

from xaibo.core.models.events import Event, EventType


class StreamConsolidatingEventListener:
    """Folds streamed YIELD events into the closing RESULT.

    Wraps another event handler. YIELD events are buffered per call and not
    forwarded; the closing RESULT or EXCEPTION is forwarded with the buffered
    stream content attached. All other events pass through untouched. Buffers
    are held until the stream's RESULT or EXCEPTION arrives.
    """

    def __init__(self, handler: Callable[[Event], None]):
        """Initialize the listener.

        Args:
            handler: Event handler that receives the consolidated events
        """
        self._handler = handler
        self._streams = {}

    def handle_event(self, event: Event) -> None:
        """Process an event, consolidating streamed chunks.

        Args:
            event: The event to process
        """
        if event.event_type == EventType.YIELD:
            self._streams.setdefault(event.call_id, []).append(event.result)
            return
        if event.event_type == EventType.RESULT:
            chunks = self._streams.pop(event.call_id, None)
            if chunks is not None:
                event = event.model_copy(
                    update={"result": {**event.result, "content": self._join(chunks)}}
                )
        elif event.event_type == EventType.EXCEPTION:
            chunks = self._streams.pop(event.call_id, None)
            if chunks is not None:
                event = event.model_copy(
                    update={"result": {
                        "stream": True,
                        "chunks": len(chunks),
                        "content": self._join(chunks),
                        "incomplete": True,
                    }}
                )
        self._handler(event)

    @staticmethod
    def _join(chunks):
        if all(isinstance(chunk, str) for chunk in chunks):
            return "".join(chunks)
        return chunks
