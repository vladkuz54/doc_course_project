from abc import abstractmethod

from .read_interface import IReadService


class IRouteStopsService(IReadService):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass
