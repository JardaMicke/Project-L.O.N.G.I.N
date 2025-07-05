import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from typing import List

# Longin Core Imports
from longin_core import (
    CoreOrchestrator,
    StorageManager,
    LONGINEventBus,
)
from longin_core.mcp import MCPServer
# New imports for Mini-agents functionality
from longin_core.agents.mini_agent import MiniAgent
from longin_core.learning_flow.runner import FlowDuration

# --- Global State & Configuration ---
# In a real application, this would come from a config file (e.g., .env, config.yaml)
# For now, we use a simple dictionary.
config: Dict[str, Any] = {
    "storage": {
        "json_store": {"base_path": "./data/json_store"},
        "redis_store": {"url": "redis://localhost:6379/0"},
        "postgres_store": {
            "user": "longin",
            "password": "longin_dev_password",
            "database": "longin_db",
            "host": "localhost",
        },
        "postgres_vector_store": {
            "user": "longin",
            "password": "longin_dev_password",
            "database": "longin_db",
            "host": "localhost",
        },
    },
    "mcp_server": {
        "host": "0.0.0.0",
        "port": 50051,
        "plugin_dir": "src/longin_core/mcp/plugins",
    },
    "event_bus": {},
    # -----------------------------------------------------------------
    # Mini-agent configuration                                         #
    # -----------------------------------------------------------------
    # Each entry defines one autonomous fine-tuning agent that will be
    # loaded by CoreOrchestrator on startup.  Paths assume the download
    # scripts place models/datasets in the shown locations – adjust as
    # needed for your environment.
    "mini_agents": [
        {
            "id": 0,
            "name": "chat_cz",
            "model_path": "data/models/agent_0/tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
            "dataset_path": "data/datasets/0.jsonl",
        },
        {
            "id": 1,
            "name": "math_master",
            "model_path": "data/models/agent_1/phi-2.Q2_K.gguf",
            "dataset_path": "data/datasets/1.jsonl",
        },
        {
            "id": 2,
            "name": "code_guru",
            "model_path": "data/models/agent_2/codellama-7b-instruct.Q2_K.gguf",
            "dataset_path": "data/datasets/2.jsonl",
        },
        {
            "id": 3,
            "name": "context_orchestrator",
            "model_path": "data/models/agent_3/mistral-7b-instruct-v0.2.Q2_K.gguf",
            "dataset_path": "data/datasets/3.jsonl",
        },
        {
            "id": 4,
            "name": "health_qa",
            "model_path": "data/models/agent_4/gemma-2b-it.Q2_K.gguf",
            "dataset_path": "data/datasets/4.jsonl",
        },
    ],
    "agents": {
        # Agent-specific configs can go here
    },
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("longin_api")

# --- Application Components Initialization ---
# These components will be managed by the FastAPI lifespan event handler.
app_state: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("API is starting up...")
    
    # Initialize core components
    storage_manager = StorageManager(config.get("storage", {}), logger.getChild("StorageManager"))
    event_bus = LONGINEventBus(logger.getChild("EventBus"), config.get("event_bus", {}))
    mcp_server = MCPServer(
        config["mcp_server"]["host"],
        config["mcp_server"]["port"],
        config["mcp_server"]["plugin_dir"],
        logger.getChild("MCPServer"),
    )
    orchestrator = CoreOrchestrator(
        config,
        logger.getChild("CoreOrchestrator"),
        storage_manager,
        event_bus,
        mcp_server,
    )
    
    # Start the orchestrator and all its components
    await orchestrator.start()
    
    # Store orchestrator in app state for access in endpoints
    app_state["orchestrator"] = orchestrator
    
    yield
    
    # --- Shutdown ---
    logger.info("API is shutting down...")
    orchestrator = app_state.get("orchestrator")
    if orchestrator:
        await orchestrator.stop()
    logger.info("Shutdown complete.")


# --- FastAPI Application ---
app = FastAPI(
    title="Longin AI Systems API",
    description="API for interacting with the Longin AI core system.",
    version="0.1.0",
    lifespan=lifespan,
)


# --- API Endpoints ---
@app.get("/status", tags=["System"])
async def get_system_status() -> Dict[str, Any]:
    """
    Retrieves the current status of the Longin AI system,
    including the status of the orchestrator and its managed agents.
    """
    orchestrator: CoreOrchestrator = app_state.get("orchestrator")
    if not orchestrator:
        return {"status": "error", "message": "Orchestrator not initialized."}

    # In a real implementation, orchestrator would have a get_status() method
    # that aggregates status from all modules and agents.
    agent_statuses = {name: agent.current_state if hasattr(agent, 'current_state') else 'unknown' for name, agent in orchestrator.agents.items()}

    return {
        "system_status": "running",
        "orchestrator_status": "active", # Placeholder
        "agent_count": len(orchestrator.agents),
        "agents": agent_statuses,
        "module_count": len(orchestrator.modules),
        "modules": list(orchestrator.modules.keys()), # Just names for now
    }


# --------------------------------------------------------------------------- #
#   FRTDSD Cycle Endpoints                                                    #
# --------------------------------------------------------------------------- #
from pydantic import BaseModel, Field


class FRTDSDRequest(BaseModel):
    """
    Request model for starting an FRTDSD cycle.
    """

    task_description: str = Field(
        ...,
        title="Task Description",
        description="Human-readable description of the development task to execute.",
        examples=["Implement user authentication using JWT"],
    )


@app.post("/start-frtdsd", tags=["FRTDSD"])
async def start_frtdsd_cycle(request: FRTDSDRequest) -> Dict[str, Any]:
    """
    Starts a new Frontend Ruled Test-Driven Self-Development (FRTDSD) cycle.

    The endpoint forwards the request to the `CodingFlowBossAgent`, which
    orchestrates the multi-agent workflow.
    """

    orchestrator: CoreOrchestrator = app_state.get("orchestrator")
    if not orchestrator:
        return {"status": "error", "message": "Orchestrator not initialized."}

    boss = orchestrator.agents.get("coding_flow_boss")
    if boss is None:
        return {"status": "error", "message": "CodingFlowBossAgent not available."}

    # Fire-and-forget launch of the cycle; it runs asynchronously
    await boss.start_frtdsd_cycle(request.task_description)

    return {
        "status": "started",
        "task_description": request.task_description,
        "message": "FRTDSD cycle has been initiated.",
    }

# --------------------------------------------------------------------------- #
#   Mini-Agent Endpoints                                                      #
# --------------------------------------------------------------------------- #

# --------------------------- Pydantic Schemas ------------------------------ #

class AgentSummary(BaseModel):
    id: int
    name: str


class AgentDetail(AgentSummary):
    model_path: str
    dataset_path: str
    statistics: Dict[str, Any]


class TrainingRequest(BaseModel):
    duration: FlowDuration = Field(
        ...,
        description="Training duration. One of: 1h, 2h, 6h, 12h, 24h",
        examples=["1h"],
    )


class ChatMessageModel(BaseModel):
    role: str
    content: str
    name: str | None = None


class ChatRequest(BaseModel):
    messages: List[ChatMessageModel]
    temperature: float | None = Field(0.7, ge=0.0, le=2.0)
    top_p: float | None = Field(1.0, ge=0.0, le=1.0)
    max_tokens: int | None = None


# --------------------------- Helper functions ------------------------------ #


def _get_orchestrator() -> CoreOrchestrator | None:
    """Helper to fetch orchestrator from app_state with typing."""
    return app_state.get("orchestrator")  # type: ignore[arg-type]


def _get_agent(agent_id: int) -> MiniAgent | None:
    orch = _get_orchestrator()
    if not orch:
        return None

    # Access the mini_agents registry safely
    agents_registry = getattr(orch, "mini_agents", None)
    if not agents_registry:
        return None

    # Primary lookup: integer key (expected)
    if agent_id in agents_registry:  # type: ignore[operator]
        return agents_registry[agent_id]  # type: ignore[index]

    # Fallback: string-keyed dict (in case ids were loaded as str)
    str_id = str(agent_id)
    return agents_registry.get(str_id)  # type: ignore[attr-defined]


# --------------------------- API Endpoints --------------------------------- #


@app.get("/agents", response_model=List[AgentSummary], tags=["Agents"])
async def list_agents():
    """Return basic information about all available MiniAgents."""
    orch = _get_orchestrator()
    if not orch or not hasattr(orch, "mini_agents"):
        return []

    return [
        AgentSummary(id=agent.id, name=agent.name)
        for agent in orch.mini_agents.values()  # type: ignore[attr-defined]
    ]


@app.get("/agents/{agent_id}", response_model=AgentDetail, tags=["Agents"])
async def get_agent(agent_id: int):
    """Retrieve detailed information about a single agent."""
    agent = _get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentDetail(
        id=agent.id,
        name=agent.name,
        model_path=agent.model_path,
        dataset_path=agent.dataset_path,
        statistics=agent.statistics,
    )


@app.post("/agents/{agent_id}/train", tags=["Agents"])
async def train_agent(agent_id: int, request: TrainingRequest):
    """Start a training flow for the specified agent."""
    agent = _get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        results = await agent.train(request.duration)
        return {"status": "ok", "results": results}
    except Exception as exc:
        logger.exception("Training failed")
        return {"status": "error", "message": str(exc)}


@app.post("/agents/{agent_id}/chat", tags=["Agents"])
async def chat_with_agent(agent_id: int, request: ChatRequest):
    """Send chat messages to the specified agent and receive a response."""
    agent = _get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        response = await agent.chat(
            [msg.dict() for msg in request.messages],
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
        return response
    except Exception as exc:
        logger.exception("Chat failed")
        return {"status": "error", "message": str(exc)}


@app.get("/agents/{agent_id}/status", tags=["Agents"])
async def get_agent_status(agent_id: int):
    """Return current statistics/state for the agent."""
    agent = _get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Basic status derived from agent.statistics; extend as needed
    return {
        "id": agent.id,
        "name": agent.name,
        "statistics": agent.statistics,
    }
