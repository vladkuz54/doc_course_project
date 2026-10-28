from abc import abstractmethod
from typing import TypeVar

from .base_interfaces import IBaseRepository

T = TypeVar("T")


class IAccountingRepository(IBaseRepository[T]):

    @abstractmethod
    async def get_by_vehicle(self, vehicle_id):
        pass

    @abstractmethod
    async def get_between_dates(self, start, end, vehicle_id=None):
        pass
