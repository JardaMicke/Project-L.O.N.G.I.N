import logging
import asyncio
import inspect
import pkgutil
import importlib
import re
from typing import Dict, Any, Optional, List

from .. import agents as agents_package
from ..storage import StorageManager
from ..event_bus import LONGINEventBus
from ..base import LonginModule
from ..mcp import MCPServer


class CoreOrchestrator:
    """
    Core orchestrator for the Longin AI Systems.
    Manages modules, agents, and coordinates system-wide operations.

    Hlavní orchestrátor pro systémy Longin AI.
    Spravuje moduly, agenty a koordinuje operace v celém systému.
    """

    def __init__(
        self,
        config: dict,
        logger: logging.Logger,
        storage_manager: StorageManager,
        event_bus: LONGINEventBus,
        mcp_server: MCPServer,
    ):
        """
        Initializes the CoreOrchestrator with necessary dependencies.

        Args:
            config (dict): Configuration dictionary for the orchestrator.
            logger (logging.Logger): Logger instance for the orchestrator.
            storage_manager (StorageManager): Instance of the storage manager.
            event_bus (LONGINEventBus): Instance of the event bus.
            mcp_server (MCPServer): Instance of the MCP server.

        Inicializuje CoreOrchestrator s potřebnými závislostmi.

        Argumenty:
            config (dict): Konfigurační slovník pro orchestrátor.
            logger (logging.Logger): Instance loggeru pro orchestrátor.
            storage_manager (StorageManager): Instance správce úložiště.
            event_bus (LONGINEventBus): Instance sběrnice událostí.
            mcp_server (MCPServer): Instance MCP serveru.
        """
        self.config = config
        self.logger = logger
        self.storage_manager = storage_manager
        self.event_bus = event_bus
        self.mcp_server = mcp_server
        
        # Dictionaries to store registered modules and agents
        self.modules: Dict[str, LonginModule] = {}
        self.agents: Dict[str, Any] = {}  # Will be replaced with Agent base class later
        
        self.logger.info("CoreOrchestrator initialized.")

    def _to_snake_case(self, name: str) -> str:
        """Converts a PascalCase string to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    async def register_module(self, module_instance: LonginModule) -> bool:
        """
        Registers a module instance with the orchestrator.

        Args:
            module_instance (LonginModule): The module instance to register.

        Returns:
            bool: True if registration was successful, False otherwise.

        Zaregistruje instanci modulu do orchestrátoru.

        Argumenty:
            module_instance (LonginModule): Instance modulu k registraci.

        Vrací:
            bool: True, pokud byla registrace úspěšná, jinak False.
        """
        module_id = module_instance.module_id
        if module_id in self.modules:
            self.logger.warning(f"Module with ID '{module_id}' is already registered.")
            return False
        
        self.modules[module_id] = module_instance
        self.logger.info(f"Module '{module_id}' registered successfully.")
        return True

    async def load_core_agents(self) -> bool:
        """
        Dynamically loads and initializes instances of all agents from the 'agents' subpackage.
        Registers them in self.agents and prepares them for use.

        Returns:
            bool: True if all agents were loaded successfully, False otherwise.

        Dynamicky načte a inicializuje instance všech agentů z podbalíčku 'agents'.
        Zaregistruje je do self.agents a připraví je k použití.

        Vrací:
            bool: True, pokud byli všichni agenti úspěšně načteni, jinak False.
        """
        self.logger.info("Dynamically loading core agents...")
        
        available_dependencies = {
            "config": self.config,
            "logger": self.logger,
            "storage_manager": self.storage_manager,
            "event_bus": self.event_bus,
            "mcp_client": self.mcp_server,
        }

        try:
            package_path = agents_package.__path__
            prefix = agents_package.__name__ + "."

            for _, module_name, _ in pkgutil.iter_modules(package_path, prefix):
                module = importlib.import_module(module_name)
                
                for class_name, agent_class in inspect.getmembers(module, inspect.isclass):
                    if class_name.endswith("Agent") and agent_class.__module__ == module_name:
                        agent_snake_name = self._to_snake_case(class_name.replace("Agent", ""))
                        self.logger.info(f"Found agent: {class_name} -> {agent_snake_name}")

                        agent_config = self.config.get("agents", {}).get(agent_snake_name, {})
                        
                        constructor_params = inspect.signature(agent_class.__init__).parameters
                        dependencies_to_inject = {}
                        
                        for param_name in constructor_params:
                            if param_name == 'self':
                                continue
                            if param_name == 'config':
                                dependencies_to_inject[param_name] = agent_config
                            elif param_name in available_dependencies:
                                dependencies_to_inject[param_name] = available_dependencies[param_name]
                        
                        self.agents[agent_snake_name] = agent_class(**dependencies_to_inject)
                        self.logger.info(f"Successfully instantiated and registered agent: {class_name}")

        except Exception as e:
            self.logger.error(f"Failed to dynamically load agents: {e}", exc_info=True)
            return False

        self.logger.info(f"Core agents loaded successfully: {list(self.agents.keys())}")
        return True

    async def start(self) -> bool:
        """
        Starts the orchestrator and all its components.
        Initializes storage, event bus, MCP server, loads core agents, and initializes all modules.

        Returns:
            bool: True if startup was successful, False otherwise.

        Spustí orchestrátor a všechny jeho komponenty.
        Inicializuje úložiště, sběrnici událostí, MCP server, načte základní agenty a inicializuje všechny moduly.

        Vrací:
            bool: True, pokud bylo spuštění úspěšné, jinak False.
        """
        self.logger.info("Starting CoreOrchestrator...")
        
        try:
            # Initialize storage
            self.logger.info("Initializing storage...")
            await self.storage_manager.initialize_stores()
            
            # Start event bus
            self.logger.info("Starting event bus...")
            await self.event_bus.start()
            
            # Start MCP server
            self.logger.info("Starting MCP server...")
            await self.mcp_server.start()
            
            # Load core agents
            self.logger.info("Loading core agents...")
            await self.load_core_agents()
            
            # Initialize all registered modules
            self.logger.info("Initializing registered modules...")
            for module_id, module in self.modules.items():
                self.logger.info(f"Initializing module '{module_id}'...")
                success = await module.initialize()
                if not success:
                    self.logger.error(f"Failed to initialize module '{module_id}'.")
                    return False
            
            self.logger.info("CoreOrchestrator started successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Error during CoreOrchestrator startup: {e}", exc_info=True)
            return False

    async def stop(self) -> bool:
        """
        Stops the orchestrator and all its components.
        Cleans up modules, stops MCP server, event bus, and shuts down storage.

        Returns:
            bool: True if shutdown was successful, False otherwise.

        Zastaví orchestrátor a všechny jeho komponenty.
        Vyčistí moduly, zastaví MCP server, sběrnici událostí a vypne úložiště.

        Vrací:
            bool: True, pokud bylo zastavení úspěšné, jinak False.
        """
        self.logger.info("Stopping CoreOrchestrator...")
        
        try:
            # Cleanup all registered modules
            self.logger.info("Cleaning up registered modules...")
            for module_id, module in self.modules.items():
                self.logger.info(f"Cleaning up module '{module_id}'...")
                success = await module.cleanup()
                if not success:
                    self.logger.warning(f"Failed to clean up module '{module_id}' gracefully.")
            
            # Stop MCP server
            self.logger.info("Stopping MCP server...")
            await self.mcp_server.stop()
            
            # Stop event bus
            self.logger.info("Stopping event bus...")
            await self.event_bus.stop()
            
            # Shutdown storage
            self.logger.info("Shutting down storage...")
            await self.storage_manager.shutdown_stores()
            
            self.logger.info("CoreOrchestrator stopped successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Error during CoreOrchestrator shutdown: {e}", exc_info=True)
            return False
