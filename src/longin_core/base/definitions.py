from abc import ABC, abstractmethod
from enum import Enum
import logging
from typing import List, Optional, Dict, Any


class ModuleStatus(Enum):
    """
    Represents the operational status of a Longin module.
    Reprezentuje provozní stav modulu Longin.
    """
    IDLE = ("Idle", "Nečinný")
    INITIALIZING = ("Initializing", "Inicializace")
    RUNNING = ("Running", "Běží")
    THINKING = ("Thinking", "Přemýšlí")
    PROCESSING = ("Processing", "Zpracovává")
    WAITING_FOR_USER = ("Waiting for User", "Čeká na uživatele")
    WAITING_FOR_RESOURCE = ("Waiting for Resource", "Čeká na zdroj")
    ERROR = ("Error", "Chyba")
    STOPPING = ("Stopping", "Zastavuje se")
    STOPPED = ("Stopped", "Zastaveno")
    DISABLED = ("Disabled", "Deaktivováno")

    def __init__(self, en_name: str, cz_name: str):
        self.en_name = en_name
        self.cz_name = cz_name

    def __str__(self):
        return self.en_name

    def to_dict(self):
        return {"en": self.en_name, "cz": self.cz_name}


class LonginModule(ABC):
    """
    Abstract base class for all Longin modules.
    Provides a common interface for module initialization, status, UI rendering,
    user interaction, message processing, and cleanup.

    Abstraktní základní třída pro všechny moduly Longin.
    Poskytuje společné rozhraní pro inicializaci modulu, stav, vykreslování UI,
    uživatelskou interakci, zpracování zpráv a úklid.
    """
    def __init__(self, module_id: str, config: dict, logger: logging.Logger):
        """
        Initializes a Longin module.

        Args:
            module_id (str): Unique identifier for the module.
            config (dict): Configuration dictionary for the module.
            logger (logging.Logger): Logger instance for the module.

        Inicializuje modul Longin.

        Argumenty:
            module_id (str): Unikátní identifikátor modulu.
            config (dict): Konfigurační slovník pro modul.
            logger (logging.Logger): Instance loggeru pro modul.
        """
        self.module_id = module_id
        self.config = config
        self.logger = logger
        self._status = ModuleStatus.IDLE

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initializes the module's resources and state.

        Returns:
            bool: True if initialization was successful, False otherwise.

        Inicializuje zdroje a stav modulu.

        Vrací:
            bool: True, pokud byla inicializace úspěšná, jinak False.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Retrieves the current status of the module for UI display.

        Returns:
            dict: A dictionary containing module status information, including:
                  - 'module_id' (str): Unique identifier of the module.
                  - 'status_enum' (ModuleStatus): Current operational status.
                  - 'color' (str): Hex color code or predefined color name for UI.
                  - 'sub_modules' (List[str]): List of IDs of sub-modules.
                  - 'connectors' (List[str]): List of IDs of connected connectors.
                  - 'hardware_status' (Dict[str, Any]): Current hardware resource usage.
                  - 'current_activity' (str): Description of the module's current activity.

        Získá aktuální stav modulu pro zobrazení v UI.

        Vrací:
            dict: Slovník obsahující informace o stavu modulu, včetně:
                  - 'module_id' (str): Unikátní identifikátor modulu.
                  - 'status_enum' (ModuleStatus): Aktuální provozní stav.
                  - 'color' (str): Hex kód barvy nebo předdefinovaný název barvy pro UI.
                  - 'sub_modules' (List[str]): Seznam ID podmodulů.
                  - 'connectors' (List[str]): Seznam ID připojených konektorů.
                  - 'hardware_status' (Dict[str, Any]): Aktuální využití hardwarových zdrojů.
                  - 'current_activity' (str): Popis aktuální aktivity modulu.
        """
        pass

    @abstractmethod
    async def render_ui_card(self) -> Dict[str, Any]:
        """
        Returns the UI specification for the module's card.

        Returns:
            dict: A dictionary representing the UI structure and data for the module's card.

        Vrací specifikaci UI pro kartu modulu.

        Vrací:
            dict: Slovník reprezentující strukturu UI a data pro kartu modulu.
        """
        pass

    @abstractmethod
    async def handle_user_action(self, action_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a user action received from the UI.

        Args:
            action_id (str): Identifier of the action to be performed.
            data (dict): Data associated with the user action.

        Returns:
            dict: A dictionary containing the result of the action or status update.

        Zpracuje uživatelskou akci přijatou z UI.

        Argumenty:
            action_id (str): Identifikátor akce, která má být provedena.
            data (dict): Data spojená s uživatelskou akcí.

        Vrací:
            dict: Slovník obsahující výsledek akce nebo aktualizaci stavu.
        """
        pass

    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processes an incoming message from the EventBus or a connector.

        Args:
            message (dict): The message to be processed.

        Returns:
            Optional[dict]: An optional dictionary containing a response message, or None if no response is needed.

        Zpracuje příchozí zprávu z EventBusu nebo konektoru.

        Argumenty:
            message (dict): Zpráva, která má být zpracována.

        Vrací:
            Optional[dict]: Volitelný slovník obsahující odpovědní zprávu, nebo None, pokud není odpověď potřeba.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleans up module resources before shutdown.

        Returns:
            bool: True if cleanup was successful, False otherwise.

        Uvolní zdroje modulu před vypnutím.

        Vrací:
            bool: True, pokud bylo vyčištění úspěšné, jinak False.
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Returns a list of capabilities provided by the module.

        Returns:
            List[str]: A list of strings describing the module's capabilities (e.g., ["chat_processing", "file_analysis"]).

        Vrací seznam schopností poskytovaných modulem.

        Vrací:
            List[str]: Seznam řetězců popisujících schopnosti modulu (např. ["chat_processing", "file_analysis"]).
        """
        pass


class LonginConnector(ABC):
    """
    Abstract base class for all Longin connectors.
    Connectors facilitate communication between Longin modules.

    Abstraktní základní třída pro všechny konektory Longin.
    Konektory usnadňují komunikaci mezi moduly Longin.
    """
    def __init__(self, connector_id: str, source_module: LonginModule, target_module_id: str, config: dict, logger: logging.Logger):
        """
        Initializes a Longin connector.

        Args:
            connector_id (str): Unique identifier for the connector.
            source_module (LonginModule): The module initiating the connection.
            target_module_id (str): The ID of the target module for the connection.
            config (dict): Configuration dictionary for the connector.
            logger (logging.Logger): Logger instance for the connector.

        Inicializuje konektor Longin.

        Argumenty:
            connector_id (str): Unikátní identifikátor konektoru.
            source_module (LonginModule): Modul iniciující připojení.
            target_module_id (str): ID cílového modulu pro připojení.
            config (dict): Konfigurační slovník pro konektor.
            logger (logging.Logger): Instance loggeru pro konektor.
        """
        self.connector_id = connector_id
        self.source_module = source_module
        self.target_module_id = target_module_id
        self.config = config
        self.logger = logger

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establishes the connection.

        Returns:
            bool: True if connection was successful, False otherwise.

        Naváže spojení.

        Vrací:
            bool: True, pokud bylo připojení úspěšné, jinak False.
        """
        pass

    @abstractmethod
    async def send_message(self, message: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Sends a message through the connector.

        Args:
            message (dict): The message to be sent.
            timeout (int): Timeout in seconds for sending the message.

        Returns:
            Optional[dict]: An optional dictionary containing a response message, or None.

        Odešle zprávu přes konektor.

        Argumenty:
            message (dict): Zpráva, která má být odeslána.
            timeout (int): Časový limit v sekundách pro odeslání zprávy.

        Vrací:
            Optional[dict]: Volitelný slovník obsahující odpovědní zprávu, nebo None.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Closes the connection and cleans up resources.

        Returns:
            bool: True if disconnection was successful, False otherwise.

        Uzavře spojení a uvolní zdroje.

        Vrací:
            bool: True, pokud bylo odpojení úspěšné, jinak False.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Retrieves the current status of the connector.

        Returns:
            dict: A dictionary containing connector status information.

        Získá aktuální stav konektoru.

        Vrací:
            dict: Slovník obsahující informace o stavu konektoru.
        """
        pass


class LonginAdapter(ABC):
    """
    Abstract base class for all Longin adapters.
    Adapters provide a unified interface for interacting with external AI providers or systems.

    Abstraktní základní třída pro všechny adaptéry Longin.
    Adaptéry poskytují jednotné rozhraní pro interakci s externími poskytovateli AI nebo systémy.
    """
    def __init__(self, adapter_id: str, provider_type: str, config: dict, logger: logging.Logger):
        """
        Initializes a Longin adapter.

        Args:
            adapter_id (str): Unique identifier for the adapter.
            provider_type (str): Type of the external provider (e.g., "openai", "ollama", "lm_studio").
            config (dict): Configuration dictionary for the adapter.
            logger (logging.Logger): Logger instance for the adapter.

        Inicializuje adaptér Longin.

        Argumenty:
            adapter_id (str): Unikátní identifikátor adaptéru.
            provider_type (str): Typ externího poskytovatele (např. "openai", "ollama", "lm_studio").
            config (dict): Konfigurační slovník pro adaptér.
            logger (logging.Logger): Instance loggeru pro adaptér.
        """
        self.adapter_id = adapter_id
        self.provider_type = provider_type
        self.config = config
        self.logger = logger

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establishes connection to the external provider.

        Returns:
            bool: True if connection was successful, False otherwise.

        Naváže spojení s externím poskytovatelem.

        Vrací:
            bool: True, pokud bylo připojení úspěšné, jinak False.
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Lists available models from the external provider.

        Returns:
            List[dict]: A list of dictionaries, each representing an available model.

        Vypíše dostupné modely od externího poskytovatele.

        Vrací:
            List[dict]: Seznam slovníků, každý reprezentující dostupný model.
        """
        pass

    @abstractmethod
    async def generate_completion(self, model_id: str, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a text completion using the specified model.

        Args:
            model_id (str): The ID of the model to use for completion.
            prompt (str): The input prompt for text generation.
            params (dict): Additional parameters for the generation (e.g., temperature, max_tokens).

        Returns:
            dict: A dictionary containing the generated completion and other metadata.

        Generuje textové dokončení pomocí zadaného modelu.

        Argumenty:
            model_id (str): ID modelu, který se má použít pro dokončení.
            prompt (str): Vstupní prompt pro generování textu.
            params (dict): Další parametry pro generování (např. teplota, max_tokens).

        Vrací:
            dict: Slovník obsahující vygenerované dokončení a další metadata.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Retrieves the current status of the adapter and its connection.

        Returns:
            dict: A dictionary containing adapter status information.

        Získá aktuální stav adaptéru a jeho připojení.

        Vrací:
            dict: Slovník obsahující informace o stavu adaptéru.
        """
        pass
