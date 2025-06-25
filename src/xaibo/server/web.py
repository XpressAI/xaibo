from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from typing import Type, Optional
import importlib
import uvicorn
import asyncio
from watchfiles import awatch

from xaibo import Xaibo, AgentConfig
from pathlib import Path

def get_class_by_path(path: str) -> Type:
    parts = path.split('.')
    pkg = '.'.join(parts[:-1])
    cls = parts[-1]
    package = importlib.import_module(pkg)
    clazz = getattr(package, cls)
    return clazz

class XaiboWebServer:
    def __init__(self, xaibo: Xaibo, adapters: list[str], agent_dir: str, host: str = "127.0.0.1", port: int = 8000, debug: bool = False, openai_api_key: Optional[str] = None, mcp_api_key: Optional[str] = None) -> None:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            self.watcher_task = asyncio.create_task(self.watch_config_files())
            yield
            self.watcher_task.cancel()
            try:
                await self.watcher_task
            except asyncio.CancelledError:
                pass


        self.xaibo = xaibo
        self.app = FastAPI(title="XaiboWebServer", lifespan=lifespan)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.agent_dir = agent_dir
        self.host = host
        self.port = port
        self.configs = {}
        self.watcher_task = None
        self.openai_api_key = openai_api_key
        self.mcp_api_key = mcp_api_key

        if debug:
            from xaibo.server.adapters.ui import UIDebugTraceEventListener
            adapters.append("xaibo.server.adapters.UiApiAdapter")
            self.xaibo.register_event_listener("", UIDebugTraceEventListener(Path("./debug")).handle_event)


        for adapter in adapters:
            clazz = get_class_by_path(adapter)
            # Pass API keys to appropriate adapters based on class name
            class_name = clazz.__name__
            if class_name == "OpenAiApiAdapter":
                instance = clazz(self.xaibo, api_key=self.openai_api_key)
            elif class_name == "McpApiAdapter":
                instance = clazz(self.xaibo, api_key=self.mcp_api_key)
            else:
                instance = clazz(self.xaibo)
            instance.adapt(self.app)

        # Initial load of configs
        self._load_configs()
            
    def _load_configs(self) -> None:
        """Load configs and register new/changed agents, unregister removed ones"""
        new_configs = AgentConfig.load_directory(self.agent_dir)
        
        # Unregister removed agents
        for path in set(self.configs.keys()) - set(new_configs.keys()):
            self.xaibo.unregister_agent(self.configs[path].id)
            
        # Register new/changed agents
        for path, config in new_configs.items():
            if path not in self.configs or self.configs[path] != config:
                self.xaibo.register_agent(config)
                
        self.configs = new_configs

    async def watch_config_files(self):
        try:
            async for _ in awatch(self.agent_dir, force_polling=True):
                self._load_configs()
        except asyncio.CancelledError:
            pass

    def start(self) -> None:
        uvicorn.run(self.app, host=self.host, port=self.port)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-dir", dest="agent_dir", default="./agents", action="store")
    parser.add_argument("--adapter", dest="adapters", default=[], action="append",
                        help="Python Package path to an API adapter class (e.g. xaibo.server.adapters.OpenAiApiAdapter, xaibo.server.adapters.McpApiAdapter)")
    parser.add_argument("--host", dest="host", default="127.0.0.1", action="store",
                        help="Host address to bind the server to")
    parser.add_argument("--port", dest="port", default=8000, type=int, action="store",
                        help="Port to run the server on")
    parser.add_argument("--debug-ui", dest="debug", default=False, type=bool, action="store",
                        help="Enable writing debug traces and start web ui")
    parser.add_argument("--openai-api-key", dest="openai_api_key", default=None, action="store",
                        help="API key for OpenAI adapter authentication (optional)")
    parser.add_argument("--mcp-api-key", dest="mcp_api_key", default=None, action="store",
                        help="API key for MCP adapter authentication (optional)")

    args = parser.parse_args()

    xaibo = Xaibo()

    server = XaiboWebServer(xaibo, args.adapters, args.agent_dir, args.host, args.port, args.debug, args.openai_api_key, args.mcp_api_key)
    server.start()