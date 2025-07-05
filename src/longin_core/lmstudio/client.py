#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Studio API Client

This module provides an asynchronous client for interacting with LM Studio's API,
which follows the OpenAI API format. It supports listing models, creating chat
completions, and streaming responses.
"""

import asyncio
import json
import logging
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field, root_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lmstudio_client")


# Custom exceptions
class LMStudioClientError(Exception):
    """Base exception for LM Studio client errors"""
    pass


class LMStudioAPIError(LMStudioClientError):
    """Exception raised for API errors returned by LM Studio"""
    def __init__(self, status_code: int, message: str, response_data: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data
        super().__init__(f"LM Studio API error ({status_code}): {message}")


class LMStudioConnectionError(LMStudioClientError):
    """Exception raised for connection errors with LM Studio"""
    pass


# Pydantic models for API data
class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str
    name: Optional[str] = None


class ModelData(BaseModel):
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: str = "user"


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelData]


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None


class StreamedChatCompletionDelta(BaseModel):
    role: Optional[ChatRole] = None
    content: Optional[str] = None


class StreamedChatCompletionChoice(BaseModel):
    index: int
    delta: StreamedChatCompletionDelta
    finish_reason: Optional[str] = None


class StreamedChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamedChatCompletionChoice]


class AsyncLMStudioClient:
    """
    Asynchronous client for interacting with LM Studio's API.
    """

    def __init__(self, base_url: str = "http://localhost:1234", api_key: Optional[str] = None):
        """
        Initialize the LM Studio client.

        Args:
            base_url: Base URL for the LM Studio API (default: http://localhost:1234)
            api_key: API key for authentication (optional, as local LM Studio doesn't require it)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = None
        logger.info(f"Initialized LM Studio client with base URL: {base_url}")

    async def _ensure_session(self) -> httpx.AsyncClient:
        """Ensure an HTTP session exists and return it."""
        if self.session is None or self.session.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = httpx.AsyncClient(headers=headers, timeout=60.0)
        return self.session

    async def _request(
        self, method: str, endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], httpx.Response]:
        """
        Make a request to the LM Studio API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON data for POST requests
            stream: Whether to stream the response

        Returns:
            Response data as dict or raw response for streaming
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._ensure_session()

        try:
            logger.debug(f"Making {method} request to {url}")
            response = await session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                stream=stream
            )

            if stream and response.status_code == 200:
                return response

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                except Exception:
                    error_message = response.text or "Unknown error"
                    error_data = None

                raise LMStudioAPIError(
                    status_code=response.status_code,
                    message=error_message,
                    response_data=error_data
                )

            return response.json()

        except httpx.RequestError as e:
            raise LMStudioConnectionError(f"Failed to connect to LM Studio: {str(e)}")
        except json.JSONDecodeError:
            raise LMStudioAPIError(
                status_code=response.status_code,
                message="Invalid JSON response from LM Studio"
            )

    async def get_models(self) -> ModelList:
        """
        Get a list of available models from LM Studio.

        Returns:
            ModelList: List of available models
        """
        logger.info("Fetching available models from LM Studio")
        response = await self._request("GET", "v1/models")
        return ModelList.parse_obj(response)

    async def create_chat_completion(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        top_p: float = 1.0,
        n: int = 1,
        max_tokens: Optional[int] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> ChatCompletionResponse:
        """
        Create a chat completion with the specified model and messages.

        Args:
            model: Model ID to use
            messages: List of chat messages
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter (0-1)
            n: Number of completions to generate
            max_tokens: Maximum number of tokens to generate
            presence_penalty: Presence penalty (-2 to 2)
            frequency_penalty: Frequency penalty (-2 to 2)
            stop: Sequences where the API will stop generating further tokens

        Returns:
            ChatCompletionResponse: The completion response
        """
        logger.info(f"Creating chat completion with model: {model}")
        
        # Convert Pydantic models to dict for the request
        messages_dict = [msg.dict(exclude_none=True) for msg in messages]
        
        payload = {
            "model": model,
            "messages": messages_dict,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
            
        if stop is not None:
            payload["stop"] = stop
            
        response = await self._request("POST", "v1/chat/completions", json_data=payload)
        return ChatCompletionResponse.parse_obj(response)

    async def stream_chat_completion(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        top_p: float = 1.0,
        n: int = 1,
        max_tokens: Optional[int] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> AsyncGenerator[StreamedChatCompletionResponse, None]:
        """
        Stream a chat completion with the specified model and messages.

        Args:
            model: Model ID to use
            messages: List of chat messages
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter (0-1)
            n: Number of completions to generate
            max_tokens: Maximum number of tokens to generate
            presence_penalty: Presence penalty (-2 to 2)
            frequency_penalty: Frequency penalty (-2 to 2)
            stop: Sequences where the API will stop generating further tokens

        Yields:
            StreamedChatCompletionResponse: Chunks of the completion response
        """
        logger.info(f"Streaming chat completion with model: {model}")
        
        # Convert Pydantic models to dict for the request
        messages_dict = [msg.dict(exclude_none=True) for msg in messages]
        
        payload = {
            "model": model,
            "messages": messages_dict,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": True,
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
            
        if stop is not None:
            payload["stop"] = stop
            
        response = await self._request("POST", "v1/chat/completions", json_data=payload, stream=True)
        
        try:
            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("data: "):
                    line = line[6:]  # Remove "data: " prefix
                    
                if line == "[DONE]":
                    break
                    
                try:
                    chunk_data = json.loads(line)
                    chunk = StreamedChatCompletionResponse.parse_obj(chunk_data)
                    yield chunk
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse streaming response chunk: {line}")
        finally:
            await response.aclose()

    async def load_model(self, model_path: str) -> Dict[str, Any]:
        """
        Load a model from a local path into LM Studio.
        
        Args:
            model_path: Path to the model file (GGUF or other supported format)
            
        Returns:
            Dict with the response from LM Studio
        """
        logger.info(f"Loading model from path: {model_path}")
        payload = {
            "path": model_path
        }
        
        try:
            # Try using the API endpoint first (if available)
            response = await self._request("POST", "v1/models/load", json_data=payload)
            logger.info(f"Model loaded successfully via API: {model_path}")
            return response
        except (LMStudioAPIError, LMStudioConnectionError) as e:
            logger.warning(f"Failed to load model via API: {e}")
            logger.info("Attempting to load model via LM Studio CLI...")
            
            # Fallback to CLI if API fails
            try:
                # This is a placeholder. In a real implementation, we would use
                # subprocess.run to call the LM Studio CLI
                logger.warning("LM Studio CLI loading not implemented yet. Please load the model manually.")
                return {"status": "error", "message": "API loading failed, CLI not implemented"}
            except Exception as e:
                logger.error(f"Failed to load model via CLI: {e}")
                raise LMStudioClientError(f"Failed to load model {model_path}: {str(e)}")

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.is_closed:
            await self.session.aclose()
            logger.debug("Closed HTTP session")


async def main():
    """Example usage of the LM Studio client."""
    client = AsyncLMStudioClient()
    
    try:
        # List available models
        print("Fetching available models...")
        models = await client.get_models()
        print(f"Available models: {[model.id for model in models.data]}")
        
        if not models.data:
            print("No models available. Please load a model in LM Studio first.")
            return
            
        # Use the first available model
        model_id = models.data[0].id
        
        # Create a chat completion
        print(f"\nCreating chat completion with model {model_id}...")
        messages = [
            ChatMessage(role=ChatRole.USER, content="Hello! Can you tell me about LM Studio?")
        ]
        
        response = await client.create_chat_completion(model_id, messages)
        print(f"Response: {response.choices[0].message.content}")
        
        # Stream a chat completion
        print("\nStreaming chat completion...")
        messages = [
            ChatMessage(role=ChatRole.USER, content="Write a short poem about AI.")
        ]
        
        full_response = ""
        async for chunk in client.stream_chat_completion(model_id, messages):
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        
        print("\n\nFull streamed response:", full_response)
        
    except LMStudioClientError as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
