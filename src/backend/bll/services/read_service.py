from ..exceptions import EntityNotFoundError
from ..interfaces.read_interface import IReadService


class ReadService(IReadService):
    entity_name = "Запис"

    def __init__(self, repository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, id):
        obj = await self.repository.get_by_id(id)
        if not obj:
            raise EntityNotFoundError(
                f"{self.entity_name} не знайдено. Можливо, запис уже видалено — "
                "оновіть сторінку."
            )
        return obj
