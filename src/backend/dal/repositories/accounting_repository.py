from sqlalchemy import select

from backend.dal.interfaces.accounting_interfaces import IAccountingRepository
from backend.dal.repositories.base_repository import BaseRepository


class AccountingRepository(IAccountingRepository, BaseRepository):
    async def get_by_vehicle(self, vehicle_id):
        return await self._where(self.model.vehicle_id == vehicle_id)

    async def get_between_dates(self, start, end, vehicle_id=None):
        conditions = [self.model.date.between(start, end)]
        if vehicle_id is not None:
            conditions.append(self.model.vehicle_id == vehicle_id)
        result = await self.session.execute(
            select(self.model).where(*conditions).order_by(self.model.date)
        )
        return result.scalars().all()
