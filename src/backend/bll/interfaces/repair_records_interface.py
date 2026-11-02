from abc import abstractmethod

from .base_interface import IBaseService


class IRepairRecordsService(IBaseService):

    @abstractmethod
    async def record_repair_cost(self, id, cost):
        pass

    @abstractmethod
    async def get_planned(self):
        pass
