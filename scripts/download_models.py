#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Downloader Script

This script downloads quantized language models from the Hugging Face Hub.
It is designed to download models for the MiniAgent system, specifically
focusing on small, quantized models (around 1-2GB) that can run efficiently
on consumer hardware.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from huggingface_hub import hf_hub_download, HfApi
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("model_downloader")

# Default list of models to download
# Each model is specified with:
# - repo_id: The Hugging Face repository ID
# - filename: The specific file to download (usually a GGUF file)
# - agent_id: The ID of the agent that will use this model
# - description: A brief description of the model and its intended use
DEFAULT_MODELS = [
    {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
        "agent_id": 0,
        "description": "Small-Talk CZ agent - TinyLlama 1.1B with q2_K quantization (~0.9 GB)"
    },
    {
        "repo_id": "TheBloke/Phi-2-GGUF",
        "filename": "phi-2.Q2_K.gguf",
        "agent_id": 1,
        "description": "Mathematics agent - Phi-2 with q2_K quantization (~1.4 GB)"
    },
    {
        "repo_id": "TheBloke/CodeLlama-7B-Instruct-GGUF",
        "filename": "codellama-7b-instruct.Q2_K.gguf",
        "agent_id": 2,
        "description": "Coding agent - CodeLlama 7B Instruct with q2_K quantization (~1.8 GB)"
    },
    {
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "filename": "mistral-7b-instruct-v0.2.Q2_K.gguf",
        "agent_id": 3,
        "description": "Context orchestrator - Mistral 7B Instruct with q2_K quantization (~1.8 GB)"
    },
    {
        "repo_id": "TheBloke/Gemma-2b-it-GGUF",
        "filename": "gemma-2b-it.Q2_K.gguf",
        "agent_id": 4,
        "description": "Health QA agent - Gemma 2B Instruct with q2_K quantization (~1.2 GB)"
    }
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download quantized language models from the Hugging Face Hub."
    )
    
    parser.add_argument(
        "--dest", 
        type=str, 
        default="data/models",
        help="Destination directory for downloaded models (default: data/models)"
    )
    
    parser.add_argument(
        "--model-list", 
        type=str, 
        help="Path to a JSON file containing a list of models to download"
    )
    
    parser.add_argument(
        "--agent-id", 
        type=int, 
        help="Download only the model for a specific agent ID"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force download even if the model already exists"
    )
    
    parser.add_argument(
        "--list-only", 
        action="store_true", 
        help="Only list the models that would be downloaded, without downloading them"
    )
    
    return parser.parse_args()


def load_model_list(model_list_path: Optional[str]) -> List[Dict]:
    """
    Load the list of models to download from a JSON file or use the default list.
    
    Args:
        model_list_path: Path to a JSON file containing a list of models to download
        
    Returns:
        List of model specifications
    """
    if model_list_path:
        try:
            with open(model_list_path, "r") as f:
                models = json.load(f)
            logger.info(f"Loaded model list from {model_list_path}")
            return models
        except Exception as e:
            logger.error(f"Error loading model list from {model_list_path}: {e}")
            logger.info("Falling back to default model list")
    
    return DEFAULT_MODELS


def check_model_exists(dest_dir: str, model_spec: Dict) -> bool:
    """
    Check if a model already exists in the destination directory.
    
    Args:
        dest_dir: Destination directory
        model_spec: Model specification
        
    Returns:
        True if the model exists, False otherwise
    """
    filename = model_spec["filename"]
    agent_id = model_spec.get("agent_id")
    
    # If agent_id is specified, check in the agent-specific directory
    if agent_id is not None:
        path = os.path.join(dest_dir, f"agent_{agent_id}", filename)
    else:
        path = os.path.join(dest_dir, filename)
    
    return os.path.exists(path)


def download_model(dest_dir: str, model_spec: Dict, force: bool = False) -> bool:
    """
    Download a model from the Hugging Face Hub.
    
    Args:
        dest_dir: Destination directory
        model_spec: Model specification
        force: Force download even if the model already exists
        
    Returns:
        True if the download was successful, False otherwise
    """
    repo_id = model_spec["repo_id"]
    filename = model_spec["filename"]
    agent_id = model_spec.get("agent_id")
    description = model_spec.get("description", "")
    
    # Determine the destination path
    if agent_id is not None:
        # Create agent-specific directory
        agent_dir = os.path.join(dest_dir, f"agent_{agent_id}")
        os.makedirs(agent_dir, exist_ok=True)
        local_path = os.path.join(agent_dir, filename)
    else:
        local_path = os.path.join(dest_dir, filename)
    
    # Check if the model already exists
    if os.path.exists(local_path) and not force:
        logger.info(f"Model already exists at {local_path}, skipping download")
        return True
    
    # Log the download
    logger.info(f"Downloading {filename} from {repo_id}")
    if description:
        logger.info(f"Description: {description}")
    
    try:
        # Download the model
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=os.path.dirname(local_path),
            local_dir_use_symlinks=False,
        )
        
        logger.info(f"Successfully downloaded {filename} to {local_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading {filename} from {repo_id}: {e}")
        return False


def main():
    """Main function to orchestrate the download process."""
    args = parse_args()
    
    # Load the model list
    models = load_model_list(args.model_list)
    
    # Filter models by agent_id if specified
    if args.agent_id is not None:
        models = [m for m in models if m.get("agent_id") == args.agent_id]
        if not models:
            logger.error(f"No models found for agent_id {args.agent_id}")
            return 1
    
    # Create the destination directory if it doesn't exist
    os.makedirs(args.dest, exist_ok=True)
    
    # List models if --list-only is specified
    if args.list_only:
        logger.info("Models that would be downloaded:")
        for i, model in enumerate(models, 1):
            logger.info(f"{i}. {model.get('description', 'No description')} - {model['repo_id']}/{model['filename']}")
        return 0
    
    # Download each model
    success_count = 0
    for i, model in enumerate(models, 1):
        logger.info(f"Processing model {i}/{len(models)}")
        
        if download_model(args.dest, model, args.force):
            success_count += 1
    
    # Log summary
    logger.info(f"Download summary: {success_count}/{len(models)} models downloaded successfully")
    
    return 0 if success_count == len(models) else 1


if __name__ == "__main__":
    sys.exit(main())
