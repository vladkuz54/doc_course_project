from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

NotificationType = Literal[
    "LICENSE_UPDATE_REQUEST",
    "MEDICAL_CHECK_REQUEST",
    "MAINTENANCE_SCHEDULED",
    "MAINTENANCE_DUE",
    "INSURANCE_EXPIRING",
    "LICENSE_EXPIRING",
    "MEDICAL_CHECK_DUE",
    "ROUTE_ASSIGNED",
    "REQUEST_APPROVED",
    "REQUEST_REJECTED",
]


@dataclass(frozen=True)
class DomainEvent:
    type: NotificationType
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
