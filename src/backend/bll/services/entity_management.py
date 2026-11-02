from ..exceptions import BusinessRuleError
from ..observer import Subject
from .base_service import BaseService


class EntityManagement(BaseService, Subject):
    status_field = "status"

    def __init__(self, repository):
        BaseService.__init__(self, repository)
        Subject.__init__(self)

    async def change_status(self, id, status):
        entity = await self.get_by_id(id)
        if getattr(entity, self.status_field) == status:
            raise BusinessRuleError(
                f"{self.entity_name} with ID {id} already has status {status}"
            )
        if not await self._can_change_status(entity, status):
            raise BusinessRuleError(
                f"{self.entity_name} with ID {id} cannot change status to {status}"
            )
        await self._apply_status(entity, status)
        await self._after_status_change(entity)
        return entity

    async def update(self, id, data):
        entity = await self.get_by_id(id)
        status = getattr(data, self.status_field)
        if status != getattr(
            entity, self.status_field
        ) and not await self._can_change_status(entity, status):
            raise BusinessRuleError(
                f"{self.entity_name} with ID {id} cannot change status to {status}"
            )
        return await super().update(id, data)

    async def _can_change_status(self, entity, status):
        return True

    async def _apply_status(self, entity, status):
        setattr(entity, self.status_field, status)
        await self.repository.update(entity)

    async def _after_status_change(self, entity):
        pass
