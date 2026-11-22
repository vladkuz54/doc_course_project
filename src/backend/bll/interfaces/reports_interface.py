from abc import ABC, abstractmethod


class IReportService(ABC):

    @abstractmethod
    def set_strategy(self, strategy):
        pass

    @abstractmethod
    async def generate(self, period_from, period_to, vehicle=None):
        pass
