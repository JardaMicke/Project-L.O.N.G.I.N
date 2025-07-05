import logging
import asyncio
import json
from typing import Dict, Any, List, Optional


class TestOracleAgent:
    """
    TestOracleAgent is responsible for generating and managing tests based on requirements.
    It creates test specifications that are used by the CodeAlchemist to implement code
    that passes these tests, following the Test-Driven Development approach.

    TestOracleAgent je zodpovědný za generování a správu testů na základě požadavků.
    Vytváří testové specifikace, které jsou používány CodeAlchemistem k implementaci kódu,
    který těmito testy projde, podle přístupu Test-Driven Development.
    """

    def __init__(self, config: dict, logger: logging.Logger, mcp_client: Any):
        """
        Initializes the TestOracleAgent with configuration, logger, and MCP client.

        Args:
            config (dict): Configuration dictionary for the agent.
            logger (logging.Logger): Logger instance for the agent.
            mcp_client (Any): MCP client for tool access (type will be specified later).

        Inicializuje TestOracleAgent s konfigurací, loggerem a MCP klientem.

        Argumenty:
            config (dict): Konfigurační slovník pro agenta.
            logger (logging.Logger): Instance loggeru pro agenta.
            mcp_client (Any): MCP klient pro přístup k nástrojům (typ bude specifikován později).
        """
        self.config = config
        self.logger = logger
        self.mcp_client = mcp_client
        self.model = config.get("model", "tester") # Assumes a model alias 'tester' is configured
        self.logger.info("TestOracleAgent initialized.")

    async def _call_llm_for_json(self, prompt: str) -> Optional[List[Dict[str, Any]]]:
        """Helper to call an LLM and parse its JSON list response."""
        self.logger.debug(f"Calling LLM for test generation with prompt: {prompt[:100]}...")
        response = await self.mcp_client.handle_request(
            tool_name="llm.generate",
            args={"model": self.model, "prompt": prompt}
        )
        if not response.get("success"):
            self.logger.error(f"LLM call failed: {response.get('error')}")
            return None
        
        content = response.get("result", {}).get("text", "")
        try:
            # The LLM should return a JSON array of test objects
            tests = json.loads(content)
            if isinstance(tests, list):
                return tests
            self.logger.warning(f"LLM returned a non-list JSON object: {type(tests)}")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from LLM response: {content}")
            return None

    async def generate_tests(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates test specifications based on the provided requirements.
        These tests will be used to guide the implementation of code.
        """
        self.logger.info(f"Generating tests for requirements: {requirements.get('description', 'N/A')}")
        
        prompt = f"""
You are TestOracleAgent. Your task is to generate a comprehensive list of test specifications based on the provided requirements.
The output must be a valid JSON array of objects. Each object should represent a single test and include keys like 'test_id', 'description', 'test_type' (e.g., 'unit', 'integration'), 'priority' ('high', 'medium', 'low'), 'inputs', and 'expected_output'.

Requirements:
{json.dumps(requirements, indent=2)}

Generate the JSON array of test specifications now.
"""
        tests = await self._call_llm_for_json(prompt)
        return tests or []

    async def update_tests(self, changes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Updates existing tests based on changes to requirements or implementation.
        """
        self.logger.info(f"Updating tests based on changes: {changes.get('reason', 'N/A')}")
        
        prompt = f"""
You are TestOracleAgent. Your task is to update the provided list of test specifications based on the given changes.
The output must be a valid JSON array of objects representing the new, complete list of tests.

Original Tests:
{json.dumps(changes.get('original_tests', []), indent=2)}

Required Changes (e.g., failed test feedback, new requirements):
{json.dumps(changes.get('feedback', {}), indent=2)}

Generate the updated JSON array of test specifications now.
"""
        updated_tests = await self._call_llm_for_json(prompt)
        return updated_tests or changes.get('original_tests', [])

    async def validate_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates the results of executed tests and provides feedback.
        """
        self.logger.info(f"Validating {len(test_results)} test results.")
        
        passed_count = 0
        failed_count = 0
        failed_tests_feedback = []

        for result in test_results:
            if result.get("status") == "passed":
                passed_count += 1
            else:
                failed_count += 1
                feedback = {
                    "test_id": result.get("test_id"),
                    "description": result.get("description"),
                    "reason": result.get("error", "Test failed with no specific error message."),
                    "actual_output": result.get("actual_output"),
                }
                failed_tests_feedback.append(feedback)

        is_success = failed_count == 0
        report = {
            "success": is_success,
            "passed": passed_count,
            "failed": failed_count,
            "total": len(test_results),
            "feedback": failed_tests_feedback if not is_success else "All tests passed successfully."
        }
        
        self.logger.info(f"Validation report: {passed_count} passed, {failed_count} failed.")
        return report

    async def generate_edge_case_tests(self, base_tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates additional tests for edge cases based on existing tests.
        """
        self.logger.info(f"Generating edge case tests from {len(base_tests)} base tests.")
        
        prompt = f"""
You are TestOracleAgent. Your task is to generate a list of edge case test specifications based on the provided base tests.
Consider scenarios like empty inputs, invalid data types, null values, large inputs, and security vulnerabilities.
The output must be a valid JSON array of objects, following the same format as the base tests.

Base Tests:
{json.dumps(base_tests, indent=2)}

Generate the JSON array of edge case test specifications now.
"""
        edge_tests = await self._call_llm_for_json(prompt)
        return edge_tests or []
