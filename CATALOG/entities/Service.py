from abc import ABC, abstractmethod


class Service(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        pass
