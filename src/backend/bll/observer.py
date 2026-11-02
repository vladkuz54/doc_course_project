from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DomainEvent:
    type: str
    related_entity: str
    related_id: int
    text: str
    recipient_id: int | None = None


class Observer(ABC):

    @abstractmethod
    async def on_event(self, event: DomainEvent):
        pass


class Subject(ABC):
    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    async def _notify(self, event: DomainEvent):
        for observer in self._observers:
            await observer.on_event(event)
