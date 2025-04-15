from enum import Enum
from typing import Any

from pydantic import BaseModel


class EventType(str, Enum):
    CALL = "call"
    RESULT = "result"
    EXCEPTION = "exception"


class Event(BaseModel):
    agent_id: str
    event_name: str
    event_type: EventType
    module_id: str
    module_class: str
    method_name: str
    time: float
    call_id: str
    caller_id: str
    arguments: dict[str, Any] | None = None
    result: Any | None = None
    exception: str | None = None
