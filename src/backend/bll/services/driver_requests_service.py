from datetime import date
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ..exceptions import EntityNotFoundError
from ..interfaces.driver_requests_interface import IDriverRequestsService
from .base_service import BaseService


class DriverRequestData(BaseModel):
    driver_id: int
    type: Literal["LICENSE_UPDATE", "MEDICAL_CHECK"]
    status: Literal["PENDING", "APPROVED"] = "PENDING"
    new_license_category: str | None = None
    new_license_expiry_date: date | None = None


class DriverRequestsService(IDriverRequestsService, BaseService):
    entity_name = "Driver request"

    def __init__(
        self,
        repository: IDriverRequestsRepository,
        drivers_repository: IDriversRepository,
    ):
        super().__init__(repository)
        self.drivers_repository = drivers_repository

    async def _validate(self, data, id=None):
        if not await self.drivers_repository.get_by_id(data.driver_id):
            raise EntityNotFoundError(f"Driver with ID {data.driver_id} not found")
