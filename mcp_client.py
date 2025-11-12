"""
MCP Client for Slackbot
Manages connections to multiple MCP servers
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class MCPManager:
    """Manages multiple MCP server connections"""
    
    def __init__(self):
        self.servers: Dict[str, dict] = {}
        self.sessions: Dict[str, ClientSession] = {}
        
    def register_server(self, name: str, command: str, args: List[str], env: Optional[Dict] = None):
        """Register an MCP server"""
        self.servers[name] = {
            "command": command,
            "args": args,
            "env": env or {}
        }
        logger.info(f"Registered MCP server: {name}")
    
    async def connect_server(self, name: str):
        """Connect to a specific MCP server"""
        if name not in self.servers:
            raise ValueError(f"Server {name} not registered")
        
        server_config = self.servers[name]
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"],
            env=server_config["env"]
        )
        
        try:
            stdio_transport = await stdio_client(server_params)
            session = ClientSession(stdio_transport[0], stdio_transport[1])
            await session.initialize()
            
            self.sessions[name] = session
            logger.info(f"Connected to MCP server: {name}")
            return session
        except Exception as e:
            logger.error(f"Failed to connect to {name}: {e}")
            raise
    
    async def disconnect_server(self, name: str):
        """Disconnect from a specific MCP server"""
        if name in self.sessions:
            await self.sessions[name].close()
            del self.sessions[name]
            logger.info(f"Disconnected from MCP server: {name}")
    
    async def list_tools(self, server_name: str) -> List[Dict]:
        """List available tools from a server"""
        if server_name not in self.sessions:
            await self.connect_server(server_name)
        
        session = self.sessions[server_name]
        tools = await session.list_tools()
        return tools.tools
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a specific server"""
        if server_name not in self.sessions:
            await self.connect_server(server_name)
        
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result
    
    async def list_all_tools(self) -> Dict[str, List[Dict]]:
        """List all tools from all registered servers"""
        all_tools = {}
        for server_name in self.servers:
            try:
                tools = await self.list_tools(server_name)
                all_tools[server_name] = tools
            except Exception as e:
                logger.error(f"Failed to list tools from {server_name}: {e}")
                all_tools[server_name] = []
        return all_tools
    
    async def cleanup(self):
        """Disconnect from all servers"""
        for name in list(self.sessions.keys()):
            await self.disconnect_server(name)


# Global MCP manager instance
mcp_manager = MCPManager()


def setup_mcp_servers():
    """Setup and register all MCP servers"""
    import os
    
    # 1. Filesystem MCP - Access local files
    mcp_manager.register_server(
        name="filesystem",
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            "/tmp/slackbot-files"  # Allowed directory
        ]
    )
    
    # 2. Memory MCP - Persistent memory
    mcp_manager.register_server(
        name="memory",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"]
    )
    
    # 3. GitHub MCP - If you have a token
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        mcp_manager.register_server(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": github_token}
        )
    
    # 4. Custom Kubernetes MCP - Your own server!
    mcp_manager.register_server(
        name="kubernetes",
        command="python",
        args=["/path/to/k8s_mcp_server.py"]
    )
    
    logger.info("MCP servers registered")


# Async wrapper for use in sync Flask context
def run_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]):
    """Synchronous wrapper for MCP tool calls"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            mcp_manager.call_tool(server_name, tool_name, arguments)
        )
        return result
    finally:
        loop.close()


def list_mcp_tools():
    """Synchronous wrapper to list all MCP tools"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(mcp_manager.list_all_tools())
        return result
    finally:
        loop.close()