import logging
import asyncio
from typing import Dict, Any, List, Optional
import os
from urllib.parse import urlparse, quote_plus


class VisualValidatorAgent:
    """
    VisualValidatorAgent is responsible for performing visual validation of UI components
    or entire application states. It typically compares current UI with expected designs
    or previous successful states to detect regressions or discrepancies.

    VisualValidatorAgent je zodpovědný za provádění vizuální validace UI komponent
    nebo celých stavů aplikace. Obvykle porovnává aktuální UI s očekávanými návrhy
    nebo předchozími úspěšnými stavy k detekci regresí nebo nesrovnalostí.
    """

    def __init__(self, config: dict, logger: logging.Logger, mcp_client: Any):
        """
        Initializes the VisualValidatorAgent with configuration, logger, and MCP client.

        Args:
            config (dict): Configuration dictionary for the agent.
            logger (logging.Logger): Logger instance for the agent.
            mcp_client (Any): MCP client for tool access (type will be specified later).

        Inicializuje VisualValidatorAgent s konfigurací, loggerem a MCP klientem.

        Argumenty:
            config (dict): Konfigurační slovník pro agenta.
            logger (logging.Logger): Instance loggeru pro agenta.
            mcp_client (Any): MCP klient pro přístup k nástrojům (typ bude specifikován později).
        """
        self.config = config
        self.logger = logger
        self.mcp_client = mcp_client
        self.logger.info("VisualValidatorAgent initialized.")

    async def validate_ui(self, url: str, expected_elements: List[dict]) -> dict:
        """
        Performs visual validation of a given UI URL against a list of expected elements or states.
        This might involve taking screenshots, comparing them, or checking element properties.

        Args:
            url (str): The URL of the UI to validate.
            expected_elements (List[dict]): A list of dictionaries describing expected UI elements
                                           or visual states (e.g., {"selector": "#myButton", "color": "green"}).

        Returns:
            dict: A dictionary containing the validation results, including pass/fail status,
                  detected discrepancies, and potentially screenshot diffs.

        Provádí vizuální validaci dané URL UI proti seznamu očekávaných prvků nebo stavů.
        To může zahrnovat pořizování snímků obrazovky, jejich porovnávání nebo kontrolu vlastností prvků.

        Argumenty:
            url (str): URL UI k validaci.
            expected_elements (List[dict]): Seznam slovníků popisujících očekávané UI prvky
                                           nebo vizuální stavy (např. {"selector": "#myButton", "color": "green"}).

        Vrací:
            dict: Slovník obsahující výsledky validace, včetně stavu úspěchu/selhání,
                  zjištěných nesrovnalostí a případně rozdílů snímků obrazovky.
        """
        self.logger.info(f"Performing visual validation for URL: {url}")
        self.logger.info(f"Expected elements: {expected_elements}")

        # 1. Take screenshot of current URL
        take_response = await self.mcp_client.handle_request(
            tool_name="browser.take_screenshot",
            args={"url": url}
        )
        if not take_response.get("success"):
            return {"success": False, "error": f"Failed to take screenshot: {take_response.get('error')}"}

        screenshot_path = take_response["result"].get("screenshot_path")
        if not screenshot_path:
            return {"success": False, "error": "Screenshot path missing from MCP response."}

        # 2. Determine baseline image (expected) to compare against
        baseline_dir = self.config.get("baseline_dir", "./baseline_screens")
        os.makedirs(baseline_dir, exist_ok=True)
        baseline_filename = f"{self._slugify_url(url)}.png"
        baseline_path = os.path.join(baseline_dir, baseline_filename)

        if not os.path.exists(baseline_path):
            # First time run – save current as baseline
            self.logger.info(f"No baseline found for {url}. Saving current screenshot as baseline.")
            await self.mcp_client.handle_request(
                tool_name="file.write",
                args={"path": baseline_path, "content": ""}  # write empty to create dir entry
            )
            # copy via MCP
            await self.mcp_client.handle_request(
                tool_name="file.copy",
                args={"src": screenshot_path, "dst": baseline_path}
            )
            return {"success": True, "discrepancies_found": 0,
                    "details": "Baseline created; no comparison performed.",
                    "screenshot_diff_url": None}

        # 3. Compare screenshots
        compare_response = await self.mcp_client.handle_request(
            tool_name="screenshot.compare",
            args={"base": baseline_path, "current": screenshot_path}
        )
        if not compare_response.get("success"):
            return {"success": False, "error": f"Comparison failed: {compare_response.get('error')}"}

        diff = compare_response["result"]
        discrepancies = diff.get("mismatch_count", 0)
        status = "success" if discrepancies == 0 else "fail"

        return {
            "success": True,
            "status": status,
            "discrepancies_found": discrepancies,
            "screenshot_diff_url": diff.get("diff_path"),
        }

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #

    def _slugify_url(self, url: str) -> str:
        """
        Converts a URL into a safe filename slug.
        """
        parsed = urlparse(url)
        netloc = parsed.netloc.replace(":", "_")
        path = quote_plus(parsed.path.strip("/"))
        return f"{netloc}_{path or 'root'}"
