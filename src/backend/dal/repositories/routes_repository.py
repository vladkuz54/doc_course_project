from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..db_models import Routes
from ..interfaces.routes_interfaces import IRoutesRepository
from .base_repository import BaseRepository


class RoutesRepository(IRoutesRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Routes)

    async def get_by_id(self, id):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.id == id)
            .options(selectinload(self.model.stops))
        )
        return result.scalars().first()

    async def get_by_driver(self, driver_id):
        return await self._where(self.model.driver_id == driver_id)

    async def get_by_vehicle(self, vehicle_id):
        return await self._where(self.model.vehicle_id == vehicle_id)

    async def get_between_dates(self, start, end):
        return await self._where(self.model.departure_at.between(start, end))
