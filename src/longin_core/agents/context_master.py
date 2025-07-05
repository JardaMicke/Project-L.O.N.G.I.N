
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional

import tiktoken
from ..storage import StorageManager, StorageType


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

    async def gather_context(self, task_description: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Gathers relevant context based on the given task description.
        Uses vector similarity search to find the most relevant chunks of information.

        Args:
            task_description (str): Description of the task for which context is needed.
            top_k (int): The number of top similar chunks to retrieve.

        Returns:
            Dict[str, Any]: The gathered context information.

        Shromažďuje relevantní kontext na základě zadaného popisu úkolu.
        Používá vektorové vyhledávání podobnosti k nalezení nejrelevantnějších částí informací.

        Argumenty:
            task_description (str): Popis úkolu, pro který je kontext potřeba.
            top_k (int): Počet nejvíce podobných chunků k načtení.

        Vrací:
            Dict[str, Any]: Shromážděné kontextové informace.
        """
        self.logger.info(f"Gathering context for task: '{task_description[:50]}...'")

        query_embedding = await self.generate_embedding(task_description)
        if not query_embedding:
            return {"success": False, "error": "Failed to generate query embedding."}

        vector_store = self.storage_manager.get_store(StorageType.POSTGRES_VECTOR)
        if not vector_store:
            return {"success": False, "error": "Vector store not available."}

        similar_chunks = await vector_store.search_similar(vector=query_embedding, top_k=top_k)

        return {
            "success": True,
            "task": task_description,
            "context_chunks": similar_chunks,
            "sources": list(set(chunk.get("metadata", {}).get("source") for chunk in similar_chunks if chunk.get("metadata"))),
        }

    async def manage_vector_db(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manages operations on the vector database, such as adding, updating, or querying vectors.

        Args:
            operation (str): The operation to perform ('add_document', 'delete_by_metadata').
            data (Dict[str, Any]): Data relevant to the operation.

        Returns:
            Dict[str, Any]: Result of the operation.

        Spravuje operace s vektorovou databází, jako je přidávání, aktualizace nebo dotazování vektorů.

        Argumenty:
            operation (str): Operace, která má být provedena ('add_document', 'delete_by_metadata').
            data (Dict[str, Any]): Data relevantní pro operaci.

        Vrací:
            Dict[str, Any]: Výsledek operace.
        """
        self.logger.info(f"Vector DB operation: '{operation}'")

        if operation == 'add_document':
            document_content = data.get("content")
            metadata = data.get("metadata", {})
            if not document_content:
                return {"success": False, "error": "Document content is required for 'add_document' operation."}

            chunks = await self.chunk_document(document_content, metadata)
            added_count = 0
            for chunk in chunks:
                embedding = await self.generate_embedding(chunk["content"])
                if embedding:
                    # Use MCP client to add vector to DB, abstracting direct DB access
                    add_result = await self.mcp_client.handle_request(
                        tool_name="db.vector_add",
                        args={
                            "id": chunk["chunk_id"],
                            "content": chunk["content"],
                            "metadata": chunk["metadata"],
                            "embedding": embedding,
                        }
                    )
                    if add_result.get("success"):
                        added_count += 1
            return {"success": True, "message": f"Processed {len(chunks)} chunks, successfully added {added_count} to DB."}

        else:
            return {"success": False, "error": f"Unsupported vector DB operation: '{operation}'"}

    async def chunk_document(self, document: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks a document into smaller pieces based on token count for efficient storage and retrieval.

        Args:
            document (str): The document to chunk.
            metadata (Dict[str, Any]): Metadata about the document.

        Returns:
            List[Dict[str, Any]]: List of document chunks with their metadata.

        Rozdělí dokument na menší části podle počtu tokenů pro efektivní ukládání a získávání.

        Argumenty:
            document (str): Dokument k rozdělení.
            metadata (Dict[str, Any]): Metadata o dokumentu.

        Vrací:
            List[Dict[str, Any]]: Seznam částí dokumentu s jejich metadaty.
        """
        self.logger.info(f"Chunking document from source: {metadata.get('source', 'N/A')}")
        try:
            tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.logger.warning("cl100k_base not found, falling back to gpt-3.5-turbo tokenizer.")
            tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

        tokens = tokenizer.encode(document)
        chunks = []

        for i in range(0, len(tokens), self.chunk_size):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_content = tokenizer.decode(chunk_tokens)

            chunk_id = str(uuid.uuid4())
            chunks.append({
                "chunk_id": chunk_id,
                "content": chunk_content,
                "metadata": metadata,
                "embedding": None  # To be filled later
            })

        self.logger.info(f"Document split into {len(chunks)} token-based chunks.")
        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the given text using an embedding model via MCP.

        Args:
            text (str): The text to generate an embedding for.

        Returns:
            List[float]: The generated embedding vector, or an empty list on failure.

        Generuje vektorový embedding pro zadaný text pomocí embedding modelu přes MCP.

        Argumenty:
            text (str): Text, pro který se má vygenerovat embedding.

        Vrací:
            List[float]: Vygenerovaný embedding vektor, nebo prázdný seznam při selhání.
        """
        self.logger.debug(f"Requesting embedding for text (length: {len(text)})")
        # Assume an 'embedding.create' tool is available on the MCP server
        response = await self.mcp_client.handle_request(
            tool_name="embedding.create",
            args={"text": text}
        )
        if response and response.get("success"):
            embedding = response.get("result", {}).get("embedding")
            if embedding:
                return embedding
        
        self.logger.warning(f"Failed to generate embedding for text (length: {len(text)}).")
        return []
