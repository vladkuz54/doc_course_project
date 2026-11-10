from abc import ABC, abstractmethod


class IReadService(ABC):

    @abstractmethod
    async def get_all(self):
        pass

    @abstractmethod
    async def get_by_id(self, id):
        pass
