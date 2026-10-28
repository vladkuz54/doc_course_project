from ..exceptions import EntityNotFoundError
from ..interfaces.base_interface import IBaseService


class BaseService(IBaseService):
    entity_name = "Entity"

    def __init__(self, repository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, id):
        obj = await self.repository.get_by_id(id)
        if not obj:
            raise EntityNotFoundError(f"{self.entity_name} with ID {id} not found")
        return obj

    async def create(self, data):
        await self._validate(data)
        return await self.repository.create(
            self.repository.model(**self.to_fields(data))
        )

    async def update(self, id, data):
        obj = await self.get_by_id(id)
        await self._validate(data, id)
        for field, value in self.to_fields(data).items():
            setattr(obj, field, value)
        return await self.repository.update(obj)

    async def delete(self, id):
        await self.get_by_id(id)
        return await self.repository.delete(id)

    async def _validate(self, data, id=None):
        # services override this with their own checks before create/update
        pass

    def to_fields(self, data):
        return data.model_dump()
