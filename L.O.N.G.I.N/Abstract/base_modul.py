# Soubor: base_modul.py
# Verze: 1.0.0

from abc import ABC, abstractmethod

class BaseModul(ABC):
    def __init__(self, id, nazev):
        self.id = id
        self.nazev = nazev
        self.stav = 'neaktivni'

    @abstractmethod
    def inicializace(self):
        pass

    @abstractmethod
    def spusteni(self):
        pass

    @abstractmethod
    def zastaveni(self):
        pass

    @abstractmethod
    def aktualizace(self, data):
        pass

    def logovani(self, zprava, uroven):
        print(f"[{self.id}] [{uroven.upper()}]: {zprava}")

    def get_stav(self):
        return self.stav
