from abc import abstractmethod

from ..db_models import Vehicles
from .base_interfaces import IBaseRepository


class IVehiclesRepository(IBaseRepository[Vehicles]):

    @abstractmethod
    async def get_by_vin(self, vin):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass
