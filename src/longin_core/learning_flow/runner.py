#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Learning Flow Runner

This module provides the LearningFlowRunner class, which manages the fine-tuning
process of language models within a specified time duration. It handles subprocess
management, metric parsing, and event broadcasting.
"""

import asyncio
import datetime
import json
import logging
import os
import pathlib
import shutil
import signal
import tempfile
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator

# Import event bus for publishing metrics and status updates
from longin_core.event_bus import LONGINEventBus

# Configure logging
logger = logging.getLogger(__name__)


class FlowDuration(str, Enum):
    """Enum for standard training durations"""
    ONE_HOUR = "1h"
    TWO_HOURS = "2h"
    SIX_HOURS = "6h"
    TWELVE_HOURS = "12h"
    TWENTYFOUR_HOURS = "24h"


class TrainingState(str, Enum):
    """Enum for training process states"""
    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELED = "canceled"


class TrainingMetrics(BaseModel):
    """Pydantic model for training metrics"""
    step: int = Field(..., description="Current training step")
    loss: float = Field(..., description="Training loss value")
    learning_rate: float = Field(..., description="Current learning rate")
    epoch: float = Field(..., description="Current epoch (can be fractional)")
    eval_loss: Optional[float] = Field(None, description="Evaluation loss if available")
    train_runtime: Optional[float] = Field(None, description="Training runtime in seconds")
    train_samples_per_second: Optional[float] = Field(None, description="Training samples per second")
    timestamp: float = Field(default_factory=time.time, description="Timestamp when metrics were recorded")

    @validator('loss', 'eval_loss', pre=True)
    def validate_loss(cls, v):
        """Ensure loss values are finite"""
        if v is not None and (isinstance(v, (int, float)) and (v < 0 or not isinstance(v, (int, float)))):
            raise ValueError(f"Loss must be a non-negative number, got {v}")
        return v


class TrainingConfig(BaseModel):
    """Configuration for the training process"""
    model_path: str = Field(..., description="Path to the base model")
    dataset_path: str = Field(..., description="Path to the training dataset")
    output_dir: str = Field(..., description="Directory to save outputs")
    learning_rate: float = Field(2e-4, description="Learning rate for training")
    batch_size: int = Field(4, description="Batch size for training")
    gradient_accumulation_steps: int = Field(8, description="Gradient accumulation steps")
    warmup_steps: int = Field(100, description="Number of warmup steps")
    max_steps: Optional[int] = Field(None, description="Maximum number of training steps")
    save_steps: int = Field(200, description="Steps between checkpoints")
    eval_steps: int = Field(200, description="Steps between evaluations")
    logging_steps: int = Field(10, description="Steps between logging")
    lora_r: int = Field(16, description="LoRA attention dimension")
    lora_alpha: int = Field(32, description="LoRA alpha parameter")
    lora_dropout: float = Field(0.05, description="LoRA dropout probability")
    max_seq_length: int = Field(512, description="Maximum sequence length")
    seed: int = Field(42, description="Random seed")


class LearningFlowRunner:
    """
    Manages the fine-tuning process of language models within a specified time duration.
    
    This class orchestrates the training process, monitors metrics, and ensures
    the training completes within the allocated time budget.
    """

    def __init__(
        self,
        agent_config: Dict[str, Any],
        duration: Union[FlowDuration, str],
        event_bus: LONGINEventBus,
        base_output_dir: str = "data/training_runs",
    ):
        """
        Initialize the LearningFlowRunner.
        
        Args:
            agent_config: Configuration dictionary for the agent
            duration: Training duration (as FlowDuration enum or string)
            event_bus: Event bus for publishing metrics and status updates
            base_output_dir: Base directory for training outputs
        """
        self.agent_config = agent_config
        self.agent_id = agent_config.get("id")
        self.agent_name = agent_config.get("name", f"agent_{self.agent_id}")
        
        # Convert string to enum if needed
        if isinstance(duration, str):
            try:
                self.duration = FlowDuration(duration)
            except ValueError:
                raise ValueError(f"Invalid duration: {duration}. Must be one of {[d.value for d in FlowDuration]}")
        else:
            self.duration = duration
            
        self.event_bus = event_bus
        self.base_output_dir = pathlib.Path(base_output_dir)
        
        # Create a unique run ID based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{self.agent_name}_{timestamp}"
        
        # Set up output directory
        self.output_dir = self.base_output_dir / f"agent_{self.agent_id}" / self.run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize state and metrics
        self.state = TrainingState.PENDING
        self.start_time = None
        self.end_time = None
        self.process = None
        self.latest_metrics = None
        self.all_metrics = []
        
        # Duration in seconds
        self.duration_seconds = self._duration_to_seconds(self.duration)
        
        # Training configuration
        self.training_config = self._prepare_training_config()
        
        logger.info(f"Initialized LearningFlowRunner for agent {self.agent_name} with duration {self.duration.value}")

    def _duration_to_seconds(self, duration: FlowDuration) -> int:
        """
        Convert duration enum to seconds.
        
        Args:
            duration: Duration enum
            
        Returns:
            Duration in seconds
        """
        duration_map = {
            FlowDuration.ONE_HOUR: 3600,
            FlowDuration.TWO_HOURS: 7200,
            FlowDuration.SIX_HOURS: 21600,
            FlowDuration.TWELVE_HOURS: 43200,
            FlowDuration.TWENTYFOUR_HOURS: 86400,
        }
        return duration_map.get(duration, 3600)  # Default to 1 hour if not found

    def _prepare_training_config(self) -> TrainingConfig:
        """
        Prepare the training configuration based on agent config and duration.
        
        Returns:
            TrainingConfig object
        """
        # Get model and dataset paths from agent config
        model_path = self.agent_config.get("model_path")
        dataset_path = self.agent_config.get("dataset_path")
        
        if not model_path or not dataset_path:
            raise ValueError(f"Missing model_path or dataset_path in agent config for agent {self.agent_id}")
        
        # Adjust hyperparameters based on duration
        # These are just example values; in a real system, you'd have more sophisticated scaling
        duration_seconds = self.duration_seconds
        
        # Scale batch size, accumulation steps, and max steps based on duration
        batch_size = min(8, 4 + (duration_seconds // 7200))  # Increase batch size with duration, max 8
        gradient_accumulation_steps = min(16, 8 + (duration_seconds // 7200 * 2))  # Scale with duration
        
        # Estimate max steps based on dataset size and duration
        # In a real implementation, you would calculate this based on dataset size
        # For now, we use a simple heuristic: more time = more steps
        max_steps = duration_seconds // 60  # Roughly one step per minute as a placeholder
        
        # Adjust save and eval frequency based on total steps
        save_steps = max(100, max_steps // 20)  # Save approximately 20 times during training
        eval_steps = max(100, max_steps // 10)  # Evaluate approximately 10 times during training
        
        return TrainingConfig(
            model_path=model_path,
            dataset_path=dataset_path,
            output_dir=str(self.output_dir),
            batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            max_steps=max_steps,
            save_steps=save_steps,
            eval_steps=eval_steps
        )

    def _build_training_command(self) -> List[str]:
        """
        Build the command to run the training script.
        
        Returns:
            List of command arguments
        """
        # Convert training config to command line arguments
        config_dict = self.training_config.dict()
        cmd = [
            "python", "-m", "longin_core.learning_flow.train",
            "--model_path", config_dict["model_path"],
            "--dataset_path", config_dict["dataset_path"],
            "--output_dir", config_dict["output_dir"],
            "--learning_rate", str(config_dict["learning_rate"]),
            "--batch_size", str(config_dict["batch_size"]),
            "--gradient_accumulation_steps", str(config_dict["gradient_accumulation_steps"]),
            "--warmup_steps", str(config_dict["warmup_steps"]),
            "--save_steps", str(config_dict["save_steps"]),
            "--eval_steps", str(config_dict["eval_steps"]),
            "--logging_steps", str(config_dict["logging_steps"]),
            "--lora_r", str(config_dict["lora_r"]),
            "--lora_alpha", str(config_dict["lora_alpha"]),
            "--lora_dropout", str(config_dict["lora_dropout"]),
            "--max_seq_length", str(config_dict["max_seq_length"]),
            "--seed", str(config_dict["seed"]),
            "--json_logging",  # Enable JSON logging for easy parsing
        ]
        
        # Add max_steps if specified
        if config_dict["max_steps"]:
            cmd.extend(["--max_steps", str(config_dict["max_steps"])])
            
        return cmd

    async def _parse_metrics(self, line: str) -> Optional[TrainingMetrics]:
        """
        Parse metrics from a line of output.
        
        Args:
            line: Line of output from the training process
            
        Returns:
            TrainingMetrics object or None if the line doesn't contain metrics
        """
        try:
            # Check if the line is a JSON metrics line
            if line.startswith('{"metrics":'):
                data = json.loads(line)
                metrics_data = data.get("metrics", {})
                
                # Create TrainingMetrics object
                metrics = TrainingMetrics(
                    step=metrics_data.get("step", 0),
                    loss=metrics_data.get("loss", 0.0),
                    learning_rate=metrics_data.get("learning_rate", 0.0),
                    epoch=metrics_data.get("epoch", 0.0),
                    eval_loss=metrics_data.get("eval_loss"),
                    train_runtime=metrics_data.get("train_runtime"),
                    train_samples_per_second=metrics_data.get("train_samples_per_second")
                )
                return metrics
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.warning(f"Error parsing metrics: {e}")
            
        return None

    async def _publish_state_update(self):
        """Publish the current state to the event bus."""
        await self.event_bus.publish(
            "training_state_update",
            {
                "agent_id": self.agent_id,
                "run_id": self.run_id,
                "state": self.state,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": self.duration.value,
                "elapsed_seconds": (time.time() - self.start_time) if self.start_time else 0,
                "remaining_seconds": max(0, self.duration_seconds - (time.time() - self.start_time)) if self.start_time else self.duration_seconds,
            }
        )

    async def _publish_metrics_update(self, metrics: TrainingMetrics):
        """
        Publish metrics update to the event bus.
        
        Args:
            metrics: Training metrics to publish
        """
        await self.event_bus.publish(
            "training_metrics_update",
            {
                "agent_id": self.agent_id,
                "run_id": self.run_id,
                "metrics": metrics.dict(),
            }
        )

    async def run(self) -> Dict[str, Any]:
        """
        Run the training process.
        
        Returns:
            Dictionary with training results
        """
        self.state = TrainingState.PREPARING
        await self._publish_state_update()
        
        logger.info(f"Starting training run {self.run_id} for agent {self.agent_name}")
        
        try:
            # Prepare the command
            cmd = self._build_training_command()
            logger.debug(f"Training command: {' '.join(cmd)}")
            
            # Start the process
            self.start_time = time.time()
            self.state = TrainingState.RUNNING
            await self._publish_state_update()
            
            # Create the process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # Set up a task to terminate the process after the duration
            termination_task = asyncio.create_task(self._terminate_after_timeout())
            
            # Process stdout for metrics
            stdout_task = asyncio.create_task(self._process_stdout())
            stderr_task = asyncio.create_task(self._process_stderr())
            
            # Wait for the process to complete or be terminated
            try:
                await asyncio.gather(stdout_task, stderr_task)
                return_code = await self.process.wait()
                
                # Cancel the termination task if the process completes before timeout
                if not termination_task.done():
                    termination_task.cancel()
                
                # Check the return code
                if return_code == 0:
                    self.state = TrainingState.COMPLETED
                    logger.info(f"Training completed successfully for run {self.run_id}")
                else:
                    self.state = TrainingState.FAILED
                    logger.error(f"Training failed with return code {return_code} for run {self.run_id}")
            except asyncio.CancelledError:
                # This happens when the termination task cancels the process
                self.state = TrainingState.TIMEOUT
                logger.info(f"Training timed out after {self.duration.value} for run {self.run_id}")
            
            # Record end time
            self.end_time = time.time()
            await self._publish_state_update()
            
            # Save training stats
            self._save_training_stats()
            
            return self._get_training_results()
            
        except Exception as e:
            self.state = TrainingState.FAILED
            self.end_time = time.time()
            logger.exception(f"Error during training: {e}")
            await self._publish_state_update()
            
            return {
                "status": "error",
                "error": str(e),
                "run_id": self.run_id,
                "agent_id": self.agent_id,
            }

    async def _terminate_after_timeout(self):
        """Terminate the process after the specified duration."""
        try:
            await asyncio.sleep(self.duration_seconds)
            
            if self.process and self.process.returncode is None:
                logger.info(f"Training duration of {self.duration.value} reached for run {self.run_id}. Terminating process.")
                
                # Send SIGINT to allow the process to save its state
                self.process.send_signal(signal.SIGINT)
                
                # Wait for the process to terminate gracefully
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=60)
                except asyncio.TimeoutError:
                    logger.warning("Process did not terminate gracefully. Killing it.")
                    self.process.kill()
                
                self.state = TrainingState.TIMEOUT
                self.end_time = time.time()
                await self._publish_state_update()
        except asyncio.CancelledError:
            # This task was cancelled because the process completed before timeout
            pass

    async def _process_stdout(self):
        """Process the stdout of the training process to extract metrics."""
        assert self.process is not None
        
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
                
            line_str = line.decode('utf-8').strip()
            logger.debug(f"[STDOUT] {line_str}")
            
            # Parse metrics
            metrics = await self._parse_metrics(line_str)
            if metrics:
                self.latest_metrics = metrics
                self.all_metrics.append(metrics)
                await self._publish_metrics_update(metrics)

    async def _process_stderr(self):
        """Process the stderr of the training process."""
        assert self.process is not None
        
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
                
            line_str = line.decode('utf-8').strip()
            logger.warning(f"[STDERR] {line_str}")

    def _save_training_stats(self):
        """Save training statistics to a file."""
        stats_path = self.output_dir / "training_stats.json"
        
        stats = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "run_id": self.run_id,
            "state": self.state,
            "duration": self.duration.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": self.end_time - self.start_time if self.start_time and self.end_time else None,
            "training_config": self.training_config.dict(),
            "final_metrics": self.latest_metrics.dict() if self.latest_metrics else None,
            "metrics_history": [m.dict() for m in self.all_metrics],
        }
        
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Saved training stats to {stats_path}")

    def _get_training_results(self) -> Dict[str, Any]:
        """
        Get the training results.
        
        Returns:
            Dictionary with training results
        """
        # Check if the adapter was saved
        adapter_path = self.output_dir / "adapter_model"
        adapter_exists = adapter_path.exists()
        
        return {
            "status": "success" if self.state in [TrainingState.COMPLETED, TrainingState.TIMEOUT] else "error",
            "state": self.state,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "duration": self.duration.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": self.end_time - self.start_time if self.start_time and self.end_time else None,
            "adapter_saved": adapter_exists,
            "adapter_path": str(adapter_path) if adapter_exists else None,
            "final_metrics": self.latest_metrics.dict() if self.latest_metrics else None,
        }

    async def cancel(self):
        """Cancel the training process."""
        if self.process and self.process.returncode is None:
            logger.info(f"Cancelling training run {self.run_id}")
            
            # Send SIGINT to allow the process to save its state
            self.process.send_signal(signal.SIGINT)
            
            # Wait for the process to terminate gracefully
            try:
                await asyncio.wait_for(self.process.wait(), timeout=60)
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate gracefully. Killing it.")
                self.process.kill()
            
            self.state = TrainingState.CANCELED
            self.end_time = time.time()
            await self._publish_state_update()
            
            # Save training stats
            self._save_training_stats()
            
            return True
        return False
