from abc import abstractmethod

from .base_interface import IBaseService


class IDriversService(IBaseService):

    @abstractmethod
    async def get_by_user_id(self, user_id):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass
