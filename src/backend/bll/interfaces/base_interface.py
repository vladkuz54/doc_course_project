from abc import abstractmethod

from .read_interface import IReadService


class IBaseService(IReadService):

    @abstractmethod
    async def create(self, data):
        pass

    @abstractmethod
    async def update(self, id, data):
        pass

    @abstractmethod
    async def delete(self, id):
        pass
