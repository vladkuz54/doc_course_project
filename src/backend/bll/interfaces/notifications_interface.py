from abc import abstractmethod

from .base_interface import IBaseService


class INotificationsService(IBaseService):

    @abstractmethod
    async def get_by_driver(self, driver_id):
        pass

    @abstractmethod
    async def get_for_admins(self):
        pass

    @abstractmethod
    async def mark_as_read(self, id):
        pass

    @abstractmethod
    async def on_event(self, event):
        pass
