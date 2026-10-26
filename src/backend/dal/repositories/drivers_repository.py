from ..db_models import Drivers
from ..interfaces.drivers_interfaces import IDriversRepository
from .base_repository import BaseRepository


class DriversRepository(IDriversRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Drivers)

    async def get_by_user_id(self, user_id):
        return await self._first(self.model.user_id == user_id)

    async def get_active(self):
        return await self._where(self.model.employment_status == "ACTIVE")
