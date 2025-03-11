import logging
from typing import Optional
from xaibo.core.models.events import Event, EventType

class DebugEventListener:
    """Event listener that logs all events for debugging purposes."""
    
    def __init__(self, log_level: int = logging.DEBUG):
        """Initialize the debug event listener.
        
        Args:
            log_level: The logging level to use for event logs (default: logging.DEBUG)
        """
        self.logger = logging.getLogger("xaibo.events")
        self.logger.setLevel(log_level)
        self.log_level = log_level
    
    def handle_event(self, event: Event) -> None:
        """Handle an event by logging it.
        
        Args:
            event: The event to log
        """        
        if event.event_type == EventType.CALL:
            self.logger.log(
                self.log_level,
                f"CALL [{event.call_id}] {event.module_class}.{event.method_name}() - Args: {event.arguments}"
            )
        elif event.event_type == EventType.RESULT:
            self.logger.log(
                self.log_level,
                f"RESULT [{event.call_id}] {event.module_class}.{event.method_name}() -> {event.result}"
            )
        else:
            self.logger.log(
                self.log_level,
                f"EVENT {event.event_name} - {event}"
            )

def register_debug_listener(registry, prefix: str = "", agent_id: Optional[str] = None, log_level: int = logging.DEBUG) -> None:
    """Register a debug event listener with the registry.
    
    Args:
        registry: The registry to register the listener with
        prefix: Event prefix to listen for (default: "" for all events)
        agent_id: Optional agent ID to filter events for
        log_level: The logging level to use for event logs (default: logging.DEBUG)
    """
    logging.basicConfig()
    listener = DebugEventListener(log_level=log_level)
    registry.register_event_listener(prefix, listener.handle_event, agent_id)
