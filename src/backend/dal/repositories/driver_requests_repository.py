from ..db_models import DriverRequests
from ..interfaces.driver_requests_interfaces import IDriverRequestsRepository
from .base_repository import BaseRepository


class DriverRequestsRepository(IDriverRequestsRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, DriverRequests)

    async def get_by_driver(self, driver_id):
        return await self._where(self.model.driver_id == driver_id)
