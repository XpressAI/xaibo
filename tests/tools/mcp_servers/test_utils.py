"""
Utilities for managing real MCP servers during testing.
"""

import asyncio
import socket
import subprocess
import sys
import time
import websockets
import aiohttp
from typing import Optional, Tuple
from pathlib import Path


def find_free_port() -> int:
    """Find a free port on localhost"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class MCPServerManager:
    """Manager for starting and stopping real MCP servers during tests"""
    
    def __init__(self):
        self.servers = {}
        self.processes = {}
    
    async def start_stdio_server(self, name: str = "stdio_test") -> Tuple[str, list]:
        """Start a stdio MCP server and return command configuration"""
        server_script = Path(__file__).parent / "stdio_server.py"
        command = [sys.executable, str(server_script)]
        
        self.servers[name] = {
            "type": "stdio",
            "command": command
        }
        
        return name, command
    
    async def start_websocket_server(self, name: str = "ws_test") -> Tuple[str, str, int]:
        """Start a WebSocket MCP server and return connection details"""
        port = find_free_port()
        server_script = Path(__file__).parent / "websocket_server.py"
        
        # Start the server process
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(server_script), "--port", str(port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.processes[name] = process
        
        # Wait for server to start
        await self._wait_for_websocket_server("localhost", port)
        
        url = f"ws://localhost:{port}"
        self.servers[name] = {
            "type": "websocket",
            "url": url,
            "port": port
        }
        
        return name, url, port
    
    async def start_sse_server(self, name: str = "sse_test") -> Tuple[str, str, int]:
        """Start an SSE MCP server and return connection details"""
        port = find_free_port()
        server_script = Path(__file__).parent / "sse_server.py"
        
        # Start the server process
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(server_script), "--port", str(port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.processes[name] = process
        
        # Wait for server to start
        await self._wait_for_http_server("localhost", port)
        
        url = f"http://localhost:{port}"
        self.servers[name] = {
            "type": "sse",
            "url": url,
            "port": port
        }
        
        return name, url, port
    
    async def _wait_for_websocket_server(self, host: str, port: int, timeout: float = 10.0):
        """Wait for WebSocket server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                websocket = await websockets.connect(f"ws://{host}:{port}")
                await websocket.close()
                return
            except (ConnectionRefusedError, OSError):
                await asyncio.sleep(0.1)
        raise TimeoutError(f"WebSocket server on {host}:{port} did not start within {timeout}s")
    
    async def _wait_for_http_server(self, host: str, port: int, timeout: float = 10.0):
        """Wait for HTTP server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{host}:{port}") as response:
                        # Server is responding
                        return
            except (aiohttp.ClientConnectorError, ConnectionRefusedError):
                await asyncio.sleep(0.1)
        raise TimeoutError(f"HTTP server on {host}:{port} did not start within {timeout}s")
    
    async def stop_server(self, name: str):
        """Stop a specific server"""
        if name in self.processes:
            process = self.processes[name]
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            del self.processes[name]
        
        if name in self.servers:
            del self.servers[name]
    
    async def stop_all_servers(self):
        """Stop all managed servers"""
        for name in list(self.servers.keys()):
            await self.stop_server(name)
    
    def get_server_config(self, name: str) -> dict:
        """Get configuration for a server"""
        if name not in self.servers:
            raise ValueError(f"Server {name} not found")
        
        server_info = self.servers[name]
        
        if server_info["type"] == "stdio":
            return {
                "name": name,
                "transport": "stdio",
                "command": server_info["command"]
            }
        elif server_info["type"] == "websocket":
            return {
                "name": name,
                "transport": "websocket",
                "url": server_info["url"]
            }
        elif server_info["type"] == "sse":
            return {
                "name": name,
                "transport": "sse",
                "url": server_info["url"]
            }
        else:
            raise ValueError(f"Unknown server type: {server_info['type']}")


# Global server manager instance for tests
_server_manager = None


def get_server_manager() -> MCPServerManager:
    """Get the global server manager instance"""
    global _server_manager
    if _server_manager is None:
        _server_manager = MCPServerManager()
    return _server_manager


async def cleanup_test_servers():
    """Cleanup function to stop all test servers"""
    global _server_manager
    if _server_manager is not None:
        await _server_manager.stop_all_servers()
        _server_manager = None