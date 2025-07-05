import logging
import asyncio
from typing import Dict, Any, Optional, List

from ..storage import StorageManager
from ..event_bus import LONGINEventBus
from ..base import LonginModule
from ..mcp import MCPServer
from ..lmstudio.client import AsyncLMStudioClient  # NEW
from ..agents.mini_agent import MiniAgent          # NEW


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
        # legacy core agent registry (string-keyed, e.g. "coding_flow_boss")
        self.agents: Dict[str, Any] = {}
        # registry for new MiniAgent objects keyed by numeric id
        self.mini_agents: Dict[int, MiniAgent] = {}

        # LM-Studio client placeholder (lazy-created in start())
        self.lmstudio_client: Optional[AsyncLMStudioClient] = None
        
        self.logger.info("CoreOrchestrator initialized.")

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
        Loads and initializes instances of key agents (CodingFlowBossAgent, ContextMasterAgent, etc.).
        Registers them in self.agents and connects them to EventBus/MCP server as needed.

        Returns:
            bool: True if all agents were loaded successfully, False otherwise.

        Načte a inicializuje instance klíčových agentů (CodingFlowBossAgent, ContextMasterAgent, atd.).
        Zaregistruje je do self.agents a propojí je s EventBusem/MCP serverem podle potřeby.

        Vrací:
            bool: True, pokud byli všichni agenti úspěšně načteni, jinak False.
        """
        self.logger.info("Loading core agents (placeholder implementation)...")
        
        # Placeholder for agent initialization
        # TODO: Implement actual agent loading logic
        # Example:
        # self.agents["coding_flow_boss"] = CodingFlowBossAgent(self.config.get("agents", {}).get("coding_flow_boss", {}), self.logger)
        # self.agents["context_master"] = ContextMasterAgent(self.config.get("agents", {}).get("context_master", {}), self.logger)
        
        # Placeholder for agent connection to EventBus
        # TODO: Implement actual agent-EventBus connection logic
        # Example:
        # await self.event_bus.subscribe("code_request", self.agents["coding_flow_boss"].handle_code_request, "coding_flow_boss")
        
        self.logger.info("Core agents loaded successfully (placeholder).")
        return True

    # ------------------------------------------------------------------
    # Mini-agent initialisation & lifecycle
    # ------------------------------------------------------------------
    async def _init_mini_agents(self) -> None:
        """
        Create/restore MiniAgent instances based on configuration.
        The config must contain a ``mini_agents`` list, each item having at
        least ``id``, ``model_path`` and ``dataset_path``.
        """
        cfg_agents: List[Dict[str, Any]] = self.config.get("mini_agents", [])
        if not cfg_agents:
            self.logger.warning("No mini_agents configuration found.")
            return

        # Create shared LM-Studio client once
        if self.lmstudio_client is None:
            lm_cfg = self.config.get("lmstudio", {})
            self.lmstudio_client = AsyncLMStudioClient(
                base_url=lm_cfg.get("host", "http://localhost:1234"),
                api_key=lm_cfg.get("api_key"),
            )

        for spec in cfg_agents:
            try:
                agent_id: int = spec["id"]
                # Try to restore previous state
                try:
                    agent = MiniAgent.load_state(agent_id)
                    self.logger.info(f"Loaded MiniAgent state for id={agent_id}")
                except FileNotFoundError:
                    agent = MiniAgent(
                        id=agent_id,
                        name=spec.get("name", f"agent_{agent_id}"),
                        model_path=spec["model_path"],
                        dataset_path=spec["dataset_path"],
                    )
                    agent.save_state()
                    self.logger.info(f"Created new MiniAgent id={agent_id}")

                # Dependency injection
                agent.lmstudio_client = self.lmstudio_client
                agent.event_bus = self.event_bus

                # Subscribe to bus events (fire-and-forget)
                await agent.subscribe_to_events()  # noqa: E501

                self.mini_agents[agent_id] = agent
            except Exception as exc:
                self.logger.error(
                    "Failed to initialise MiniAgent from spec %s : %s", spec, exc, exc_info=True
                )

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

            # Initialise mini-agents
            self.logger.info("Initialising mini_agents...")
            await self._init_mini_agents()
            
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

            # Persist mini-agents & close LM-Studio client
            for agent in self.mini_agents.values():
                try:
                    agent.save_state()
                except Exception as exc:
                    self.logger.warning("Failed to save agent %s : %s", agent.id, exc)
            if self.lmstudio_client:
                await self.lmstudio_client.close()
            
            self.logger.info("CoreOrchestrator stopped successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Error during CoreOrchestrator shutdown: {e}", exc_info=True)
            return False
