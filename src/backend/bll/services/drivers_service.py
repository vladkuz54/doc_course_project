from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from ...dal.db_models import ACTIVE_ROUTE_STATUSES, LICENSE_CATEGORIES
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.users_interfaces import IUsersRepository
from ..exceptions import EntityAlreadyExistsError, EntityNotFoundError
from ..interfaces.drivers_interface import IDriversService
from .entity_management import EntityManagement


class DriverData(BaseModel):
    user_id: int
    full_name: str
    license_categories: list[Literal[LICENSE_CATEGORIES]] = Field(min_length=1)
    experience_years: int = Field(0, ge=0, le=60)
    license_expiry_date: date
    medical_check_date: date
    medical_valid_until: date
    medical_check_status: Literal["VALID", "EXPIRED", "PENDING"] = "VALID"
    employment_status: Literal["ACTIVE", "ON_LEAVE", "DISMISSED"] = "ACTIVE"


class DriverStatusData(BaseModel):
    employment_status: Literal["ACTIVE", "ON_LEAVE", "DISMISSED"]


class DriversService(IDriversService, EntityManagement):
    entity_name = "Driver"
    status_field = "employment_status"

    def __init__(
        self,
        repository: IDriversRepository,
        users_repository: IUsersRepository,
        routes_repository: IRoutesRepository,
    ):
        super().__init__(repository)
        self.users_repository = users_repository
        self.routes_repository = routes_repository

    async def _validate(self, data, id=None):
        if not await self.users_repository.get_by_id(data.user_id):
            raise EntityNotFoundError(f"User with ID {data.user_id} not found")
        existing = await self.repository.get_by_user_id(data.user_id)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"User with ID {data.user_id} already has a driver profile"
            )

    async def _can_change_status(self, entity, status):
        if status == "ACTIVE":
            return True
        routes = await self.routes_repository.get_by_driver(entity.id)
        return not any(r.status in ACTIVE_ROUTE_STATUSES for r in routes)

    async def get_by_user_id(self, user_id):
        driver = await self.repository.get_by_user_id(user_id)
        if not driver:
            raise EntityNotFoundError(f"User with ID {user_id} has no driver profile")
        return driver

    async def get_by_driver(self, driver_id):
        return [await self.get_by_id(driver_id)]
