import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import heapq

import tiktoken
from ..storage import StorageManager


class GarbageCollectorAgent:
    """
    GarbageCollectorAgent is responsible for intelligently managing the context window
    and archiving old or less relevant data to optimize system performance and resource usage.
    It maintains a token limit of 512 tokens with a chunk size of 128 tokens and chunk overlap of 32 tokens.

    GarbageCollectorAgent je zodpovědný za inteligentní správu kontextového okna
    a archivaci starých nebo méně relevantních dat pro optimalizaci výkonu systému a využití zdrojů.
    Udržuje limit tokenů 512 s velikostí chunku 128 tokenů a překryvem chunků 32 tokenů.
    """

    def __init__(self, config: dict, logger: logging.Logger, storage_manager: StorageManager):
        """
        Initializes the GarbageCollectorAgent with configuration, logger, and storage manager.

        Args:
            config (dict): Configuration dictionary for the agent.
            logger (logging.Logger): Logger instance for the agent.
            storage_manager (StorageManager): Instance of the storage manager for data persistence.

        Inicializuje GarbageCollectorAgent s konfigurací, loggerem a správcem úložiště.

        Argumenty:
            config (dict): Konfigurační slovník pro agenta.
            logger (logging.Logger): Instance loggeru pro agenta.
            storage_manager (StorageManager): Instance správce úložiště pro perzistenci dat.
        """
        self.config = config
        self.logger = logger
        self.storage_manager = storage_manager
        self.max_context_tokens = config.get("max_context_tokens", 512)
        self.chunk_size = config.get("chunk_size", 128)
        self.chunk_overlap = config.get("chunk_overlap", 32)
        self.warning_threshold = config.get("warning_threshold", 0.8)
        self.critical_threshold = config.get("critical_threshold", 0.95)
        self.logger.info("GarbageCollectorAgent initialized.")

    async def manage_context_window(self, current_context: List[dict]) -> List[dict]:
        """
        Manages the active context window, prioritizing and potentially trimming context
        to stay within defined token limits (default: 512 tokens).

        Args:
            current_context (List[dict]): The current list of context chunks or items.

        Returns:
            List[dict]: The optimized and managed context window.

        Spravuje aktivní kontextové okno, prioritizuje a případně ořezává kontext,
        aby zůstal v definovaných limitech tokenů (výchozí: 512 tokenů).

        Argumenty:
            current_context (List[dict]): Aktuální seznam kontextových chunků nebo položek.

        Vrací:
            List[dict]: Optimalizované a spravované kontextové okno.
        """
        # 1. Ensure each chunk has token size computed
        total_tokens = 0
        for chunk in current_context:
            if "size_tokens" not in chunk or chunk["size_tokens"] is None:
                chunk["size_tokens"] = self._count_tokens(chunk.get("content", ""))
            total_tokens += chunk["size_tokens"]

        self.logger.debug(f"Total tokens before GC: {total_tokens}")

        # 2. Build a min-heap keyed by (priority, last_accessed) to easily pop lowest-priority
        heap: List[tuple] = []
        for ch in current_context:
            # Lower priority value = more important, so heap by reverse
            priority_key = ch.get("priority", 2)
            last_access = ch.get("last_accessed") or datetime.utcnow()
            heapq.heappush(heap, (priority_key, last_access, ch))

        # 3. Trim if exceeds limits
        if total_tokens > self.max_context_tokens:
            self.logger.info(
                f"Context window exceeds limit ({total_tokens}/{self.max_context_tokens}). "
                "Archiving least important chunks."
            )
        while total_tokens > self.max_context_tokens and heap:
            _, _, victim = heapq.heappop(heap)
            await self._archive_chunk(victim)
            current_context.remove(victim)
            total_tokens -= victim["size_tokens"]

        self.logger.debug(f"Total tokens after GC: {total_tokens}")
        return current_context

    async def archive_old_data(self, criteria: dict):
        """
        Archives old or less frequently accessed data based on specified criteria.
        This data is moved from active storage to a more permanent archive.

        Args:
            criteria (dict): Criteria for identifying data to be archived (e.g., age, access count).

        Archivuje stará nebo méně často přístupná data na základě zadaných kritérií.
        Tato data jsou přesunuta z aktivního úložiště do trvalejšího archivu.

        Argumenty:
            criteria (dict): Kritéria pro identifikaci dat k archivaci (např. stáří, počet přístupů).
        """
        age_days: int = criteria.get("age_days", 30)
        threshold_date = datetime.utcnow() - timedelta(days=age_days)

        store = await self.storage_manager.select_store("log", "append_only")
        if not store:
            self.logger.warning("No archive store available.")
            return

        # Example criteria application – in practice we'd query persistent storage.
        # Here we only log the action.
        self.logger.info(
            f"Would archive chunks older than {threshold_date.isoformat()}. "
            "Real implementation depends on storage format."
        )

    async def _emergency_cleanup(self, needed_tokens: int):
        """
        Internal method for emergency cleanup when token limit is critically exceeded.
        Removes lowest priority chunks to make space for new, important content.

        Args:
            needed_tokens (int): Number of tokens that need to be freed up.

        self.logger.warning(f"Emergency cleanup requested for {needed_tokens} tokens.")
        # This is a stub; actual implementation would receive current_context
        # and archive until freed. For now, we just log.
        # Future hook: self.manage_context_window(...) with emergency flag.
        Argumenty:
            needed_tokens (int): Počet tokenů, které je třeba uvolnit.
        """
        self.logger.warning(f"Emergency cleanup requested for {needed_tokens} tokens (placeholder).")
        # Placeholder for actual emergency cleanup logic
        pass

    async def get_memory_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the context memory, including token usage and statistics.

        Returns:
            Dict[str, Any]: A dictionary containing memory status information.

        Vrací aktuální stav kontextové paměti, včetně využití tokenů a statistik.

        Vrací:
            Dict[str, Any]: Slovník obsahující informace o stavu paměti.
        """
        # In a full implementation, the agent would keep state of current_context.
        # Here we assume caller passes context when needed, so we return static info.
        status = {
            "total_tokens": self.max_context_tokens,
            "used_tokens": None,
            "available_tokens": None,
            "usage_percentage": None,
            "chunks_count": None,
            "status": "unknown",
        }
        return status

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #

    def _count_tokens(self, text: str) -> int:
        """Counts tokens of a text using tiktoken cl100k_base encoding."""
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(enc.encode(text))

    async def _archive_chunk(self, chunk: Dict[str, Any]):
        """Persists a context chunk to archive storage."""
        store = await self.storage_manager.select_store("log", "append_only")
        if not store:
            self.logger.warning("No archive store available, dropping chunk.")
            return
        archive_id = str(uuid.uuid4())
        await store.set(archive_id, chunk)
        self.logger.debug(f"Archived chunk {chunk.get('chunk_id')} as {archive_id}.")
