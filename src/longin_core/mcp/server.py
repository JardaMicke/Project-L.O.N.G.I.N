import logging
import asyncio
import importlib
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Optional dependency – `websockets` is lightweight and pure-python.
# If it's missing we will log a warning and skip WS startup.
try:
    import websockets
except ModuleNotFoundError:  # pragma: no cover
    websockets = None


class MCPServer:
    """
    Micro-Agent Communication Protocol (MCP) Server for Longin AI Systems.
    Manages dynamic loading of plugins and routing of tool requests.

    Server komunikačního protokolu mikro-agentů (MCP) pro systémy Longin AI.
    Spravuje dynamické načítání pluginů a směrování požadavků na nástroje.
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
        self.ws_server: Optional["websockets.server.Serve"] = None  # WebSocket server instance

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
        Starts the MCP Server, loading plugins and initializing communication channels.

        Spouští MCP Server, načítá pluginy a inicializuje komunikační kanály.
        """
        self.logger.info("Starting MCP Server...")
        await self.load_plugins()

        # Placeholder for gRPC server startup
        self.logger.info(f"gRPC server starting on {self.host}:{self.port} (placeholder)")

        # Basic WebSocket server startup (JSON RPC-style)
        if websockets:
            self.ws_server = await websockets.serve(
                self._ws_handler,
                self.host,
                self.port,
            )
            self.logger.info(f"WebSocket server listening on ws://{self.host}:{self.port}")
        else:
            self.logger.warning(
                "websockets library not installed – WebSocket interface disabled."
            )

        self.logger.info("MCP Server started successfully.")

    # ------------------------------------------------------------------
    # WebSocket handling
    # ------------------------------------------------------------------
    async def _ws_handler(self, websocket):  # type: ignore[valid-type]
        """
        Minimal JSON-RPC style handler:
        Expect messages like: {\"tool\": \"file.read\", \"args\": {\"path\": \"README.md\"}}
        """
        async for message in websocket:
            try:
                request = json.loads(message)
                tool_name = request.get("tool")
                args = request.get("args", {}) or {}
                if not tool_name:
                    await websocket.send(
                        json.dumps({"success": False, "error": "Missing 'tool' field"})
                    )
                    continue
                response = await self.handle_request(tool_name, args)
                await websocket.send(json.dumps(response))
            except Exception as e:  # noqa: BLE001
                self.logger.error("WebSocket handler error: %s", e, exc_info=True)
                await websocket.send(json.dumps({"success": False, "error": str(e)}))

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
            result = await tool_func(args)  # Assuming tool_func is an async method
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"Error executing tool '{tool_name}': {e}")
            return {"success": False, "error": str(e)}

    async def stop(self):
        """
        Stops the MCP Server and cleans up resources.

        Zastavuje MCP Server a uvolňuje zdroje.
        """
        self.logger.info("Stopping MCP Server...")
        # Placeholder for actual server shutdown logic
        self.logger.info("gRPC server shutting down (placeholder)")

        # Gracefully shut down WebSocket server if running
        if self.ws_server:
            self.logger.info("WebSocket server shutting down...")
            self.ws_server.close()
            try:
                await self.ws_server.wait_closed()
            except Exception:  # noqa: BLE001
                pass
            self.logger.info("WebSocket server shut down.")

        self.logger.info("MCP Server stopped.")
