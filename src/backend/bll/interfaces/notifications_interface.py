from abc import abstractmethod

from .base_interface import IBaseService


class INotificationsService(IBaseService):

    @abstractmethod
    async def get_for_driver(self, driver_id):
        pass
