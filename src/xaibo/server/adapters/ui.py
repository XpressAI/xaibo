from os import PathLike

import strawberry
from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from strawberry.fastapi import GraphQLRouter, BaseContext
from typing import List, Optional, Dict, Union
from dotenv import load_dotenv


from strawberry.scalars import JSON

from xaibo import Xaibo
from xaibo.core import models
import json
from pathlib import Path
from importlib.resources import files


class UiContext(BaseContext):
    def __init__(self, xaibo: Xaibo):
        self.xaibo = xaibo


@strawberry.type
class Agent:
    id: str

@strawberry.type
class ModuleConfig:
    module: str
    id: str
    provides: Optional[List[str]]
    uses: Optional[List[str]]
    config: Optional[JSON]

@strawberry.type
class ExchangeConfig:
    module: Optional[str] = None
    field_name: Optional[str] = None
    protocol: str
    provider: JSON

@strawberry.type
class AgentConfig:
    id: str
    modules: List[ModuleConfig]
    exchange: List[ExchangeConfig]

@strawberry.type
class Event:
    agent_id: str
    event_name: str
    event_type: str
    module_id: str
    module_class: str
    method_name: str
    time: float
    call_id: str
    caller_id: str
    arguments: Optional[JSON]
    result: Optional[JSON]
    exception: Optional[str]

@strawberry.type
class DebugTrace:
    agent_id: str
    events: List[Event]


@strawberry.type
class Query:
    @strawberry.field
    async def list_agents(self, info: strawberry.Info[UiContext]) -> List[Agent]:
        agents = info.context.xaibo.list_agents()
        return [Agent(id=agent_id) for agent_id in agents]
    
    @strawberry.field
    async def agent_config(self, agent_id: str, info: strawberry.Info[UiContext]) -> AgentConfig:
        cfg = info.context.xaibo.get_agent_config(agent_id)
        return AgentConfig(
            id=cfg.id,
            modules=[ModuleConfig(id=m.id, module=m.module, provides=m.provides, uses=m.uses, config=m.config) for m in cfg.modules],
            exchange=[ExchangeConfig(module=e.module, protocol=e.protocol, provider=e.provider) for e in cfg.exchange]
        )

    @strawberry.field
    async def debug_log(self, agent_id: str) -> DebugTrace:
        target_path = Path("./debug") / f"{agent_id}.jsonl"
        events = []
        if target_path.exists():
            lines = target_path.read_text().splitlines()
            events = [Event(**json.loads(line)) for line in lines]
        return DebugTrace(agent_id=agent_id, events=events)

schema = strawberry.Schema(
    query=Query            
)

class UiApiAdapter:
    def __init__(self, xaibo: Xaibo):
        self.xaibo = xaibo
        self.router = APIRouter()

        graphql_router = GraphQLRouter(
            schema,
            context_getter=self.get_context
        )

        self.router.include_router(graphql_router, prefix="/graphql")

        self.static_path = files("xaibo.server.adapters") / "ui" / "static" / "build"

    def adapt(self, app: FastAPI):
        load_dotenv()

        app.include_router(self.router, prefix="/api/ui")
        app.mount("/", StaticFiles(directory=str(self.static_path), html=True), name="ui-static-files")
        @app.middleware("http")
        async def spa_fallback_middleware(request: Request, call_next):
            response = await call_next(request)
            if response.status_code == 404 and "text/html" in request.headers.get("accept", ""):
                # Return SPA index.html for unhandled routes
                return FileResponse(self.static_path / "index.html")
            return response


    def get_context(self) -> UiContext:
        return UiContext(self.xaibo)

class UIDebugTraceEventListener:
    """Event listener that logs all events for debugging purposes."""

    def __init__(self, output_directory: Path):
        """Initialize the debug event listener.

        Args:
            log_level: The logging level to use for event logs (default: logging.DEBUG)
        """
        self.output_directory = output_directory

    def handle_event(self, event: models.Event) -> None:
        """Handle an event by logging it.

        Args:
            event: The event to log
        """
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True)

        target_file = self.output_directory / f"{event.agent_id}.jsonl"
        with target_file.open("a") as f:
            f.write(json.dumps(event.model_dump(), default=repr))
            f.write("\n")