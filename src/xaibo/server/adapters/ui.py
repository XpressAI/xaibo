import strawberry
from fastapi import FastAPI, APIRouter
from strawberry.fastapi import GraphQLRouter, BaseContext
from typing import List, Optional, Dict

from strawberry.scalars import JSON

from xaibo import Xaibo

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
    module: str
    protocol: str
    provider: str

@strawberry.type
class AgentConfig:
    id: str
    modules: List[ModuleConfig]
    exchange: List[ExchangeConfig]


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

    def adapt(self, app: FastAPI):
        app.include_router(self.router, prefix="/api/ui")

    def get_context(self) -> UiContext:
        return UiContext(self.xaibo)
