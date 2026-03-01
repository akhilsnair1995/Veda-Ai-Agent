# mcp/server_base.py
# The foundation for building any MCP server.
# Inherit from MCPServer and define your tools.
# It handles all protocol boilerplate automatically.

import json
import sys
import inspect
from typing import Any, Callable
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable
    
    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters
        }


@dataclass
class Resource:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"
    fn: Callable = None

    def to_schema(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


class MCPServer:
    """
    Base class for building MCP servers.
    
    To build a server:
    1. Inherit from this class
    2. Define tools with add_tool()
    3. Call server.run() to start
    
    The server communicates via stdin/stdout JSON-RPC.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, Tool] = {}
        self._resources: dict[str, Resource] = {}
        self._msg_id = 0

    def add_tool(self, 
                 name: str, 
                 description: str, 
                 parameters: dict,
                 fn: Callable):
        """Register a tool with this server."""
        self._tools[name] = Tool(
            name=name, 
            description=description,
            parameters=parameters,
            fn=fn
        )

    def add_resource(self,
                     uri: str,
                     name: str, 
                     description: str,
                     fn: Callable,
                     mime_type: str = "text/plain"):
        """Register a resource with this server."""
        self._resources[uri] = Resource(
            uri=uri,
            name=name,
            description=description,
            fn=fn,
            mime_type=mime_type
        )

    def _send(self, message: dict):
        """Write a JSON-RPC message to stdout."""
        sys.stdout.write(json.dumps(message) + "\n")
        sys.stdout.flush()

    def _send_response(self, id: Any, result: Any):
        self._send({
            "jsonrpc": "2.0",
            "id": id,
            "result": result
        })

    def _send_error(self, id: Any, code: int, message: str):
        self._send({
            "jsonrpc": "2.0",
            "id": id,
            "error": {"code": code, "message": message}
        })

    def _handle_initialize(self, id: Any, params: dict):
        self._send_response(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        })

    def _handle_tools_list(self, id: Any):
        self._send_response(id, {
            "tools": [t.to_schema() for t in self._tools.values()]
        })

    def _handle_tools_call(self, id: Any, params: dict):
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self._tools:
            self._send_error(id, -32601, f"Tool not found: {tool_name}")
            return

        try:
            # Inspection check to see if we should pass brain
            sig = inspect.signature(self._tools[tool_name].fn)
            if 'brain' in sig.parameters:
                # This would need the brain object, but base server doesn't have it.
                # Usually MCP tools are stateless.
                result = self._tools[tool_name].fn(**arguments)
            else:
                result = self._tools[tool_name].fn(**arguments)
                
            self._send_response(id, {
                "content": [{"type": "text", "text": str(result)}]
            })
        except Exception as e:
            self._send_response(id, {
                "content": [{
                    "type": "text", 
                    "text": f"Tool error: {e}"
                }],
                "isError": True
            })

    def _handle_resources_list(self, id: Any):
        self._send_response(id, {
            "resources": [r.to_schema() for r in self._resources.values()]
        })

    def _handle_resources_read(self, id: Any, params: dict):
        uri = params.get("uri")
        if uri not in self._resources:
            self._send_error(id, -32601, f"Resource not found: {uri}")
            return

        try:
            content = self._resources[uri].fn()
            self._send_response(id, {
                "contents": [{
                    "uri": uri,
                    "mimeType": self._resources[uri].mime_type,
                    "text": str(content)
                }]
            })
        except Exception as e:
            self._send_error(id, -32603, f"Resource error: {e}")

    def run(self):
        """
        Start the MCP server. Reads from stdin, writes to stdout.
        Runs until stdin closes or process is killed.
        """
        sys.stderr.write(f"MCP Server '{self.name}' starting...\n")
        sys.stderr.flush()

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue

            method = message.get("method", "")
            msg_id = message.get("id")
            params = message.get("params", {})

            # Route to handler
            if method == "initialize":
                self._handle_initialize(msg_id, params)
            elif method == "notifications/initialized":
                pass  # Acknowledge, no response needed
            elif method == "tools/list":
                self._handle_tools_list(msg_id)
            elif method == "tools/call":
                self._handle_tools_call(msg_id, params)
            elif method == "resources/list":
                self._handle_resources_list(msg_id)
            elif method == "resources/read":
                self._handle_resources_read(msg_id, params)
            elif method == "ping":
                self._send_response(msg_id, {})
            else:
                if msg_id:
                    self._send_error(
                        msg_id, -32601, 
                        f"Method not found: {method}"
                    )
