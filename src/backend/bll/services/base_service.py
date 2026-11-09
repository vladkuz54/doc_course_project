from abc import abstractmethod

from ..interfaces.base_interface import IBaseService
from .read_service import ReadService


class BaseService(ReadService, IBaseService):
    async def create(self, data):
        await self._validate(data)
        entity = await self._save(data)
        await self._after_add(entity)
        return entity

    async def update(self, id, data):
        obj = await self.get_by_id(id)
        await self._validate(data, id)
        for field, value in self.to_fields(data).items():
            setattr(obj, field, value)
        return await self.repository.update(obj)

    async def delete(self, id):
        await self.get_by_id(id)
        return await self.repository.delete(id)

    @abstractmethod
    async def _validate(self, data, id=None):
        pass

    async def _save(self, data):
        return await self.repository.create(
            self.repository.model(**self.to_fields(data))
        )

    async def _after_add(self, entity):
        pass

    def to_fields(self, data):
        return data.model_dump()
