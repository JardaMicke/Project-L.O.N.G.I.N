# Soubor: interfaces.py
# Verze: 1.0.0

from abc import ABC, abstractmethod
from base_modul import BaseModul

class IPart(BaseModul):
    @abstractmethod
    def ziskej_data(self):
        pass

    @abstractmethod
    def nastav_data(self, data):
        pass

    @abstractmethod
    def validace(self):
        pass


class IUnit(BaseModul):
    @abstractmethod
    def pridej_part(self, part: IPart):
        pass

    @abstractmethod
    def odeber_part(self, part_id: str):
        pass

    @abstractmethod
    def ziskej_part(self, part_id: str) -> IPart:
        pass

    @abstractmethod
    def zpracuj_data(self):
        pass


class IComponent(BaseModul):
    @abstractmethod
    def pridej_unit(self, unit: IUnit):
        pass

    @abstractmethod
    def odeber_unit(self, unit_id: str):
        pass

    @abstractmethod
    def ziskej_unit(self, unit_id: str) -> IUnit:
        pass

    @abstractmethod
    def proved_operaci(self, operace: str, data: any):
        pass


class IAugment(BaseModul):
    @abstractmethod
    def pridej_component(self, component: IComponent):
        pass

    @abstractmethod
    def odeber_component(self, component_id: str):
        pass

    @abstractmethod
    def ziskej_component(self, component_id: str) -> IComponent:
        pass

    @abstractmethod
    def spust_augmentaci(self):
        pass

    @abstractmethod
    def zastav_augmentaci(self):
        pass
