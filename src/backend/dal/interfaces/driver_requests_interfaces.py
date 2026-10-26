from abc import abstractmethod

from ..db_models import DriverRequests
from .base_interfaces import IBaseRepository


class IDriverRequestsRepository(IBaseRepository[DriverRequests]):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def get_pending(self):
        pass
