from abc import abstractmethod

from ..db_models import Routes
from .base_interfaces import IBaseRepository


class IRoutesRepository(IBaseRepository[Routes]):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def get_by_vehicle(self, vehicle_id):
        pass

    @abstractmethod
    async def get_between_dates(self, start, end, vehicle_id=None):
        pass
