from quart import Quart
from quart_cors import cors
from typing import Type

import importlib

from xaibo import Xaibo, AgentConfig

def get_class_by_path(path: str) -> Type:
    parts = path.split('.')
    pkg = '.'.join(parts[:-1])
    cls = parts[-1]
    package = importlib.import_module(pkg)
    clazz = getattr(package, cls)
    return clazz

class XaiboWebServer:
    def __init__(self, xaibo: Xaibo, adapters: list[str], agent_dir: str, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.xaibo = xaibo
        self.app = Quart("XaiboWebServer")
        self.app = cors(self.app, allow_origin="*")
        self.agent_dir = agent_dir
        self.host = host
        self.port = port
        self.configs = {}
        self.watcher_task = None

        for adapter in adapters:
            clazz = get_class_by_path(adapter)
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

    def start(self) -> None:
        from watchfiles import awatch
        import asyncio

        async def watch_config_files():
            try:
                async for _ in awatch(self.agent_dir):
                    self._load_configs()
            except asyncio.CancelledError:
                pass

        @self.app.before_serving
        async def start_file_watcher():
            self.watcher_task = asyncio.create_task(watch_config_files())

        @self.app.after_serving
        async def cleanup():
            if self.watcher_task:
                self.watcher_task.cancel()
                try:
                    await self.watcher_task
                except asyncio.CancelledError:
                    pass

        self.app.run(host=self.host, port=self.port)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-dir", dest="agent_dir", default="./agents", action="store")
    parser.add_argument("--adapter", dest="adapters", default=[], action="append",
                        help="Python Package path to an API adapter class (e.g. xaibo.server.adapters.OpenAiApiAdapter)")
    parser.add_argument("--host", dest="host", default="127.0.0.1", action="store",
                        help="Host address to bind the server to")
    parser.add_argument("--port", dest="port", default=8000, type=int, action="store",
                        help="Port to run the server on")

    args = parser.parse_args()

    xaibo = Xaibo()

    server = XaiboWebServer(xaibo, args.adapters, args.agent_dir, args.host, args.port)
    server.start()