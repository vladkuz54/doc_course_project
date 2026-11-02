from abc import abstractmethod
from decimal import Decimal

from ..exceptions import EntityNotFoundError
from ..interfaces.accounting_interface import IAccountingService
from .base_service import BaseService


class AccountingService(IAccountingService, BaseService):
    def __init__(self, repository, vehicles_repository):
        super().__init__(repository)
        self.vehicles_repository = vehicles_repository

    async def list(self, period_from, period_to, vehicle=None):
        return await self.repository.get_between_dates(
            period_from, period_to, vehicle.id if vehicle else None
        )

    async def total(self, period_from, period_to):
        records = await self.repository.get_between_dates(period_from, period_to)
        return sum((r.amount for r in records if r.amount is not None), Decimal("0"))

    async def get_by_vehicle(self, vehicle_id):
        return await self.repository.get_by_vehicle(vehicle_id)

    @abstractmethod
    def _create_record(self, data):
        pass

    async def _ensure_vehicle_exists(self, vehicle_id):
        if not await self.vehicles_repository.get_by_id(vehicle_id):
            raise EntityNotFoundError(f"Vehicle with ID {vehicle_id} not found")

    async def _save(self, data):
        return await self.repository.create(self._create_record(data))
