from abc import ABC, abstractmethod


class IRouteStopsService(ABC):

    @abstractmethod
    async def get_all(self):
        pass

    @abstractmethod
    async def get_by_id(self, id):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass
