import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.longin_core.orchestrator import CoreOrchestrator
from src.longin_core.storage import StorageManager
from src.longin_core.event_bus import LONGINEventBus
from src.longin_core.mcp import MCPServer

@pytest.mark.asyncio
async def test_frtdsd_cycle():
    # Mock dependencies
    config = {}
    logger = MagicMock()
    storage_manager = AsyncMock(spec=StorageManager)
    event_bus = AsyncMock(spec=LONGINEventBus)
    mcp_server = AsyncMock(spec=MCPServer)

    # Initialize CoreOrchestrator
    orchestrator = CoreOrchestrator(config, logger, storage_manager, event_bus, mcp_server)
    await orchestrator.load_core_agents()

    # Get CodingFlowBossAgent
    coding_flow_boss = orchestrator.agents.get("coding_flow_boss")
    assert coding_flow_boss is not None

    # Start the cycle
    task_description = "Create a button with the text 'Test'"
    await coding_flow_boss.start_frtdsd_cycle(task_description)

    # Assert that the first event was published
    event_bus.publish.assert_called_with("context_request", {"task": task_description}, "coding_flow_boss")
