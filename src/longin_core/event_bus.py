import logging
import asyncio
from typing import Dict, List, Callable, Optional
from collections import defaultdict


class LONGINEventBus:
    """
    A central asynchronous event bus for the Longin AI Systems.
    It facilitates communication between different modules by allowing them to
    publish and subscribe to specific topics.

    Centrální asynchronní sběrnice událostí pro systémy Longin AI.
    Usnadňuje komunikaci mezi různými moduly tím, že jim umožňuje
    publikovat a odebírat konkrétní témata.
    """

    def __init__(self, logger: logging.Logger, config: dict):
        """
        Initializes the LONGINEventBus.

        Args:
            logger (logging.Logger): The logger instance for the event bus.
            config (dict): Configuration dictionary for the event bus.

        Inicializuje sběrnici událostí LONGINEventBus.

        Argumenty:
            logger (logging.Logger): Instance loggeru pro sběrnici událostí.
            config (dict): Konfigurační slovník pro sběrnici událostí.
        """
        self.logger = logger
        self.config = config
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self.logger.info("LONGINEventBus initialized.")

    async def publish(self, topic: str, message: dict, source_module_id: str):
        """
        Publishes a message to a specific topic. The message will be added to the
        internal queue for asynchronous processing.

        Args:
            topic (str): The topic to which the message is published.
            message (dict): The content of the message.
            source_module_id (str): The ID of the module publishing the message.

        Publikuje zprávu na konkrétní téma. Zpráva bude přidána do
        interní fronty pro asynchronní zpracování.

        Argumenty:
            topic (str): Téma, na které je zpráva publikována.
            message (dict): Obsah zprávy.
            source_module_id (str): ID modulu, který zprávu publikuje.
        """
        await self.message_queue.put({"topic": topic, "message": message, "source_id": source_module_id})
        self.logger.debug(f"Message published to topic '{topic}' from '{source_module_id}'.")

    async def subscribe(self, topic: str, callback: Callable, module_id: str):
        """
        Registers a callback function to receive messages from a specific topic.

        Args:
            topic (str): The topic to subscribe to.
            callback (Callable): The asynchronous function to call when a message is published to the topic.
            module_id (str): The ID of the module subscribing.

        Registruje callback funkci pro příjem zpráv z konkrétního tématu.

        Argumenty:
            topic (str): Téma, k jehož odběru se modul přihlašuje.
            callback (Callable): Asynchronní funkce, která se zavolá, když je na téma publikována zpráva.
            module_id (str): ID modulu, který se přihlašuje k odběru.
        """
        if callback not in self.subscribers[topic]:
            self.subscribers[topic].append(callback)
            self.logger.info(f"Module '{module_id}' subscribed to topic '{topic}'.")
        else:
            self.logger.warning(f"Module '{module_id}' already subscribed to topic '{topic}'.")

    async def unsubscribe(self, topic: str, callback: Callable, module_id: str):
        """
        Unregisters a callback function from a specific topic.

        Args:
            topic (str): The topic to unsubscribe from.
            callback (Callable): The callback function to remove.
            module_id (str): The ID of the module unsubscribing.

        Odregistruje callback funkci z konkrétního tématu.

        Argumenty:
            topic (str): Téma, od jehož odběru se modul odhlašuje.
            callback (Callable): Callback funkce, která má být odstraněna.
            module_id (str): ID modulu, který se odhlašuje.
        """
        if callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            self.logger.info(f"Module '{module_id}' unsubscribed from topic '{topic}'.")
            if not self.subscribers[topic]:
                del self.subscribers[topic]
        else:
            self.logger.warning(f"Module '{module_id}' was not subscribed to topic '{topic}' with this callback.")

    async def _process_message_queue(self):
        """
        Internal method to continuously process messages from the queue and
        dispatch them to registered subscribers.

        Interní metoda pro nepřetržité zpracování zpráv z fronty a
        jejich odesílání registrovaným odběratelům.
        """
        self.logger.info("EventBus message processing started.")
        while True:
            try:
                message_data = await self.message_queue.get()
                topic = message_data["topic"]
                message = message_data["message"]
                source_id = message_data["source_id"]

                self.logger.debug(f"Processing message for topic '{topic}' from '{source_id}'.")

                if topic in self.subscribers:
                    for callback in list(self.subscribers[topic]):  # Iterate over a copy to allow modification during loop
                        try:
                            await callback(message)
                        except Exception as e:
                            self.logger.error(f"Error in subscriber callback for topic '{topic}': {e}", exc_info=True)
                self.message_queue.task_done()
            except asyncio.CancelledError:
                self.logger.info("EventBus message processing task cancelled.")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in EventBus message processing loop: {e}", exc_info=True)

    async def start(self):
        """
        Starts the EventBus by initiating the message processing task.

        Spustí sběrnici událostí zahájením úlohy zpracování zpráv.
        """
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_message_queue())
            self.logger.info("LONGINEventBus started.")
        else:
            self.logger.warning("LONGINEventBus is already running.")

    async def stop(self):
        """
        Gracefully stops the EventBus by cancelling the message processing task.
        It waits for the queue to be empty before stopping.

        Elegantně zastaví sběrnici událostí zrušením úlohy zpracování zpráv.
        Před zastavením počká, dokud nebude fronta prázdná.
        """
        if self._processing_task and not self._processing_task.done():
            self.logger.info("Stopping LONGINEventBus. Waiting for pending messages...")
            try:
                await asyncio.wait_for(self.message_queue.join(), timeout=5) # Wait for messages to be processed
            except asyncio.TimeoutError:
                self.logger.warning("EventBus queue not empty after timeout. Some messages might be unprocessed.")
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass # Task was cancelled as expected
            self._processing_task = None
            self.logger.info("LONGINEventBus stopped.")
        else:
            self.logger.warning("LONGINEventBus is not running or already stopped.")

    def determine_communication_type(self, source_level: int, target_level: int) -> str:
        """
        Determines the communication type based on the hierarchical levels of source and target modules.

        Args:
            source_level (int): The hierarchical level of the source module.
            target_level (int): The hierarchical level of the target module.

        Returns:
            str: The determined communication type ("eventbus", "direct_call", or "api_queue").

        Určuje typ komunikace na základě hierarchických úrovní zdrojového a cílového modulu.

        Argumenty:
            source_level (int): Hierarchická úroveň zdrojového modulu.
            target_level (int): Hierarchická úroveň cílového modulu.

        Vrací:
            str: Určený typ komunikace ("eventbus", "direct_call" nebo "api_queue").
        """
        if source_level == target_level:
            return "eventbus"  # same-level -> eventbus
        elif abs(source_level - target_level) == 1:
            return "direct_call"  # neighbour -> direct_call
        else:
            return "api_queue"  # distant -> api_queue
