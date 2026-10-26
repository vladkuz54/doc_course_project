from datetime import date
from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.users_interfaces import IUsersRepository
from ..exceptions import EntityAlreadyExistsError
from ..interfaces.drivers_interface import IDriversService
from .base_service import BaseService


class DriverData(BaseModel):
    user_id: int
    full_name: str
    license_category: str
    experience_years: int = 0
    license_expiry_date: date
    medical_check_date: date
    medical_valid_until: date
    medical_check_status: Literal["VALID", "EXPIRED", "PENDING"] = "VALID"
    employment_status: Literal["ACTIVE", "DISMISSED"] = "ACTIVE"


class DriversService(IDriversService, BaseService):
    entity_name = "Driver"

    def __init__(
        self, repository: IDriversRepository, users_repository: IUsersRepository
    ):
        super().__init__(repository, {"user_id": (users_repository, "User")})

    async def validate(self, data, id=None):
        await super().validate(data, id)
        existing = await self.repository.get_by_user_id(data.user_id)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"User with ID {data.user_id} already has a driver profile"
            )
