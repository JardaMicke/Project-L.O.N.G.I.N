import logging
import asyncio
import importlib
import os
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class MCPRequest(BaseModel):
    """
    Pydantic model for validating incoming MCP requests.
    """
    tool_name: str
    args: Dict[str, Any] = {}


class MCPServer:
    """
    Micro-Agent Communication Protocol (MCP) Server for Longin AI Systems.
    Manages dynamic loading of plugins and routing of tool requests via a FastAPI server.

    Server komunikačního protokolu mikro-agentů (MCP) pro systémy Longin AI.
    Spravuje dynamické načítání pluginů a směrování požadavků na nástroje přes FastAPI server.
    """

    def __init__(self, host: str, port: int, plugin_dir: str, logger: logging.Logger):
        """
        Initializes the MCP Server.

        Args:
            host (str): The host address for the server.
            port (int): The port number for the server.
            plugin_dir (str): Directory where MCP plugins are located.
            logger (logging.Logger): Logger instance for the server.

        Inicializuje MCP Server.

        Argumenty:
            host (str): Adresa hostitele pro server.
            port (int): Číslo portu pro server.
            plugin_dir (str): Adresář, kde se nacházejí MCP pluginy.
            logger (logging.Logger): Instance loggeru pro server.
        """
        self.host = host
        self.port = port
        self.plugin_dir = Path(plugin_dir)
        self.logger = logger
        self.plugins: Dict[str, Any] = {}  # Stores plugin instances
        self.tools: Dict[str, Any] = {}  # Stores callable tool methods
        
        self.app = FastAPI(
            title="Longin MCP Server",
            description="Micro-Agent Communication Protocol Server",
            version="0.1.0"
        )
        self._server_task: Optional[asyncio.Task] = None
        self._setup_routes()

    def _setup_routes(self):
        """Sets up the API routes for the FastAPI application."""
        
        @self.app.post("/mcp", summary="Execute an MCP tool")
        async def mcp_endpoint(request: MCPRequest):
            """
            Receives a tool execution request and routes it to the appropriate handler.
            """
            result = await self.handle_request(request.tool_name, request.args)
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("error", "Tool execution failed"))
            return result

        @self.app.get("/tools", summary="List available tools")
        async def list_tools():
            """
            Returns a list of all registered tool names.
            """
            return {"tools": list(self.tools.keys())}

    async def load_plugins(self):
        """
        Dynamically loads plugins from the specified plugin directory.
        Each plugin module is expected to contain a class ending with 'Plugin'.

        Dynamicky načítá pluginy ze zadaného adresáře pluginů.
        Očekává se, že každý modul pluginu bude obsahovat třídu končící na 'Plugin'.
        """
        self.logger.info(f"Loading plugins from {self.plugin_dir}...")
        if not self.plugin_dir.is_dir():
            self.logger.warning(f"Plugin directory {self.plugin_dir} not found.")
            return

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(
                        module_name, self.plugin_dir / filename
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Find and instantiate the plugin class
                        for attr_name in dir(module):
                            if attr_name.endswith("Plugin") and attr_name != "Plugin":
                                plugin_class = getattr(module, attr_name)
                                if isinstance(plugin_class, type):  # Ensure it's a class
                                    plugin_instance = plugin_class()
                                    plugin_name = module_name.replace("_plugin", "")
                                    self.plugins[plugin_name] = plugin_instance
                                    self.logger.info(f"Loaded plugin: {plugin_name}")

                                    # Register tools
                                    if hasattr(plugin_instance, "tools") and isinstance(
                                        plugin_instance.tools, dict
                                    ):
                                        for tool_name, tool_func in plugin_instance.tools.items():
                                            full_tool_name = f"{plugin_name}.{tool_name}"
                                            self.tools[full_tool_name] = tool_func
                                            self.logger.info(
                                                f"  Registered tool: {full_tool_name}"
                                            )
                                    break
                except Exception as e:
                    self.logger.error(f"Failed to load plugin {module_name}: {e}")

    async def start(self):
        """
        Starts the MCP Server, loading plugins and running the FastAPI application with uvicorn.

        Spouští MCP Server, načítá pluginy a spouští FastAPI aplikaci pomocí uvicorn.
        """
        self.logger.info("Starting MCP Server...")
        await self.load_plugins()

        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        
        self._server_task = asyncio.create_task(server.serve())
        self.logger.info(f"MCP Server (FastAPI) started successfully on http://{self.host}:{self.port}")

    async def handle_request(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles an incoming MCP request by executing the specified tool.

        Args:
            tool_name (str): The full name of the tool to execute (e.g., "file.read").
            args (dict): Arguments to pass to the tool's execute method.

        Returns:
            dict: A dictionary containing the result of the tool execution or an error message.

        Zpracovává příchozí požadavek MCP spuštěním zadaného nástroje.

        Argumenty:
            tool_name (str): Celé jméno nástroje ke spuštění (např. "file.read").
            args (dict): Argumenty, které se mají předat metodě execute nástroje.

        Vrací:
            dict: Slovník obsahující výsledek spuštění nástroje nebo chybovou zprávu.
        """
        self.logger.debug(f"Handling request for tool: {tool_name} with args: {args}")
        if tool_name not in self.tools:
            self.logger.warning(f"Tool '{tool_name}' not found.")
            return {"success": False, "error": f"Tool '{tool_name}' not found"}

        tool_func = self.tools[tool_name]
        try:
            # Assuming tool_func is an async method/function that accepts a dict of args
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(args)
            else:
                result = tool_func(args)
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def stop(self):
        """
        Stops the MCP Server and cleans up resources.

        Zastavuje MCP Server a uvolňuje zdroje.
        """
        if self._server_task and not self._server_task.done():
            self.logger.info("Stopping MCP Server (FastAPI)...")
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                self.logger.info("MCP Server task has been cancelled.")
            finally:
                self._server_task = None
                self.logger.info("MCP Server stopped.")
        else:
            self.logger.info("MCP Server is not running.")
