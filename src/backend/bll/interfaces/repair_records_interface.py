from abc import abstractmethod

from .accounting_interface import IAccountingService


class IRepairRecordsService(IAccountingService):

    @abstractmethod
    async def record_repair_cost(self, id, cost):
        pass

    @abstractmethod
    async def get_planned(self):
        pass
