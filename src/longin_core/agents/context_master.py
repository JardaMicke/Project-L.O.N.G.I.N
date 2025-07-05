import logging
import asyncio
from typing import Dict, Any, List, Optional
from ..storage import StorageManager


class ContextMasterAgent:
    """
    ContextMasterAgent is responsible for gathering, managing, and providing context
    for other agents in the system. It handles vector database operations, chunking,
    and retrieval of relevant context based on task descriptions.

    ContextMasterAgent je zodpovědný za shromažďování, správu a poskytování kontextu
    pro ostatní agenty v systému. Zajišťuje operace s vektorovou databází, chunking
    a získávání relevantního kontextu na základě popisů úkolů.
    """

    def __init__(self, config: dict, logger: logging.Logger, storage_manager: StorageManager, mcp_client: Any):
        """
        Initializes the ContextMasterAgent with configuration, logger, storage manager, and MCP client.

        Args:
            config (dict): Configuration dictionary for the agent.
            logger (logging.Logger): Logger instance for the agent.
            storage_manager (StorageManager): Storage manager for accessing different storage types.
            mcp_client (Any): MCP client for tool access (type will be specified later).

        Inicializuje ContextMasterAgent s konfigurací, loggerem, správcem úložiště a MCP klientem.

        Argumenty:
            config (dict): Konfigurační slovník pro agenta.
            logger (logging.Logger): Instance loggeru pro agenta.
            storage_manager (StorageManager): Správce úložiště pro přístup k různým typům úložišť.
            mcp_client (Any): MCP klient pro přístup k nástrojům (typ bude specifikován později).
        """
        self.config = config
        self.logger = logger
        self.storage_manager = storage_manager
        self.mcp_client = mcp_client
        self.context_window_size = config.get("context_window_size", 512)
        self.chunk_size = config.get("chunk_size", 128)
        self.logger.info("ContextMasterAgent initialized.")

    async def gather_context(self, task_description: str) -> Dict[str, Any]:
        """
        Gathers relevant context based on the given task description.
        Uses vector similarity search to find the most relevant chunks of information.

        Args:
            task_description (str): Description of the task for which context is needed.

        Returns:
            Dict[str, Any]: The gathered context information.

        Shromažďuje relevantní kontext na základě zadaného popisu úkolu.
        Používá vektorové vyhledávání podobnosti k nalezení nejrelevantnějších částí informací.

        Argumenty:
            task_description (str): Popis úkolu, pro který je kontext potřeba.

        Vrací:
            Dict[str, Any]: Shromážděné kontextové informace.
        """
        self.logger.info(f"Gathering context for task: {task_description}")
        
        # ------------------------------------------------------------------
        # 1) Získáme seznam souborů v repozitáři pomocí MCP file.list
        # ------------------------------------------------------------------
        try:
            list_resp = await self.mcp_client.handle_request(
                "file.list", {"path": self.config.get("repo_root", ".")}
            )
            if not list_resp.get("success"):
                raise RuntimeError(list_resp.get("error", "Unknown MCP error"))
            file_list: List[str] = list_resp["result"]
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to list files via MCP: %s", exc, exc_info=True)
            return {
                "task": task_description,
                "context_chunks": [],
                "sources": [],
                "tokens_used": 0,
                "status": "mcp_error",
                "error": str(exc),
            }

        # ------------------------------------------------------------------
        # 2) Filtrování souborů dle relevance (jednoduše podle výskytu klíčových slov)
        # ------------------------------------------------------------------
        keywords = {w.lower() for w in task_description.split() if len(w) > 2}
        candidate_files = [
            f
            for f in file_list
            if any(kw in f.lower() for kw in keywords)
            and any(f.endswith(ext) for ext in (".py", ".md", ".txt"))
        ]
        # Omezíme počet zpracovaných souborů kvůli výkonu
        max_files = self.config.get("max_files", 10)
        candidate_files = candidate_files[:max_files]

        self.logger.info("Context candidate files: %s", candidate_files)

        all_chunks: List[Dict[str, Any]] = []
        sources: List[str] = []
        tokens_used = 0

        # ------------------------------------------------------------------
        # 3) Načteme a chunkujeme obsah každého souboru
        # ------------------------------------------------------------------
        for filepath in candidate_files:
            try:
                read_resp = await self.mcp_client.handle_request(
                    "file.read", {"path": filepath}
                )
                if not read_resp.get("success"):
                    self.logger.warning("Cannot read %s: %s", filepath, read_resp.get("error"))
                    continue
                content: str = read_resp["result"]
                file_chunks = await self.chunk_document(
                    content, {"title": filepath, "path": filepath}
                )
                all_chunks.extend(file_chunks)
                sources.append(filepath)

                # Přibližný počet tokenů (1 znak = ~0.25 tokenu, hrubý odhad)
                tokens_used += max(1, len(content) // 4)

                # Respektujeme limit kontextového okna
                if tokens_used >= self.context_window_size:
                    self.logger.info("Context window limit reached, stopping further reads.")
                    break
            except Exception as exc:  # noqa: BLE001
                self.logger.error("Error while processing %s: %s", filepath, exc, exc_info=True)
                continue

        status = "ok" if all_chunks else "no_relevant_files"
        return {
            "task": task_description,
            "context_chunks": all_chunks,
            "sources": sources,
            "tokens_used": tokens_used,
            "status": status,
        }

    async def manage_vector_db(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manages operations on the vector database, such as adding, updating, or querying vectors.

        Args:
            operation (str): The operation to perform ('add', 'update', 'query', 'delete').
            data (Dict[str, Any]): Data relevant to the operation.

        Returns:
            Dict[str, Any]: Result of the operation.

        Spravuje operace s vektorovou databází, jako je přidávání, aktualizace nebo dotazování vektorů.

        Argumenty:
            operation (str): Operace, která má být provedena ('add', 'update', 'query', 'delete').
            data (Dict[str, Any]): Data relevantní pro operaci.

        Vrací:
            Dict[str, Any]: Výsledek operace.
        """
        self.logger.info(f"Vector DB operation: {operation}")
        
        # Placeholder for actual implementation
        self.logger.info("Vector DB management (placeholder).")
        
        # Get the vector store from storage manager
        vector_store = await self.storage_manager.get_store("postgres_vector")
        
        # Simulated operation result
        return {
            "operation": operation,
            "status": "placeholder",
            "result": None
        }

    async def chunk_document(self, document: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks a document into smaller pieces for efficient storage and retrieval.

        Args:
            document (str): The document to chunk.
            metadata (Dict[str, Any]): Metadata about the document.

        Returns:
            List[Dict[str, Any]]: List of document chunks with their metadata.

        Rozdělí dokument na menší části pro efektivní ukládání a získávání.

        Argumenty:
            document (str): Dokument k rozdělení.
            metadata (Dict[str, Any]): Metadata o dokumentu.

        Vrací:
            List[Dict[str, Any]]: Seznam částí dokumentu s jejich metadaty.
        """
        self.logger.info(f"Chunking document: {metadata.get('title', 'Untitled')}")
        
        # Placeholder for actual implementation
        self.logger.info("Document chunking (placeholder).")
        
        # Simulated chunking result
        return [
            {
                "chunk_id": "placeholder_chunk_1",
                "content": "Placeholder chunk content 1",
                "metadata": metadata,
                "embedding": None
            }
        ]

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the given text using an embedding model.

        Args:
            text (str): The text to generate an embedding for.

        Returns:
            List[float]: The generated embedding vector.

        Generuje vektorový embedding pro zadaný text pomocí embedding modelu.

        Argumenty:
            text (str): Text, pro který se má vygenerovat embedding.

        Vrací:
            List[float]: Vygenerovaný embedding vektor.
        """
        self.logger.info(f"Generating embedding for text (length: {len(text)})")
        
        # Placeholder for actual implementation
        self.logger.info("Embedding generation (placeholder).")
        
        # Simulated embedding result (just zeros for placeholder)
        return [0.0] * 384  # Typical embedding dimension
