#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fine-tuning script for language models using PEFT/QLoRA

This script handles the fine-tuning of language models using Parameter-Efficient
Fine-Tuning techniques (specifically LoRA) with quantization for memory efficiency.
It is designed to be called as a subprocess by the LearningFlowRunner.
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from typing import Dict, List, Optional, Union, Any

import torch
import transformers
from datasets import load_dataset
from peft import (
    LoraConfig,
    PeftModel,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    TrainerCallback,
    TrainerControl,
    TrainerState,
    TrainingArguments,
)
from trl import SFTTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("train")

# Global flag for graceful shutdown
INTERRUPT_RECEIVED = False


class JsonMetricsCallback(TrainerCallback):
    """
    Callback to log metrics as JSON for easy parsing by the parent process.
    """
    
    def on_log(self, args, state, control, logs=None, **kwargs):
        """Called when the trainer logs metrics."""
        if not logs:
            return
            
        # Add step information if not present
        if "step" not in logs and state.global_step is not None:
            logs["step"] = state.global_step
            
        # Add epoch information if not present
        if "epoch" not in logs and state.epoch is not None:
            logs["epoch"] = state.epoch
            
        # Create a metrics JSON object and print it to stdout
        metrics_json = json.dumps({"metrics": logs})
        print(metrics_json, flush=True)


def setup_graceful_shutdown():
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        global INTERRUPT_RECEIVED
        if not INTERRUPT_RECEIVED:
            logger.info("Interrupt received. Will save model and exit after current step.")
            INTERRUPT_RECEIVED = True
        else:
            logger.info("Second interrupt received. Exiting immediately.")
            sys.exit(1)
            
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fine-tune a language model with PEFT/QLoRA")
    
    # Required arguments
    parser.add_argument("--model_path", type=str, required=True, help="Path to the base model")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to the training dataset")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save outputs")
    
    # Training hyperparameters
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for training")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--warmup_steps", type=int, default=100, help="Number of warmup steps")
    parser.add_argument("--max_steps", type=int, default=None, help="Maximum number of training steps")
    parser.add_argument("--save_steps", type=int, default=200, help="Steps between checkpoints")
    parser.add_argument("--eval_steps", type=int, default=200, help="Steps between evaluations")
    parser.add_argument("--logging_steps", type=int, default=10, help="Steps between logging")
    
    # LoRA parameters
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA attention dimension")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha parameter")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout probability")
    
    # Other parameters
    parser.add_argument("--max_seq_length", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--json_logging", action="store_true", help="Enable JSON logging for metrics")
    parser.add_argument("--eval_split", type=str, default=None, help="Dataset split to use for evaluation")
    parser.add_argument("--quantization", type=str, default="4bit", choices=["4bit", "8bit", "none"], 
                        help="Quantization type (4bit, 8bit, or none)")
    
    return parser.parse_args()


def load_and_prepare_model(args):
    """
    Load and prepare the model for training.
    
    Args:
        args: Command line arguments
        
    Returns:
        tuple: (model, tokenizer)
    """
    logger.info(f"Loading model from {args.model_path}")
    
    # Determine if we're using quantization
    if args.quantization == "4bit":
        logger.info("Using 4-bit quantization")
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    elif args.quantization == "8bit":
        logger.info("Using 8-bit quantization")
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
        )
    else:
        logger.info("Not using quantization")
        quantization_config = None
    
    # Load the model
    model_kwargs = {}
    if quantization_config:
        model_kwargs["quantization_config"] = quantization_config
        
    # Check if the model is a GGUF file
    if args.model_path.endswith(".gguf"):
        try:
            from llama_cpp import Llama
            logger.info("Detected GGUF model, using llama.cpp for inference")
            
            # For GGUF models, we'll use a different approach
            # This is a placeholder; in a real implementation, you'd integrate with llama.cpp
            raise NotImplementedError(
                "GGUF models are not yet supported for fine-tuning. "
                "Please use a Hugging Face model or convert your GGUF model."
            )
        except ImportError:
            logger.error("llama-cpp-python not installed, but required for GGUF models")
            raise
    else:
        # Load the model from Hugging Face
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            trust_remote_code=True,
            **model_kwargs
        )
    
    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path,
        trust_remote_code=True,
        use_fast=True
    )
    
    # Ensure the tokenizer has pad_token
    if tokenizer.pad_token is None:
        if tokenizer.eos_token is not None:
            tokenizer.pad_token = tokenizer.eos_token
        else:
            tokenizer.pad_token = tokenizer.eos_token = "</s>"
    
    # Prepare the model for k-bit training if using quantization
    if args.quantization in ["4bit", "8bit"]:
        model = prepare_model_for_kbit_training(model)
    
    return model, tokenizer


def load_and_prepare_dataset(args, tokenizer):
    """
    Load and prepare the dataset for training.
    
    Args:
        args: Command line arguments
        tokenizer: Tokenizer for the model
        
    Returns:
        dataset: Prepared dataset
    """
    logger.info(f"Loading dataset from {args.dataset_path}")
    
    # Determine the file format and load accordingly
    if args.dataset_path.endswith(".json") or args.dataset_path.endswith(".jsonl"):
        dataset = load_dataset("json", data_files=args.dataset_path)
    elif os.path.isdir(args.dataset_path):
        dataset = load_dataset(args.dataset_path)
    else:
        # Try to infer the format
        try:
            dataset = load_dataset(args.dataset_path)
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    logger.info(f"Dataset loaded: {dataset}")
    
    # Check if we need to split the dataset for evaluation
    if args.eval_split:
        if args.eval_split in dataset:
            train_dataset = dataset["train"]
            eval_dataset = dataset[args.eval_split]
        else:
            logger.warning(f"Eval split {args.eval_split} not found in dataset. Using train-test split.")
            # Split the dataset
            splits = dataset["train"].train_test_split(test_size=0.1, seed=args.seed)
            train_dataset = splits["train"]
            eval_dataset = splits["test"]
    else:
        # No evaluation dataset
        train_dataset = dataset["train"] if "train" in dataset else dataset
        eval_dataset = None
    
    logger.info(f"Train dataset size: {len(train_dataset)}")
    if eval_dataset:
        logger.info(f"Eval dataset size: {len(eval_dataset)}")
    
    return train_dataset, eval_dataset


def setup_peft_config(args):
    """
    Set up the PEFT configuration for LoRA.
    
    Args:
        args: Command line arguments
        
    Returns:
        LoraConfig: Configuration for LoRA
    """
    logger.info("Setting up LoRA configuration")
    
    # Set up LoRA config
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Common target modules for transformer models
    )
    
    return peft_config


def setup_training_arguments(args):
    """
    Set up the training arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        TrainingArguments: Configuration for training
    """
    logger.info("Setting up training arguments")
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_steps=args.warmup_steps,
        max_steps=args.max_steps,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        evaluation_strategy="steps" if args.eval_split else "no",
        eval_steps=args.eval_steps if args.eval_split else None,
        save_strategy="steps",
        load_best_model_at_end=True if args.eval_split else False,
        report_to="none",  # Disable wandb, tensorboard, etc.
        remove_unused_columns=False,
        push_to_hub=False,
        label_names=[],
        seed=args.seed,
    )
    
    return training_args


def train_model(args, model, tokenizer, train_dataset, eval_dataset=None):
    """
    Train the model using SFTTrainer.
    
    Args:
        args: Command line arguments
        model: Model to train
        tokenizer: Tokenizer for the model
        train_dataset: Training dataset
        eval_dataset: Evaluation dataset
        
    Returns:
        model: Trained model
    """
    logger.info("Setting up trainer")
    
    # Set up PEFT config
    peft_config = setup_peft_config(args)
    
    # Set up training arguments
    training_args = setup_training_arguments(args)
    
    # Set up callbacks
    callbacks = []
    if args.json_logging:
        callbacks.append(JsonMetricsCallback())
    
    # Create the trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=peft_config,
        dataset_text_field="text" if "text" in train_dataset.column_names else None,
        tokenizer=tokenizer,
        callbacks=callbacks,
        max_seq_length=args.max_seq_length,
    )
    
    # Add a custom callback to check for interruption
    class InterruptCallback(TrainerCallback):
        def on_step_end(self, args, state, control, **kwargs):
            if INTERRUPT_RECEIVED:
                logger.info("Interrupt received. Stopping training.")
                control.should_training_stop = True
    
    trainer.add_callback(InterruptCallback())
    
    # Train the model
    logger.info("Starting training")
    trainer.train()
    
    # Save the final model
    logger.info(f"Saving final model to {os.path.join(args.output_dir, 'adapter_model')}")
    trainer.save_model(os.path.join(args.output_dir, "adapter_model"))
    
    return model


def main():
    """Main function to run the training process."""
    # Set up graceful shutdown
    setup_graceful_shutdown()
    
    # Parse arguments
    args = parse_args()
    
    # Set random seed
    transformers.set_seed(args.seed)
    
    try:
        # Load and prepare the model
        model, tokenizer = load_and_prepare_model(args)
        
        # Load and prepare the dataset
        train_dataset, eval_dataset = load_and_prepare_dataset(args, tokenizer)
        
        # Train the model
        model = train_model(args, model, tokenizer, train_dataset, eval_dataset)
        
        logger.info("Training completed successfully")
        return 0
    except Exception as e:
        logger.exception(f"Error during training: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
