from abc import abstractmethod

from .base_interface import IBaseService


class IAccountingService(IBaseService):

    @abstractmethod
    async def list(self, period_from, period_to, vehicle=None):
        pass

    @abstractmethod
    async def get_by_vehicle(self, vehicle_id):
        pass
