from os import PathLike

import strawberry
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from strawberry.fastapi import GraphQLRouter, BaseContext
from typing import List, Optional, Dict, Union
from dotenv import load_dotenv
from pydantic import BaseModel


from strawberry.scalars import JSON

from xaibo import Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.core import models
from xaibo.primitives.modules.conversation.conversation import SimpleConversation
import json
from pathlib import Path
from importlib.resources import files


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    response: str
    history: List[Dict[str, str]]


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
class ExchangeConfigGQL:
    module: Optional[str] = None
    field_name: Optional[str] = None
    protocol: str
    provider: JSON

@strawberry.type
class AgentConfig:
    id: str
    modules: List[ModuleConfig]
    exchange: List[ExchangeConfigGQL]

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
            exchange=[ExchangeConfigGQL(module=e.module, protocol=e.protocol, provider=e.provider) for e in cfg.exchange]
        )

    @strawberry.field
    async def debug_log(self, agent_id: str) -> DebugTrace:
        target_path = Path("./debug") / f"{agent_id}.jsonl"
        events = []
        if target_path.exists():
            lines = target_path.read_text().splitlines()
            events = [Event(**json.loads(line)) for line in lines]
        return DebugTrace(agent_id=agent_id, events=events)

@strawberry.type
class Mutation:
    @strawberry.mutation
    def clear_log(self, agent_id: str) -> DebugTrace:
        target_path = Path("./debug") / f"{agent_id}.jsonl"
        events = []
        if target_path.exists():
            target_path.unlink()
        return DebugTrace(agent_id=agent_id, events=events)

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
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

        # REST endpoint for chat
        @self.router.post("/chat/{agent_id}", response_model=ChatResponse)
        async def chat(agent_id: str, request: ChatRequest) -> ChatResponse:
            try:
                # Convert history to SimpleConversation format
                conversation = SimpleConversation.from_openai_messages(request.history)

                # Get agent with conversation history injected via ConfigOverrides
                agent = self.xaibo.get_agent_with(agent_id, ConfigOverrides(
                    instances={
                        '__conversation_history__': conversation
                    },
                    exchange=[ExchangeConfig(
                        protocol='ConversationHistoryProtocol',
                        provider='__conversation_history__'
                    )]
                ))

                # Call agent.handle_text to get response
                response = await agent.handle_text(request.message, entry_point='__entry__')

                # Build updated history with assistant response
                updated_history = list(request.history)
                # Add user's message
                updated_history.append({"role": "user", "content": request.message})
                # Add assistant's response
                updated_history.append({"role": "assistant", "content": response.text or ""})

                return ChatResponse(
                    response=response.text or "",
                    history=updated_history
                )
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

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