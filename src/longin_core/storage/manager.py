from abc import ABC, abstractmethod
from enum import Enum
import logging
from typing import Dict, Any, Optional, List
import json
import asyncio
import os

# Define StorageType Enum
class StorageType(Enum):
    """
    Represents the types of storage available in the Longin AI Systems.
    Reprezentuje typy úložišť dostupné v systémech Longin AI.
    """
    JSON = "json"
    REDIS = "redis"
    POSTGRES = "postgres"
    POSTGRES_VECTOR = "postgres_vector"
    CACHE = "redis" # Alias for REDIS

    def __str__(self):
        return self.value

# Abstract BaseStore Class
class BaseStore(ABC):
    """
    Abstract base class for all storage implementations in Longin AI Systems.
    Abstraktní základní třída pro všechny implementace úložišť v systémech Longin AI.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        """
        Initializes the base store with configuration and a logger.
        Inicializuje základní úložiště s konfigurací a loggerem.
        """
        self.config = config
        self.logger = logger

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establishes a connection to the storage.
        Naváže spojení s úložištěm.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Closes the connection to the storage and cleans up resources.
        Uzavře spojení s úložištěm a uvolní zdroje.
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a value from the storage by its key.
        Získá hodnotu z úložiště podle jejího klíče.
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Sets a value in the storage with an optional time-to-live (TTL).
        Nastaví hodnotu v úložišti s volitelnou dobou platnosti (TTL).
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Deletes a value from the storage by its key.
        Smaže hodnotu z úložiště podle jejího klíče.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Performs a health check on the storage connection.
        Provede kontrolu stavu připojení k úložišti.
        """
        pass

# Concrete Store Implementations (Placeholders)
class JsonStore(BaseStore):
    """
    JSON file-based storage implementation.
    Implementace úložiště založeného na JSON souborech.
    """
    def __init__(self, config: dict, logger: logging.Logger, base_path: str):
        super().__init__(config, logger)
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.logger.info(f"JsonStore initialized with base path: {self.base_path}")

    async def connect(self) -> bool:
        self.logger.info("JsonStore connected (file system access).")
        return True

    async def disconnect(self) -> bool:
        self.logger.info("JsonStore disconnected (no active connection to close).")
        return True

    async def get(self, key: str) -> Optional[Any]:
        file_path = os.path.join(self.base_path, f"{key}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        self.logger.warning(f"Key '{key}' not found in JsonStore.")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        file_path = os.path.join(self.base_path, f"{key}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Key '{key}' set in JsonStore.")
        return True

    async def delete(self, key: str) -> bool:
        file_path = os.path.join(self.base_path, f"{key}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            self.logger.info(f"Key '{key}' deleted from JsonStore.")
            return True
        self.logger.warning(f"Key '{key}' not found for deletion in JsonStore.")
        return False

    async def health_check(self) -> bool:
        # Check if base_path is writable
        try:
            test_file = os.path.join(self.base_path, "health_check_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception as e:
            self.logger.error(f"JsonStore health check failed: {e}")
            return False

class RedisStore(BaseStore):
    """
    Redis-based storage implementation.
    Implementace úložiště založeného na Redis.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.logger.info("RedisStore initialized.")
        # Placeholder for actual Redis client initialization
        self.client = None

    async def connect(self) -> bool:
        self.logger.info("Connecting to Redis (placeholder).")
        # self.client = await redis.asyncio.from_url(self.config.get("url", "redis://localhost"))
        return True

    async def disconnect(self) -> bool:
        self.logger.info("Disconnecting from Redis (placeholder).")
        # if self.client: await self.client.close()
        return True

    async def get(self, key: str) -> Optional[Any]:
        self.logger.info(f"Getting key '{key}' from Redis (placeholder).")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self.logger.info(f"Setting key '{key}' in Redis (placeholder). TTL: {ttl}.")
        return True

    async def delete(self, key: str) -> bool:
        self.logger.info(f"Deleting key '{key}' from Redis (placeholder).")
        return True

    async def health_check(self) -> bool:
        self.logger.info("RedisStore health check (placeholder).")
        return True

class PostgresStore(BaseStore):
    """
    PostgreSQL-based storage implementation.
    Implementace úložiště založeného na PostgreSQL.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.logger.info("PostgresStore initialized.")
        # Placeholder for actual PostgreSQL client initialization
        self.pool = None

    async def connect(self) -> bool:
        self.logger.info("Connecting to PostgreSQL (placeholder).")
        # self.pool = await asyncpg.create_pool(**self.config)
        return True

    async def disconnect(self) -> bool:
        self.logger.info("Disconnecting from PostgreSQL (placeholder).")
        # if self.pool: await self.pool.close()
        return True

    async def get(self, key: str) -> Optional[Any]:
        self.logger.info(f"Getting key '{key}' from Postgres (placeholder).")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self.logger.info(f"Setting key '{key}' in Postgres (placeholder).")
        return True

    async def delete(self, key: str) -> bool:
        self.logger.info(f"Deleting key '{key}' from Postgres (placeholder).")
        return True

    async def health_check(self) -> bool:
        self.logger.info("PostgresStore health check (placeholder).")
        return True

class PostgresVectorStore(PostgresStore):
    """
    PostgreSQL with pgvector extension for vector embeddings storage.
    PostgreSQL s rozšířením pgvector pro ukládání vektorových embeddingů.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.logger.info("PostgresVectorStore initialized.")

    async def search_similar(self, vector: List[float], top_k: int) -> List[dict]:
        """
        Searches for similar vectors in the database.
        Vyhledává podobné vektory v databázi.
        """
        self.logger.info(f"Searching for {top_k} similar vectors (placeholder).")
        return []

# StorageManager Class
class StorageManager:
    """
    Manages various storage solutions for the Longin AI Systems.
    Spravuje různá úložná řešení pro systémy Longin AI.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        """
        Initializes the StorageManager and configures individual storage instances.
        Inicializuje StorageManager a konfiguruje jednotlivé instance úložišť.
        """
        self.config = config
        self.logger = logger
        self.stores: Dict[StorageType, BaseStore] = {}
        self._initialize_storage_instances()
        self.logger.info("StorageManager initialized.")

    def _initialize_storage_instances(self):
        """
        Initializes concrete storage instances based on configuration.
        Inicializuje konkrétní instance úložišť na základě konfigurace.
        """
        if self.config.get("json_store"):
            self.stores[StorageType.JSON] = JsonStore(
                self.config["json_store"], self.logger, self.config["json_store"]["base_path"]
            )
        if self.config.get("redis_store"):
            self.stores[StorageType.REDIS] = RedisStore(self.config["redis_store"], self.logger)
            self.stores[StorageType.CACHE] = self.stores[StorageType.REDIS] # CACHE is an alias for REDIS
        if self.config.get("postgres_store"):
            self.stores[StorageType.POSTGRES] = PostgresStore(self.config["postgres_store"], self.logger)
        if self.config.get("postgres_vector_store"):
            self.stores[StorageType.POSTGRES_VECTOR] = PostgresVectorStore(self.config["postgres_vector_store"], self.logger)

    async def initialize_stores(self):
        """
        Connects to all initialized storage instances.
        Připojí se ke všem inicializovaným instancím úložišť.
        """
        self.logger.info("Initializing all configured stores...")
        for store_type, store_instance in self.stores.items():
            try:
                success = await store_instance.connect()
                if success:
                    self.logger.info(f"Store '{store_type.name}' connected successfully.")
                else:
                    self.logger.warning(f"Store '{store_type.name}' failed to connect.")
            except Exception as e:
                self.logger.error(f"Error connecting to store '{store_type.name}': {e}")

    def get_store(self, store_type: StorageType) -> Optional[BaseStore]:
        """
        Returns an instance of the requested storage type.
        Vrátí instanci požadovaného typu úložiště.
        """
        return self.stores.get(store_type)

    async def select_store(self, data_type: str, access_pattern: str) -> Optional[BaseStore]:
        """
        Dynamically selects the most suitable store based on data type and access pattern.
        Currently returns a default store or logs that dynamic selection is not implemented.
        Dynamicky vybere nejvhodnější úložiště na základě typu dat a vzoru přístupu.
        V současné době vrací výchozí úložiště nebo loguje, že dynamický výběr není implementován.
        """
        self.logger.warning(
            f"Dynamic store selection not fully implemented. Data Type: {data_type}, Access Pattern: {access_pattern}"
        )
        # Placeholder logic:
        if data_type == "vector_embedding":
            return self.get_store(StorageType.POSTGRES_VECTOR)
        elif data_type == "cache" or access_pattern == "frequent_read":
            return self.get_store(StorageType.CACHE)
        elif data_type == "log" or access_pattern == "append_only":
            return self.get_store(StorageType.JSON)
        else:
            return self.get_store(StorageType.POSTGRES) # Default to Postgres for general data

    async def shutdown_stores(self):
        """
        Disconnects from all initialized storage instances.
        Odpojí se od všech inicializovaných instancí úložišť.
        """
        self.logger.info("Shutting down all configured stores...")
        for store_type, store_instance in self.stores.items():
            try:
                success = await store_instance.disconnect()
                if success:
                    self.logger.info(f"Store '{store_type.name}' disconnected successfully.")
                else:
                    self.logger.warning(f"Store '{store_type.name}' failed to disconnect gracefully.")
            except Exception as e:
                self.logger.error(f"Error disconnecting from store '{store_type.name}': {e}")
