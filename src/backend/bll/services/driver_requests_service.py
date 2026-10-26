from datetime import date
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
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
        super().__init__(repository, {"driver_id": (drivers_repository, "Driver")})
