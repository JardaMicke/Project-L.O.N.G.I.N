# Soubor: base_connector.py
# Verze: 1.0.0

from abc import ABC, abstractmethod
from datetime import datetime

class BaseConnector(ABC):
    def __init__(self, source_module, target_module):
        self.source_module = source_module
        self.target_module = target_module
        self.stats = {
            'transfer_count': 0,
            'total_data_size': 0,
            'last_activity': None
        }
        self.version = "1.0.0"
        self.file_name = "base_connector.py"

    @abstractmethod
    def verify_data(self, data):
        pass

    @abstractmethod
    def transform_data(self, data):
        pass

    def transfer_data(self, data):
        if self.verify_data(data):
            transformed_data = self.transform_data(data)
            self.send_data(transformed_data)
            self.update_stats(data)
        else:
            raise ValueError('Invalid data for transfer')

    def send_data(self, data):
        self.target_module.update(data)

    def update_stats(self, data):
        self.stats['transfer_count'] += 1
        self.stats['total_data_size'] += len(str(data))
        self.stats['last_activity'] = datetime.now()

    def get_stats(self):
        return self.stats

    def log(self, message):
        print(f"[Connector {self.source_module.id} -> {self.target_module.id}] v{self.version} ({self.file_name}): {message}")
