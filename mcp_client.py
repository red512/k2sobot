"""
Simplified MCP Client for Slackbot
Uses subprocess with timeout for reliability
"""
import subprocess
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MCPClient:  # Keep the same name!
    """Simplified MCP Client using subprocess"""
    
    def __init__(self):
        self.servers: Dict[str, dict] = {}
        
    def register_server(self, name: str, command: str, args: List[str], env: Optional[Dict] = None):
        """Register an MCP server"""
        self.servers[name] = {
            "command": command,
            "args": args,
            "env": env or {}
        }
        logger.info(f"✅ Registered MCP server: {name}")
    
    def list_servers(self) -> List[str]:
        """List all registered servers"""
        return list(self.servers.keys())
    
    def _call_mcp_server(self, server_name: str, method: str, params: dict = None, timeout: int = 5) -> dict:
        """Call MCP server via subprocess with timeout"""
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        server_config = self.servers[server_name]
        
        # Build JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            logger.debug(f"Calling {server_name}: {method}")
            
            # Prepare environment
            env = {**os.environ.copy(), **server_config["env"]}
            
            # Call server with timeout
            process = subprocess.Popen(
                [server_config["command"]] + server_config["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            # Send request and wait for response with timeout
            stdout, stderr = process.communicate(
                input=json.dumps(request) + "\n",
                timeout=timeout
            )
            
            if stderr:
                logger.debug(f"Server stderr: {stderr}")
            
            if not stdout.strip():
                raise Exception("Empty response from server")
            
            # Parse response (handle multiple lines)
            lines = stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        response = json.loads(line)
                        if "error" in response:
                            raise Exception(f"Server error: {response['error']}")
                        return response
                    except json.JSONDecodeError:
                        continue
            
            raise Exception("No valid JSON response found")
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception(f"MCP server '{server_name}' timeout after {timeout}s")
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            raise
    
    def list_tools(self, server_name: str) -> List[Dict]:
        """List tools from a server"""
        try:
            response = self._call_mcp_server(server_name, "tools/list")
            
            tools = response.get("result", {}).get("tools", [])
            
            return [
                {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "inputSchema": tool.get("inputSchema", {})
                }
                for tool in tools
            ]
        except Exception as e:
            logger.error(f"Failed to list tools from {server_name}: {e}")
            return []
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on a server"""
        try:
            logger.info(f"Calling tool: {server_name}.{tool_name} with {arguments}")
            
            response = self._call_mcp_server(
                server_name,
                "tools/call",
                {"name": tool_name, "arguments": arguments}
            )
            
            result = response.get("result", {})
            content = result.get("content", [])
            
            if content and len(content) > 0:
                return content[0].get("text", "No result")
            
            return "No result"
            
        except Exception as e:
            logger.error(f"Failed to call {server_name}.{tool_name}: {e}")
            return f"Error: {str(e)}"
    
    def list_all_tools(self) -> Dict[str, List[Dict]]:
        """List all tools from all servers"""
        all_tools = {}
        for server_name in self.servers:
            try:
                tools = self.list_tools(server_name)
                all_tools[server_name] = tools
                if tools:
                    logger.info(f"✅ Listed {len(tools)} tools from {server_name}")
            except Exception as e:
                logger.error(f"Failed to list tools from {server_name}: {e}")
                all_tools[server_name] = []
        return all_tools


# Global MCP client instance
mcp_client = MCPClient()


def setup_mcp_servers():
    """Setup and register MCP servers"""
    
    python_path = sys.executable
    logger.info(f"🐍 Using Python interpreter: {python_path}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"📁 Script directory: {script_dir}")
    
    # 1. Time MCP Server
    time_server_path = os.path.join(script_dir, "time_mcp_server.py")
    if os.path.exists(time_server_path):
        logger.info(f"✅ Found time server file")
        mcp_client.register_server(
            name="time",
            command=python_path,
            args=[time_server_path]
        )
    else:
        logger.error(f"❌ Time server not found: {time_server_path}")
    
    # 2. Joke MCP Server
    joke_server_path = os.path.join(script_dir, "joke_mcp_server.py")
    if os.path.exists(joke_server_path):
        logger.info(f"✅ Found joke server file")
        mcp_client.register_server(
            name="joke",
            command=python_path,
            args=[joke_server_path]
        )
    else:
        logger.error(f"❌ Joke server not found: {joke_server_path}")
    
    registered = mcp_client.list_servers()
    logger.info(f"✅ MCP setup complete. Registered servers: {registered}")
    
    return registered


def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance"""
    return mcp_client