from ..db_models import Vehicles
from ..interfaces.vehicles_interfaces import IVehiclesRepository
from .base_repository import BaseRepository


class VehiclesRepository(IVehiclesRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Vehicles)

    async def get_by_vin(self, vin):
        return await self._first(self.model.vin == vin)

    async def get_active(self):
        return await self._where(self.model.status == "ACTIVE")
