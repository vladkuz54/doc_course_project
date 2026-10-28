from abc import abstractmethod

from .base_interface import IBaseService


class IUsersService(IBaseService):

    @abstractmethod
    async def authenticate(self, username, password):
        pass

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass
