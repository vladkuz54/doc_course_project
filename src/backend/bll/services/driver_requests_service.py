from datetime import date
from typing import Literal

from pydantic import BaseModel

from ...dal.db_models import LICENSE_CATEGORIES
from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.driver_requests_interface import IDriverRequestsService


class DriverRequestData(BaseModel):
    driver_id: int
    type: Literal["LICENSE_UPDATE", "MEDICAL_CHECK"]
    new_license_category: Literal[LICENSE_CATEGORIES] | None = None
    new_license_expiry_date: date | None = None


class DriverRequestsService(IDriverRequestsService):
    entity_name = "Driver request"

    def __init__(self, repository: IDriverRequestsRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, id):
        obj = await self.repository.get_by_id(id)
        if not obj:
            raise EntityNotFoundError(f"{self.entity_name} with ID {id} not found")
        return obj

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)
