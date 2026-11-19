from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

NotificationType = Literal[
    "LICENSE_UPDATE_REQUEST",
    "MEDICAL_CHECK_REQUEST",
    "MAINTENANCE_DUE",
    "INSURANCE_EXPIRING",
    "LICENSE_EXPIRING",
    "MEDICAL_CHECK_DUE",
    "ROUTE_ASSIGNED",
    "ROUTE_UPDATED",
    "ROUTE_UNASSIGNED",
    "ROUTE_CANCELLED",
    "REPAIR_COST_MISSING",
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


class Subscriber(ABC):

    @abstractmethod
    async def on_event(self, event: DomainEvent):
        pass


class Subject(ABC):
    def __init__(self):
        self._subscribers = []

    def attach(self, subscriber: Subscriber):
        self._subscribers.append(subscriber)

    def detach(self, subscriber: Subscriber):
        self._subscribers.remove(subscriber)

    async def _notify(self, event: DomainEvent):
        for subscriber in self._subscribers:
            await subscriber.on_event(event)
