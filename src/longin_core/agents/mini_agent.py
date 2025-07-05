#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniAgent Module

This module defines the MiniAgent class, which represents a small, autonomous agent
designed for fine-tuning and inference using quantized language models.
Each agent has its own model, dataset, memory, and statistics.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, ClassVar

# Import Longin Core components
from longin_core.event_bus import LONGINEventBus
from longin_core.lmstudio.client import AsyncLMStudioClient, ChatMessage, ChatRole
from longin_core.learning_flow.runner import LearningFlowRunner, FlowDuration, TrainingState


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MiniAgent:
    """
    A small, autonomous agent designed for fine-tuning and inference.
    
    Each MiniAgent has its own language model, dataset, memory, and statistics.
    It can be trained using the LearningFlowRunner and can perform inference
    using the LMStudioClient.
    """
    
    # Basic properties
    id: int
    name: str
    model_path: str
    dataset_path: str
    
    # State properties
    memory: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    # Non-serialized properties
    _lmstudio_client: Optional[AsyncLMStudioClient] = field(default=None, repr=False)
    _event_bus: Optional[LONGINEventBus] = field(default=None, repr=False)
    _base_dir: ClassVar[str] = "data/agents"
    
    def __post_init__(self):
        """Initialize dependencies and ensure directories exist."""
        # Ensure the agent directory exists
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize statistics if empty
        if not self.statistics:
            self.statistics = {
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "training_runs": [],
                "chat_completions": 0,
                "total_training_time": 0,
                "last_training_run": None,
                "best_loss": None,
            }
    
    @property
    def agent_dir(self) -> Path:
        """Get the directory path for this agent's data."""
        return Path(self._base_dir) / str(self.id)
    
    @property
    def state_path(self) -> Path:
        """Get the path to the agent's state file."""
        return self.agent_dir / "agent_state.json"
    
    @property
    def lmstudio_client(self) -> AsyncLMStudioClient:
        """Get the LMStudioClient, creating it if it doesn't exist."""
        if self._lmstudio_client is None:
            # Default to localhost:1234, but this could be configurable
            self._lmstudio_client = AsyncLMStudioClient(base_url="http://localhost:1234")
        return self._lmstudio_client
    
    @lmstudio_client.setter
    def lmstudio_client(self, client: AsyncLMStudioClient):
        """Set the LMStudioClient."""
        self._lmstudio_client = client
    
    @property
    def event_bus(self) -> LONGINEventBus:
        """Get the event bus, creating it if it doesn't exist."""
        if self._event_bus is None:
            # This would typically be injected by the orchestrator
            raise ValueError("Event bus not set. Please set it before using.")
        return self._event_bus
    
    @event_bus.setter
    def event_bus(self, bus: LONGINEventBus):
        """Set the event bus."""
        self._event_bus = bus
    
    def save_state(self) -> None:
        """Save the agent's state to a file."""
        # Update last modified timestamp
        self.statistics["last_modified"] = datetime.now().isoformat()
        
        # Create a serializable representation of the agent
        state = {
            "id": self.id,
            "name": self.name,
            "model_path": self.model_path,
            "dataset_path": self.dataset_path,
            "memory": self.memory,
            "statistics": self.statistics,
        }
        
        # Save to file
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)
            
        logger.info(f"Saved agent state to {self.state_path}")
    
    @classmethod
    def load_state(cls, agent_id: int, base_dir: str = "data/agents") -> "MiniAgent":
        """
        Load an agent's state from a file.
        
        Args:
            agent_id: The ID of the agent to load
            base_dir: The base directory for agent data
            
        Returns:
            MiniAgent: The loaded agent
        
        Raises:
            FileNotFoundError: If the agent state file doesn't exist
        """
        # Set the base directory
        cls._base_dir = base_dir
        
        # Construct the path to the agent's state file
        state_path = Path(base_dir) / str(agent_id) / "agent_state.json"
        
        # Check if the file exists
        if not state_path.exists():
            raise FileNotFoundError(f"Agent state file not found: {state_path}")
        
        # Load the state from the file
        with open(state_path, "r") as f:
            state = json.load(f)
        
        # Create a new agent with the loaded state
        agent = cls(
            id=state["id"],
            name=state["name"],
            model_path=state["model_path"],
            dataset_path=state["dataset_path"],
            memory=state["memory"],
            statistics=state["statistics"],
        )
        
        logger.info(f"Loaded agent state from {state_path}")
        return agent
    
    async def train(self, duration: Union[str, FlowDuration]) -> Dict[str, Any]:
        """
        Start a training run for this agent.
        
        Args:
            duration: The duration of the training run (e.g., "1h", "6h", "24h")
            
        Returns:
            Dict[str, Any]: The results of the training run
        """
        logger.info(f"Starting training run for agent {self.id} ({self.name}) with duration {duration}")
        
        # Create the agent config for the LearningFlowRunner
        agent_config = {
            "id": self.id,
            "name": self.name,
            "model_path": self.model_path,
            "dataset_path": self.dataset_path,
        }
        
        # Create and run the LearningFlowRunner
        runner = LearningFlowRunner(
            agent_config=agent_config,
            duration=duration,
            event_bus=self.event_bus,
        )
        
        # Run the training process
        results = await runner.run()
        
        # Update statistics with the results
        training_run = {
            "run_id": results.get("run_id"),
            "duration": str(duration),
            "start_time": results.get("start_time"),
            "end_time": results.get("end_time"),
            "elapsed_seconds": results.get("elapsed_seconds"),
            "state": results.get("state"),
            "adapter_path": results.get("adapter_path"),
        }
        
        # Add metrics if available
        if results.get("final_metrics"):
            training_run["final_metrics"] = results.get("final_metrics")
            
            # Update best loss if this is better
            current_loss = results.get("final_metrics", {}).get("loss")
            if current_loss is not None:
                if self.statistics.get("best_loss") is None or current_loss < self.statistics.get("best_loss"):
                    self.statistics["best_loss"] = current_loss
        
        # Update agent statistics
        self.statistics["training_runs"].append(training_run)
        self.statistics["last_training_run"] = training_run
        self.statistics["total_training_time"] += training_run.get("elapsed_seconds", 0)
        
        # Save the updated state
        self.save_state()
        
        # If training was successful and an adapter was saved, try to load it into LM Studio
        if results.get("adapter_saved") and results.get("adapter_path"):
            try:
                # In a real implementation, we would merge the adapter with the base model
                # or configure LM Studio to use the adapter
                logger.info(f"Training completed successfully. Adapter saved to {results.get('adapter_path')}")
                
                # This is a placeholder for loading the adapter into LM Studio
                # await self.lmstudio_client.load_model(results.get("adapter_path"))
            except Exception as e:
                logger.error(f"Failed to load adapter into LM Studio: {e}")
        
        return results
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat request to the agent's language model.
        
        Args:
            messages: List of messages in the chat history
            **kwargs: Additional parameters to pass to the LMStudioClient
            
        Returns:
            Dict[str, Any]: The response from the language model
        """
        logger.info(f"Sending chat request to agent {self.id} ({self.name})")
        
        # Convert dict messages to ChatMessage objects
        chat_messages = [
            ChatMessage(
                role=ChatRole(msg["role"]),
                content=msg["content"],
                name=msg.get("name")
            )
            for msg in messages
        ]
        
        try:
            # Get the model ID to use (this would be the runtime ID in LM Studio)
            # In a real implementation, we would track the runtime ID of the model
            # For now, we'll use the base model path as the ID
            model_id = os.path.basename(self.model_path)
            
            # Send the chat request to LM Studio
            response = await self.lmstudio_client.create_chat_completion(
                model=model_id,
                messages=chat_messages,
                **kwargs
            )
            
            # Update statistics
            self.statistics["chat_completions"] += 1
            self.save_state()
            
            return response.dict()
        except Exception as e:
            logger.error(f"Error during chat completion: {e}")
            raise
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """
        Stream a chat response from the agent's language model.
        
        Args:
            messages: List of messages in the chat history
            **kwargs: Additional parameters to pass to the LMStudioClient
            
        Yields:
            Chunks of the response from the language model
        """
        logger.info(f"Streaming chat request to agent {self.id} ({self.name})")
        
        # Convert dict messages to ChatMessage objects
        chat_messages = [
            ChatMessage(
                role=ChatRole(msg["role"]),
                content=msg["content"],
                name=msg.get("name")
            )
            for msg in messages
        ]
        
        try:
            # Get the model ID to use
            model_id = os.path.basename(self.model_path)
            
            # Stream the chat response from LM Studio
            async for chunk in self.lmstudio_client.stream_chat_completion(
                model=model_id,
                messages=chat_messages,
                **kwargs
            ):
                yield chunk
            
            # Update statistics after streaming completes
            self.statistics["chat_completions"] += 1
            self.save_state()
        except Exception as e:
            logger.error(f"Error during chat streaming: {e}")
            raise
    
    async def subscribe_to_events(self):
        """Subscribe to relevant events on the event bus."""
        # Subscribe to training events to update the agent's state
        await self.event_bus.subscribe(
            f"training_state_update.agent_{self.id}",
            self._handle_training_state_update
        )
        
        await self.event_bus.subscribe(
            f"training_metrics_update.agent_{self.id}",
            self._handle_training_metrics_update
        )
    
    async def _handle_training_state_update(self, data: Dict[str, Any]):
        """
        Handle training state update events.
        
        Args:
            data: Event data containing training state information
        """
        # This method would be called when a training state update event is published
        # We could update the agent's state based on the event data
        logger.debug(f"Received training state update for agent {self.id}: {data}")
        
        # Update memory with the latest training state
        self.memory["latest_training_state"] = data
    
    async def _handle_training_metrics_update(self, data: Dict[str, Any]):
        """
        Handle training metrics update events.
        
        Args:
            data: Event data containing training metrics
        """
        # This method would be called when a training metrics update event is published
        logger.debug(f"Received training metrics update for agent {self.id}: {data}")
        
        # Update memory with the latest metrics
        self.memory["latest_metrics"] = data


async def main():
    """Example usage of the MiniAgent class."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create an event bus
    event_bus = LONGINEventBus(logger=logger)
    
    try:
        # Try to load an existing agent
        try:
            agent = MiniAgent.load_state(agent_id=0)
            logger.info(f"Loaded existing agent: {agent.name}")
        except FileNotFoundError:
            # Create a new agent if one doesn't exist
            logger.info("Creating new agent")
            agent = MiniAgent(
                id=0,
                name="example_agent",
                model_path="data/models/TinyLlama-1.1B-q2_K.gguf",
                dataset_path="data/datasets/0.jsonl",
            )
        
        # Set the event bus
        agent.event_bus = event_bus
        
        # Subscribe to events
        await agent.subscribe_to_events()
        
        # Start a training run (1 hour)
        results = await agent.train(duration=FlowDuration.ONE_HOUR)
        logger.info(f"Training results: {results}")
        
        # Send a chat request
        messages = [
            {"role": "user", "content": "Hello! Can you tell me about yourself?"}
        ]
        response = await agent.chat(messages)
        logger.info(f"Chat response: {response}")
        
        # Save the agent's state
        agent.save_state()
        
    except Exception as e:
        logger.exception(f"Error in main: {e}")
    finally:
        # Clean up
        if hasattr(agent, 'lmstudio_client') and agent.lmstudio_client:
            await agent.lmstudio_client.close()


if __name__ == "__main__":
    asyncio.run(main())
