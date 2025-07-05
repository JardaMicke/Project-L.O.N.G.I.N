import logging
import asyncio
import os
import json
import uuid
from typing import Dict, Any, List, Optional

from ..storage import StorageManager, JsonStore, StorageType


class SuccessMonitorRecorderAgent:
    """
    SuccessMonitorRecorderAgent is responsible for capturing, storing, and retrieving
    details of successfully completed development flows or operations within the system.
    This agent contributes to the knowledge base by recording "good flows" for future reference
    and autonomous learning.

    SuccessMonitorRecorderAgent je zodpovědný za zachycování, ukládání a získávání
    detailů úspěšně dokončených vývojových toků nebo operací v rámci systému.
    Tento agent přispívá do znalostní báze zaznamenáváním "dobrých toků" pro budoucí reference
    a autonomní učení.
    """

    def __init__(self, config: dict, logger: logging.Logger, storage_manager: StorageManager):
        """
        Initializes the SuccessMonitorRecorderAgent with configuration, logger, and storage manager.

        Args:
            config (dict): Configuration dictionary for the agent.
            logger (logging.Logger): Logger instance for the agent.
            storage_manager (StorageManager): Instance of the storage manager for data persistence.

        Inicializuje SuccessMonitorRecorderAgent s konfigurací, loggerem a správcem úložiště.

        Argumenty:
            config (dict): Konfigurační slovník pro agenta.
            logger (logging.Logger): Instance loggeru pro agenta.
            storage_manager (StorageManager): Instance správce úložiště pro perzistenci dat.
        """
        self.config = config
        self.logger = logger
        self.storage_manager = storage_manager
        self.logger.info("SuccessMonitorRecorderAgent initialized.")

    async def record_successful_flow(self, flow_details: dict):
        """
        Records the details of a successfully completed development flow.
        This information is stored in the knowledge base for future analysis and learning.

        Args:
            flow_details (dict): A dictionary containing all relevant details of the successful flow,
                                 e.g., task description, agents involved, code changes, test results, etc.

        Zaznamená detaily úspěšně dokončeného vývojového toku.
        Tyto informace jsou uloženy do znalostní báze pro budoucí analýzu a učení.

        Argumenty:
            flow_details (dict): Slovník obsahující všechny relevantní detaily úspěšného toku,
                                 např. popis úkolu, zapojené agenty, změny kódu, výsledky testů atd.
        """
        self.logger.info(f"Recording successful flow: {flow_details.get('task_id', 'N/A')}")
        # Ensure the flow has a unique identifier
        task_id: str = flow_details.get("task_id") or str(uuid.uuid4())
        flow_details["task_id"] = task_id

        # Try to obtain an append-only knowledge-base store
        store = await self.storage_manager.select_store("knowledge_base", "append_only")

        # Fallback to JSON store if specialised store not configured yet
        if store is None:
            store = self.storage_manager.get_store(StorageType.JSON)

        if store is None:
            self.logger.error("No persistent store available for recording successful flows.")
            return

        try:
            await store.set(task_id, flow_details)
            self.logger.info(f"Successfully recorded flow under id '{task_id}'.")
        except Exception as e:
            self.logger.error(f"Failed to record successful flow '{task_id}': {e}", exc_info=True)

    async def get_recorded_flows(self, criteria: dict) -> List[dict]:
        """
        Retrieves previously recorded successful flows based on specified criteria.

        Args:
            criteria (dict): A dictionary specifying the search criteria (e.g., {'agent_type': 'coder', 'status': 'completed'}).

        Returns:
            List[dict]: A list of dictionaries, each representing a recorded successful flow that matches the criteria.

        Získá dříve zaznamenané úspěšné toky na základě zadaných kritérií.

        Argumenty:
            criteria (dict): Slovník specifikující kritéria vyhledávání (např. {'agent_type': 'coder', 'status': 'completed'}).

        Vrací:
            List[dict]: Seznam slovníků, každý reprezentující zaznamenaný úspěšný tok, který odpovídá kritériím.
        """
        self.logger.info(f"Retrieving recorded flows with criteria: {criteria}")

        store = await self.storage_manager.select_store("knowledge_base", "read_only")
        if store is None:
            store = self.storage_manager.get_store(StorageType.JSON)

        if store is None:
            self.logger.error("No store available for retrieving successful flows.")
            return []

        results: List[dict] = []

        # Simple implementation for JsonStore – iterate over files
        if isinstance(store, JsonStore):
            base_path = store.base_path  # type: ignore[attr-defined]
            for fname in os.listdir(base_path):
                if not fname.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(base_path, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if self._matches_criteria(data, criteria):
                        results.append(data)
                except Exception as e:
                    self.logger.warning(f"Skipping malformed flow file '{fname}': {e}")
        else:
            # Generic fallback: attempt to iterate keys if store supports it
            try:
                # Expecting the store to implement `list_keys` (not yet in interface)
                keys = await getattr(store, "list_keys")()  # type: ignore[attr-defined]
                for k in keys:
                    data = await store.get(k)
                    if data and self._matches_criteria(data, criteria):
                        results.append(data)
            except AttributeError:
                self.logger.warning("Store does not support listing keys; criteria filtering skipped.")

        self.logger.info(f"Retrieved {len(results)} flow(s) matching criteria.")
        return results

    # ------------------------------------------------------------------ #
    # Helper methods
    # ------------------------------------------------------------------ #

    @staticmethod
    def _matches_criteria(item: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """
        Simple recursive matcher to determine if an item satisfies all criteria.
        Supports nested dictionary keys using dot-notation.
        """
        for key, expected_val in criteria.items():
            # support dot notation for nested search
            parts = key.split(".")
            current_val: Any = item
            for part in parts:
                if isinstance(current_val, dict) and part in current_val:
                    current_val = current_val[part]
                else:
                    return False

            # Support callable criteria for advanced filtering
            if callable(expected_val):
                if not expected_val(current_val):
                    return False
            elif current_val != expected_val:
                return False
        return True
