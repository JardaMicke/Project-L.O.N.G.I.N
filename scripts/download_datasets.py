#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Downloader Script

This script downloads and preprocesses datasets from the Hugging Face Hub
for use with the MiniAgent system. It converts various dataset formats into
a standardized JSONL format with 'prompt' and 'response' fields that can be
used for fine-tuning language models.
"""

import argparse
import json
import logging
import os
import sys
import random
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any

from datasets import load_dataset, Dataset, DatasetDict
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("dataset_downloader")

# Default list of datasets to download
# Each dataset is specified with:
# - repo_id: The Hugging Face repository ID or local path
# - subset: The specific subset of the dataset (optional)
# - split: The split to use (e.g., "train", "validation")
# - agent_id: The ID of the agent that will use this dataset
# - description: A brief description of the dataset and its intended use
# - preprocessing_fn: The name of the preprocessing function to use (defined below)
# - max_samples: Maximum number of samples to include (for limiting dataset size)
DEFAULT_DATASETS = [
    {
        "repo_id": "czech_dialogue",
        "subset": None,
        "split": "train",
        "agent_id": 0,
        "description": "Czech dialogue dataset for Small-Talk CZ agent",
        "preprocessing_fn": "preprocess_dialogue_dataset",
        "max_samples": 500
    },
    {
        "repo_id": "gsm8k",
        "subset": "main",
        "split": "train",
        "agent_id": 1,
        "description": "Grade School Math 8K dataset for Mathematics agent",
        "preprocessing_fn": "preprocess_gsm8k_dataset",
        "max_samples": 300
    },
    {
        "repo_id": "codeparrot/codecompete-self-instruct",
        "subset": None,
        "split": "train",
        "agent_id": 2,
        "description": "Code completion dataset for Coding agent",
        "preprocessing_fn": "preprocess_code_dataset",
        "max_samples": 500
    },
    {
        "repo_id": "knkarthick/dialogsum",
        "subset": None,
        "split": "train",
        "agent_id": 3,
        "description": "Dialogue summarization dataset for Context Orchestrator agent",
        "preprocessing_fn": "preprocess_summarization_dataset",
        "max_samples": 500
    },
    {
        "repo_id": "medical_meadow/medical_meadow_medqa",
        "subset": None,
        "split": "train",
        "agent_id": 4,
        "description": "Medical QA dataset for Health QA agent",
        "preprocessing_fn": "preprocess_qa_dataset",
        "max_samples": 500
    }
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download and preprocess datasets from the Hugging Face Hub."
    )
    
    parser.add_argument(
        "--dest", 
        type=str, 
        default="data/datasets",
        help="Destination directory for processed datasets (default: data/datasets)"
    )
    
    parser.add_argument(
        "--dataset-list", 
        type=str, 
        help="Path to a JSON file containing a list of datasets to download"
    )
    
    parser.add_argument(
        "--agent-id", 
        type=int, 
        help="Download only the dataset for a specific agent ID"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force download and preprocessing even if the dataset already exists"
    )
    
    parser.add_argument(
        "--list-only", 
        action="store_true", 
        help="Only list the datasets that would be downloaded, without downloading them"
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Override the max_samples setting for all datasets"
    )
    
    return parser.parse_args()


def load_dataset_list(dataset_list_path: Optional[str]) -> List[Dict]:
    """
    Load the list of datasets to download from a JSON file or use the default list.
    
    Args:
        dataset_list_path: Path to a JSON file containing a list of datasets to download
        
    Returns:
        List of dataset specifications
    """
    if dataset_list_path:
        try:
            with open(dataset_list_path, "r") as f:
                datasets = json.load(f)
            logger.info(f"Loaded dataset list from {dataset_list_path}")
            return datasets
        except Exception as e:
            logger.error(f"Error loading dataset list from {dataset_list_path}: {e}")
            logger.info("Falling back to default dataset list")
    
    return DEFAULT_DATASETS


def check_dataset_exists(dest_dir: str, dataset_spec: Dict) -> bool:
    """
    Check if a processed dataset already exists in the destination directory.
    
    Args:
        dest_dir: Destination directory
        dataset_spec: Dataset specification
        
    Returns:
        True if the dataset exists, False otherwise
    """
    agent_id = dataset_spec.get("agent_id")
    
    # If agent_id is specified, check in the agent-specific directory
    if agent_id is not None:
        path = os.path.join(dest_dir, f"{agent_id}.jsonl")
    else:
        # Extract a name from the repo_id
        name = dataset_spec["repo_id"].split("/")[-1]
        path = os.path.join(dest_dir, f"{name}.jsonl")
    
    return os.path.exists(path)


def download_dataset(dataset_spec: Dict) -> Optional[Union[Dataset, DatasetDict]]:
    """
    Download a dataset from the Hugging Face Hub.
    
    Args:
        dataset_spec: Dataset specification
        
    Returns:
        The downloaded dataset or None if the download failed
    """
    repo_id = dataset_spec["repo_id"]
    subset = dataset_spec.get("subset")
    split = dataset_spec.get("split")
    description = dataset_spec.get("description", "")
    
    # Log the download
    logger.info(f"Downloading dataset from {repo_id}")
    if subset:
        logger.info(f"Subset: {subset}")
    if description:
        logger.info(f"Description: {description}")
    
    try:
        # Download the dataset
        if subset:
            dataset = load_dataset(repo_id, subset)
        else:
            dataset = load_dataset(repo_id)
        
        # If a split is specified, get that split
        if split and isinstance(dataset, DatasetDict) and split in dataset:
            dataset = dataset[split]
            logger.info(f"Using split: {split}")
        
        logger.info(f"Successfully downloaded dataset from {repo_id}")
        return dataset
    except Exception as e:
        logger.error(f"Error downloading dataset from {repo_id}: {e}")
        return None


# Preprocessing functions for different dataset types
def preprocess_dialogue_dataset(dataset: Dataset, max_samples: Optional[int] = None) -> List[Dict]:
    """
    Preprocess a dialogue dataset into a list of prompt-response pairs.
    
    Args:
        dataset: The dataset to preprocess
        max_samples: Maximum number of samples to include
        
    Returns:
        List of dictionaries with 'prompt' and 'response' keys
    """
    logger.info("Preprocessing dialogue dataset")
    
    # Check if the dataset has the expected structure
    if "dialogue" in dataset.column_names:
        # Dataset has a 'dialogue' column, extract turns
        result = []
        for item in tqdm(dataset, desc="Processing dialogues"):
            dialogue = item["dialogue"]
            if isinstance(dialogue, list):
                # Dialogue is a list of turns
                for i in range(len(dialogue) - 1):
                    result.append({
                        "prompt": dialogue[i],
                        "response": dialogue[i + 1]
                    })
            elif isinstance(dialogue, str):
                # Dialogue is a string, try to split by newlines or other delimiters
                turns = dialogue.split("\n")
                for i in range(len(turns) - 1):
                    if turns[i].strip() and turns[i + 1].strip():
                        result.append({
                            "prompt": turns[i].strip(),
                            "response": turns[i + 1].strip()
                        })
    elif "input" in dataset.column_names and "output" in dataset.column_names:
        # Dataset has 'input' and 'output' columns
        result = [
            {"prompt": item["input"], "response": item["output"]}
            for item in tqdm(dataset, desc="Processing input-output pairs")
            if item["input"].strip() and item["output"].strip()
        ]
    elif "question" in dataset.column_names and "answer" in dataset.column_names:
        # Dataset has 'question' and 'answer' columns
        result = [
            {"prompt": item["question"], "response": item["answer"]}
            for item in tqdm(dataset, desc="Processing QA pairs")
            if item["question"].strip() and item["answer"].strip()
        ]
    else:
        # Try to infer structure from column names
        prompt_candidates = ["prompt", "query", "question", "input", "instruction", "text"]
        response_candidates = ["response", "answer", "output", "completion", "target"]
        
        prompt_col = None
        for col in prompt_candidates:
            if col in dataset.column_names:
                prompt_col = col
                break
                
        response_col = None
        for col in response_candidates:
            if col in dataset.column_names:
                response_col = col
                break
        
        if prompt_col and response_col:
            result = [
                {"prompt": item[prompt_col], "response": item[response_col]}
                for item in tqdm(dataset, desc=f"Processing {prompt_col}-{response_col} pairs")
                if item[prompt_col].strip() and item[response_col].strip()
            ]
        else:
            logger.error("Could not infer dataset structure")
            return []
    
    # Limit the number of samples if specified
    if max_samples and len(result) > max_samples:
        logger.info(f"Limiting dataset to {max_samples} samples (from {len(result)})")
        result = random.sample(result, max_samples)
    
    logger.info(f"Preprocessed {len(result)} dialogue samples")
    return result


def preprocess_gsm8k_dataset(dataset: Dataset, max_samples: Optional[int] = None) -> List[Dict]:
    """
    Preprocess the GSM8K dataset into a list of prompt-response pairs.
    
    Args:
        dataset: The dataset to preprocess
        max_samples: Maximum number of samples to include
        
    Returns:
        List of dictionaries with 'prompt' and 'response' keys
    """
    logger.info("Preprocessing GSM8K dataset")
    
    result = []
    for item in tqdm(dataset, desc="Processing math problems"):
        if "question" in item and "answer" in item:
            # Format the prompt as a math problem
            prompt = f"Solve the following math problem step by step:\n\n{item['question']}"
            
            # Extract the answer, which often includes the solution steps
            response = item["answer"]
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    
    # Limit the number of samples if specified
    if max_samples and len(result) > max_samples:
        logger.info(f"Limiting dataset to {max_samples} samples (from {len(result)})")
        result = random.sample(result, max_samples)
    
    logger.info(f"Preprocessed {len(result)} math problems")
    return result


def preprocess_code_dataset(dataset: Dataset, max_samples: Optional[int] = None) -> List[Dict]:
    """
    Preprocess a code dataset into a list of prompt-response pairs.
    
    Args:
        dataset: The dataset to preprocess
        max_samples: Maximum number of samples to include
        
    Returns:
        List of dictionaries with 'prompt' and 'response' keys
    """
    logger.info("Preprocessing code dataset")
    
    result = []
    
    # Check for common code dataset structures
    if "instruction" in dataset.column_names and "response" in dataset.column_names:
        # Dataset has instruction-response format
        for item in tqdm(dataset, desc="Processing coding instructions"):
            prompt = item["instruction"]
            response = item["response"]
            
            # Add language hint if available
            if "language" in item:
                prompt = f"Write code in {item['language']}:\n{prompt}"
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    elif "problem" in dataset.column_names and "solution" in dataset.column_names:
        # Dataset has problem-solution format
        for item in tqdm(dataset, desc="Processing coding problems"):
            prompt = item["problem"]
            response = item["solution"]
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    elif "code" in dataset.column_names:
        # Dataset contains code snippets, create completion tasks
        for item in tqdm(dataset, desc="Processing code snippets"):
            code = item["code"]
            
            # Split the code into prompt and completion
            lines = code.split("\n")
            if len(lines) > 4:
                split_point = len(lines) // 2
                prompt = "\n".join(lines[:split_point])
                response = "\n".join(lines[split_point:])
                
                result.append({
                    "prompt": f"Complete the following code:\n\n{prompt}",
                    "response": response
                })
    else:
        # Try to infer structure from column names
        prompt_candidates = ["prompt", "input", "instruction", "context", "question"]
        response_candidates = ["response", "output", "completion", "answer", "solution", "target"]
        
        prompt_col = None
        for col in prompt_candidates:
            if col in dataset.column_names:
                prompt_col = col
                break
                
        response_col = None
        for col in response_candidates:
            if col in dataset.column_names:
                response_col = col
                break
        
        if prompt_col and response_col:
            result = [
                {"prompt": item[prompt_col], "response": item[response_col]}
                for item in tqdm(dataset, desc=f"Processing {prompt_col}-{response_col} pairs")
                if item[prompt_col].strip() and item[response_col].strip()
            ]
        else:
            logger.error("Could not infer dataset structure")
            return []
    
    # Limit the number of samples if specified
    if max_samples and len(result) > max_samples:
        logger.info(f"Limiting dataset to {max_samples} samples (from {len(result)})")
        result = random.sample(result, max_samples)
    
    logger.info(f"Preprocessed {len(result)} code samples")
    return result


def preprocess_summarization_dataset(dataset: Dataset, max_samples: Optional[int] = None) -> List[Dict]:
    """
    Preprocess a summarization dataset into a list of prompt-response pairs.
    
    Args:
        dataset: The dataset to preprocess
        max_samples: Maximum number of samples to include
        
    Returns:
        List of dictionaries with 'prompt' and 'response' keys
    """
    logger.info("Preprocessing summarization dataset")
    
    result = []
    
    # Check for common summarization dataset structures
    if "document" in dataset.column_names and "summary" in dataset.column_names:
        # Dataset has document-summary format
        for item in tqdm(dataset, desc="Processing documents"):
            prompt = f"Summarize the following text:\n\n{item['document']}"
            response = item["summary"]
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    elif "dialogue" in dataset.column_names and "summary" in dataset.column_names:
        # Dataset has dialogue-summary format (like DialogSum)
        for item in tqdm(dataset, desc="Processing dialogues"):
            prompt = f"Summarize the following dialogue:\n\n{item['dialogue']}"
            response = item["summary"]
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    elif "text" in dataset.column_names and "summary" in dataset.column_names:
        # Dataset has text-summary format
        for item in tqdm(dataset, desc="Processing texts"):
            prompt = f"Summarize the following text:\n\n{item['text']}"
            response = item["summary"]
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    else:
        # Try to infer structure from column names
        text_candidates = ["text", "document", "article", "content", "input", "dialogue"]
        summary_candidates = ["summary", "summaries", "abstract", "target", "output"]
        
        text_col = None
        for col in text_candidates:
            if col in dataset.column_names:
                text_col = col
                break
                
        summary_col = None
        for col in summary_candidates:
            if col in dataset.column_names:
                summary_col = col
                break
        
        if text_col and summary_col:
            result = [
                {
                    "prompt": f"Summarize the following text:\n\n{item[text_col]}", 
                    "response": item[summary_col]
                }
                for item in tqdm(dataset, desc=f"Processing {text_col}-{summary_col} pairs")
                if item[text_col].strip() and item[summary_col].strip()
            ]
        else:
            logger.error("Could not infer dataset structure")
            return []
    
    # Limit the number of samples if specified
    if max_samples and len(result) > max_samples:
        logger.info(f"Limiting dataset to {max_samples} samples (from {len(result)})")
        result = random.sample(result, max_samples)
    
    logger.info(f"Preprocessed {len(result)} summarization samples")
    return result


def preprocess_qa_dataset(dataset: Dataset, max_samples: Optional[int] = None) -> List[Dict]:
    """
    Preprocess a question-answering dataset into a list of prompt-response pairs.
    
    Args:
        dataset: The dataset to preprocess
        max_samples: Maximum number of samples to include
        
    Returns:
        List of dictionaries with 'prompt' and 'response' keys
    """
    logger.info("Preprocessing QA dataset")
    
    result = []
    
    # Check for common QA dataset structures
    if "question" in dataset.column_names and "answer" in dataset.column_names:
        # Dataset has question-answer format
        for item in tqdm(dataset, desc="Processing QA pairs"):
            prompt = item["question"]
            response = item["answer"]
            
            # Add context if available
            if "context" in item and item["context"]:
                prompt = f"Context: {item['context']}\n\nQuestion: {prompt}"
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    elif "input" in dataset.column_names and "output" in dataset.column_names:
        # Dataset has input-output format
        for item in tqdm(dataset, desc="Processing input-output pairs"):
            prompt = item["input"]
            response = item["output"]
            
            result.append({
                "prompt": prompt,
                "response": response
            })
    else:
        # Try to infer structure from column names
        question_candidates = ["question", "query", "input", "instruction"]
        answer_candidates = ["answer", "response", "output", "target"]
        context_candidates = ["context", "passage", "document", "text"]
        
        question_col = None
        for col in question_candidates:
            if col in dataset.column_names:
                question_col = col
                break
                
        answer_col = None
        for col in answer_candidates:
            if col in dataset.column_names:
                answer_col = col
                break
                
        context_col = None
        for col in context_candidates:
            if col in dataset.column_names:
                context_col = col
                break
        
        if question_col and answer_col:
            for item in tqdm(dataset, desc=f"Processing {question_col}-{answer_col} pairs"):
                prompt = item[question_col]
                
                # Add context if available
                if context_col and item.get(context_col):
                    prompt = f"Context: {item[context_col]}\n\nQuestion: {prompt}"
                
                result.append({
                    "prompt": prompt,
                    "response": item[answer_col]
                })
        else:
            logger.error("Could not infer dataset structure")
            return []
    
    # Limit the number of samples if specified
    if max_samples and len(result) > max_samples:
        logger.info(f"Limiting dataset to {max_samples} samples (from {len(result)})")
        result = random.sample(result, max_samples)
    
    logger.info(f"Preprocessed {len(result)} QA samples")
    return result


def preprocess_dataset(dataset: Dataset, dataset_spec: Dict, sample_size_override: Optional[int] = None) -> List[Dict]:
    """
    Preprocess a dataset using the specified preprocessing function.
    
    Args:
        dataset: The dataset to preprocess
        dataset_spec: Dataset specification
        sample_size_override: Override the max_samples setting
        
    Returns:
        List of dictionaries with 'prompt' and 'response' keys
    """
    preprocessing_fn_name = dataset_spec.get("preprocessing_fn", "preprocess_dialogue_dataset")
    max_samples = sample_size_override or dataset_spec.get("max_samples")
    
    # Get the preprocessing function
    preprocessing_fn = globals().get(preprocessing_fn_name)
    if not preprocessing_fn:
        logger.error(f"Preprocessing function {preprocessing_fn_name} not found")
        return []
    
    # Preprocess the dataset
    return preprocessing_fn(dataset, max_samples)


def save_processed_dataset(processed_data: List[Dict], dest_dir: str, dataset_spec: Dict) -> bool:
    """
    Save a processed dataset to a JSONL file.
    
    Args:
        processed_data: List of dictionaries with 'prompt' and 'response' keys
        dest_dir: Destination directory
        dataset_spec: Dataset specification
        
    Returns:
        True if the save was successful, False otherwise
    """
    agent_id = dataset_spec.get("agent_id")
    
    # Determine the destination path
    if agent_id is not None:
        # Save to agent-specific file
        output_path = os.path.join(dest_dir, f"{agent_id}.jsonl")
    else:
        # Extract a name from the repo_id
        name = dataset_spec["repo_id"].split("/")[-1]
        output_path = os.path.join(dest_dir, f"{name}.jsonl")
    
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the processed data to a JSONL file
        with open(output_path, "w", encoding="utf-8") as f:
            for item in processed_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        logger.info(f"Saved processed dataset to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving processed dataset to {output_path}: {e}")
        return False


def process_dataset(dest_dir: str, dataset_spec: Dict, force: bool = False, sample_size_override: Optional[int] = None) -> bool:
    """
    Process a dataset: download, preprocess, and save.
    
    Args:
        dest_dir: Destination directory
        dataset_spec: Dataset specification
        force: Force processing even if the dataset already exists
        sample_size_override: Override the max_samples setting
        
    Returns:
        True if the processing was successful, False otherwise
    """
    # Check if the processed dataset already exists
    if check_dataset_exists(dest_dir, dataset_spec) and not force:
        logger.info(f"Processed dataset already exists for agent_id {dataset_spec.get('agent_id')}, skipping")
        return True
    
    # Download the dataset
    dataset = download_dataset(dataset_spec)
    if dataset is None:
        return False
    
    # Preprocess the dataset
    processed_data = preprocess_dataset(dataset, dataset_spec, sample_size_override)
    if not processed_data:
        return False
    
    # Save the processed dataset
    return save_processed_dataset(processed_data, dest_dir, dataset_spec)


def main():
    """Main function to orchestrate the dataset processing."""
    args = parse_args()
    
    # Load the dataset list
    datasets = load_dataset_list(args.dataset_list)
    
    # Filter datasets by agent_id if specified
    if args.agent_id is not None:
        datasets = [d for d in datasets if d.get("agent_id") == args.agent_id]
        if not datasets:
            logger.error(f"No datasets found for agent_id {args.agent_id}")
            return 1
    
    # Create the destination directory if it doesn't exist
    os.makedirs(args.dest, exist_ok=True)
    
    # List datasets if --list-only is specified
    if args.list_only:
        logger.info("Datasets that would be processed:")
        for i, dataset in enumerate(datasets, 1):
            logger.info(f"{i}. {dataset.get('description', 'No description')} - {dataset['repo_id']}")
        return 0
    
    # Process each dataset
    success_count = 0
    for i, dataset in enumerate(datasets, 1):
        logger.info(f"Processing dataset {i}/{len(datasets)}")
        
        if process_dataset(args.dest, dataset, args.force, args.sample_size):
            success_count += 1
    
    # Log summary
    logger.info(f"Processing summary: {success_count}/{len(datasets)} datasets processed successfully")
    
    return 0 if success_count == len(datasets) else 1


if __name__ == "__main__":
    sys.exit(main())
