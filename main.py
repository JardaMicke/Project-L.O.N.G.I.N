#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Longin AI Systems - Main Entry Point

This module serves as the main entry point for the Longin AI Systems application.
It initializes the core components and starts the application.

Tento modul slouží jako hlavní vstupní bod pro aplikaci Longin AI Systems.
Inicializuje základní komponenty a spouští aplikaci.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any

# Core implementations
from src.longin_core.storage import StorageManager
from src.longin_core.event_bus import LONGINEventBus
from src.longin_core.mcp import MCPServer
from src.longin_core.orchestrator import CoreOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main entry point for the application.
    
    Hlavní vstupní bod aplikace.
    """
    try:
        # ---- minimal runtime configuration (replace with ConfigManager later) ----
        config: Dict[str, Any] = {
            "redis_store": {"url": os.getenv("REDIS_URL", "redis://localhost:6379/0")},
            "postgres_store": {
                "user": os.getenv("POSTGRES_USER", "longin"),
                "password": os.getenv("POSTGRES_PASSWORD", "longin_dev_password"),
                "database": os.getenv("POSTGRES_DB", "longin_db"),
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
            },
            "postgres_vector_store": {
                "user": os.getenv("POSTGRES_USER", "longin"),
                "password": os.getenv("POSTGRES_PASSWORD", "longin_dev_password"),
                "database": os.getenv("POSTGRES_DB", "longin_db"),
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
            },
            "json_store": {"base_path": "./data/json_store"},
            "agents": {},  # agent-specific configs can be injected here
        }

        # ---- instantiate core components ----
        storage_manager = StorageManager(config, logger)
        event_bus = LONGINEventBus(logger, config.get("event_bus", {}))
        mcp_server = MCPServer(
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8000")),
            plugin_dir="src/longin_core/mcp/plugins",
            logger=logger,
        )
        orchestrator = CoreOrchestrator(
            config=config,
            logger=logger,
            storage_manager=storage_manager,
            event_bus=event_bus,
            mcp_server=mcp_server,
        )

        # ---- run lifecycle ----
        async def _run() -> None:
            started = await orchestrator.start()
            if not started:
                logger.error("CoreOrchestrator failed to start.")
                return
            logger.info("Longin AI Systems is running.")
            # Keep running until cancelled
            await asyncio.Future()  # run forever

        await _run()
    except KeyboardInterrupt:
        logger.info("Longin AI Systems shutdown by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        # ensure graceful shutdown of orchestrator
        try:
            await orchestrator.stop()  # type: ignore[arg-type]
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        logger.info("Longin AI Systems shutdown complete")
    asyncio.run(main())

if __name__ == "__main__":
    main()
