from ..exceptions import BusinessRuleError
from ..interfaces.entity_management_interface import IEntityManagement
from .base_service import BaseService


class EntityManagement(BaseService, IEntityManagement):
    status_field = "status"
    status_labels = {}
    status_blocked_message = "Цей статус зараз не можна встановити."

    async def change_status(self, id, status):
        entity = await self.get_by_id(id)
        if getattr(entity, self.status_field) == status:
            label = self.status_labels.get(status, status)
            raise BusinessRuleError(
                f"Статус уже «{label}», змінювати нічого не потрібно."
            )
        if not await self._can_change_status(entity, status):
            raise BusinessRuleError(self.status_blocked_message)
        await self._apply_status(entity, status)
        await self._after_status_change(entity)
        return entity

    async def update(self, id, data):
        entity = await self.get_by_id(id)
        status = getattr(data, self.status_field)
        if status != getattr(
            entity, self.status_field
        ) and not await self._can_change_status(entity, status):
            raise BusinessRuleError(self.status_blocked_message)
        return await super().update(id, data)

    async def _can_change_status(self, entity, status):
        return True

    async def _apply_status(self, entity, status):
        setattr(entity, self.status_field, status)
        await self.repository.update(entity)

    async def _after_status_change(self, entity):
        pass
