from datetime import date
from typing import Literal

from pydantic import BaseModel

from ...dal.db_models import LICENSE_CATEGORIES
from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ..exceptions import BusinessRuleError, EntityNotFoundError
from ..interfaces.driver_requests_interface import IDriverRequestsService
from .base_service import BaseService


class DriverRequestData(BaseModel):
    driver_id: int
    type: Literal["LICENSE_UPDATE", "MEDICAL_CHECK"]
    status: Literal["PENDING", "APPROVED"] = "PENDING"
    new_license_category: Literal[LICENSE_CATEGORIES] | None = None
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
        driver = await self.drivers_repository.get_by_id(data.driver_id)
        if not driver:
            raise EntityNotFoundError(f"Driver with ID {data.driver_id} not found")
        if data.type == "LICENSE_UPDATE":
            if data.new_license_category is None:
                raise BusinessRuleError(
                    "License update request needs new_license_category"
                )
            if id is None and data.new_license_category in driver.license_categories:
                raise BusinessRuleError(
                    f"Driver already has license category {data.new_license_category}"
                )

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)
