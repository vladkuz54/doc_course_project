from abc import abstractmethod

from .base_interface import IBaseService


class IEntityManagement(IBaseService):

    @abstractmethod
    async def change_status(self, id, status):
        pass
