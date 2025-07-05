#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Test Script for Mini-Agent System

This script tests the API endpoints for the Mini-Agent system, including
listing agents, retrieving agent details, training agents, chatting with
agents, and getting agent status.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List, Optional

import httpx
from httpx import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("api_test")

# API configuration
API_BASE_URL = "http://localhost:8000"  # Adjust as needed
TIMEOUT = 30.0  # Timeout for API requests in seconds


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    json_data: Optional[Dict[str, Any]] = None,
    expected_status: int = 200
) -> Dict[str, Any]:
    """
    Make an HTTP request to the API and handle errors.
    
    Args:
        client: httpx AsyncClient
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (without base URL)
        json_data: JSON data for POST requests
        expected_status: Expected HTTP status code
        
    Returns:
        Response data as dict
    """
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    logger.info(f"Making {method} request to {url}")
    
    try:
        response = await client.request(
            method=method,
            url=url,
            json=json_data,
            timeout=TIMEOUT
        )
        
        # Check status code
        if response.status_code != expected_status:
            logger.error(f"Unexpected status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise ValueError(f"Expected status code {expected_status}, got {response.status_code}")
        
        # Parse JSON response
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            raise ValueError("Invalid JSON response")
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise


async def test_list_agents(client: httpx.AsyncClient) -> bool:
    """
    Test the GET /agents endpoint.
    
    Args:
        client: httpx AsyncClient
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info("Testing GET /agents endpoint")
    
    try:
        response_data = await make_request(client, "GET", "/agents")
        
        # Assertions
        assert isinstance(response_data, list), "Response should be a list"
        
        # Log the agents
        logger.info(f"Found {len(response_data)} agents")
        for agent in response_data:
            logger.info(f"Agent: {agent}")
            
            # Verify agent structure
            assert "id" in agent, "Agent should have an id"
            assert "name" in agent, "Agent should have a name"
            
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def test_get_agent(client: httpx.AsyncClient, agent_id: int = 0) -> bool:
    """
    Test the GET /agents/{agent_id} endpoint.
    
    Args:
        client: httpx AsyncClient
        agent_id: ID of the agent to retrieve
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info(f"Testing GET /agents/{agent_id} endpoint")
    
    try:
        response_data = await make_request(client, "GET", f"/agents/{agent_id}")
        
        # Assertions
        assert isinstance(response_data, dict), "Response should be a dictionary"
        
        # Verify agent structure
        assert "id" in response_data, "Agent should have an id"
        assert "name" in response_data, "Agent should have a name"
        assert "model_path" in response_data, "Agent should have a model_path"
        assert "dataset_path" in response_data, "Agent should have a dataset_path"
        assert "statistics" in response_data, "Agent should have statistics"
        
        # Log the agent details
        logger.info(f"Agent details: {response_data}")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def test_train_agent(client: httpx.AsyncClient, agent_id: int = 0) -> bool:
    """
    Test the POST /agents/{agent_id}/train endpoint.
    
    Args:
        client: httpx AsyncClient
        agent_id: ID of the agent to train
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info(f"Testing POST /agents/{agent_id}/train endpoint")
    
    try:
        # Use the shortest training duration for testing
        json_data = {
            "duration": "1h"
        }
        
        response_data = await make_request(
            client, 
            "POST", 
            f"/agents/{agent_id}/train", 
            json_data=json_data
        )
        
        # Assertions
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "status" in response_data, "Response should have a status"
        
        # Log the response
        logger.info(f"Training response: {response_data}")
        
        # Check if training was started successfully
        if response_data.get("status") == "ok":
            logger.info("Training started successfully")
            
            # Check for results
            assert "results" in response_data, "Response should have results"
            results = response_data.get("results", {})
            
            # Log training details
            logger.info(f"Run ID: {results.get('run_id')}")
            logger.info(f"State: {results.get('state')}")
            
            return True
        else:
            logger.warning(f"Training not started: {response_data.get('message')}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def test_chat_with_agent(client: httpx.AsyncClient, agent_id: int = 0) -> bool:
    """
    Test the POST /agents/{agent_id}/chat endpoint.
    
    Args:
        client: httpx AsyncClient
        agent_id: ID of the agent to chat with
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info(f"Testing POST /agents/{agent_id}/chat endpoint")
    
    try:
        # Create a simple chat message
        json_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! Can you tell me about yourself?"
                }
            ],
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 100
        }
        
        response_data = await make_request(
            client, 
            "POST", 
            f"/agents/{agent_id}/chat", 
            json_data=json_data
        )
        
        # Assertions
        assert isinstance(response_data, dict), "Response should be a dictionary"
        
        # Check for error response
        if "status" in response_data and response_data.get("status") == "error":
            logger.warning(f"Chat failed: {response_data.get('message')}")
            return False
        
        # Check for OpenAI-style response
        assert "choices" in response_data, "Response should have choices"
        choices = response_data.get("choices", [])
        assert len(choices) > 0, "Response should have at least one choice"
        
        # Log the response
        choice = choices[0]
        if "message" in choice:
            message = choice["message"]
            logger.info(f"Agent response: {message.get('content')}")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def test_get_agent_status(client: httpx.AsyncClient, agent_id: int = 0) -> bool:
    """
    Test the GET /agents/{agent_id}/status endpoint.
    
    Args:
        client: httpx AsyncClient
        agent_id: ID of the agent to get status for
        
    Returns:
        True if the test passed, False otherwise
    """
    logger.info(f"Testing GET /agents/{agent_id}/status endpoint")
    
    try:
        response_data = await make_request(client, "GET", f"/agents/{agent_id}/status")
        
        # Assertions
        assert isinstance(response_data, dict), "Response should be a dictionary"
        
        # Verify status structure
        assert "id" in response_data, "Status should have an id"
        assert "name" in response_data, "Status should have a name"
        assert "statistics" in response_data, "Status should have statistics"
        
        # Log the status
        logger.info(f"Agent status: {response_data}")
        
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def main():
    """Main function to run all tests."""
    logger.info("Starting API tests")
    
    # Create an HTTP client
    async with httpx.AsyncClient() as client:
        # Run tests
        tests = [
            ("List Agents", test_list_agents(client)),
            ("Get Agent", test_get_agent(client)),
            ("Get Agent Status", test_get_agent_status(client)),
            ("Chat with Agent", test_chat_with_agent(client)),
            ("Train Agent", test_train_agent(client)),
        ]
        
        # Execute tests and collect results
        results = []
        for test_name, test_coro in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = await test_coro
                results.append((test_name, result))
                logger.info(f"Test {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Print summary
        logger.info("\n=== Test Summary ===")
        passed = 0
        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nPassed {passed}/{len(results)} tests")


if __name__ == "__main__":
    asyncio.run(main())
