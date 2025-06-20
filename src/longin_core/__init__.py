"""
Longin Core - Main package for the Longin AI Systems application.
Longin Core - Hlavní balíček pro aplikaci Longin AI Systems.
"""

__version__ = "0.1.0"

# Public exports
from .event_bus import LONGINEventBus
# Storage layer exports
from .storage import StorageManager, StorageType
# Orchestrator export
from .orchestrator import CoreOrchestrator
# Agents exports
from .agents import (
    CodingFlowBossAgent,
    ContextMasterAgent,
    TestOracleAgent,
    CodeAlchemistAgent,
    VisualValidatorAgent,
    SuccessMonitorRecorderAgent,
    GarbageCollectorAgent,
)

# Define __all__ for explicit re-exports
__all__ = [
    "__version__",
    # Event bus
    "LONGINEventBus",
    # Storage
    "StorageManager",
    "StorageType",
    # Orchestrator
    "CoreOrchestrator",
    # Agents
    "CodingFlowBossAgent",
    "ContextMasterAgent",
    "TestOracleAgent",
    "CodeAlchemistAgent",
    "VisualValidatorAgent",
    "SuccessMonitorRecorderAgent",
    "GarbageCollectorAgent",
]
