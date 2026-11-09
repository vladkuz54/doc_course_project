from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from ...dal.db_models import (
    ACTIVE_ROUTE_STATUSES,
    LICENSE_CATEGORIES,
    medical_valid_until,
)
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.users_interfaces import IUsersRepository
from ..exceptions import (
    BusinessRuleError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from ..interfaces.drivers_interface import IDriversService
from .entity_management import EntityManagement


class DriverData(BaseModel):
    user_id: int
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    license_categories: list[Literal[LICENSE_CATEGORIES]] = Field(min_length=1)
    experience_years: int = Field(0, ge=0, le=60)
    license_expiry_date: date
    medical_check_date: date
    employment_status: Literal["ACTIVE", "DISMISSED"] = "ACTIVE"


class DriverUpdateData(DriverData):
    experience_years: int = Field(ge=0, le=60)
    employment_status: Literal["ACTIVE", "DISMISSED"]


class DriverStatusData(BaseModel):
    employment_status: Literal["ACTIVE", "DISMISSED"]


class DriversService(IDriversService, EntityManagement):
    entity_name = "Водія"
    status_field = "employment_status"
    status_labels = {"ACTIVE": "Працює", "DISMISSED": "Звільнений"}
    status_blocked_message = (
        "Водія не можна звільнити, поки на нього є заплановані маршрути "
        "або маршрути в дорозі. Спочатку завершіть, скасуйте або передайте "
        "ці маршрути іншому водієві."
    )

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
        user = await self.users_repository.get_by_id(data.user_id)
        if not user:
            raise EntityNotFoundError(
                "Обліковий запис для цього водія не знайдено. Оновіть сторінку."
            )
        if user.role != "DRIVER":
            raise BusinessRuleError(
                f"«{user.username}» — обліковий запис адміністратора. Профіль "
                "водія можна створити лише для облікового запису водія."
            )
        existing = await self.repository.get_by_user_id(data.user_id)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"Користувач «{user.username}» уже має профіль водія. "
                "Відредагуйте наявний профіль."
            )

    async def _can_change_status(self, entity, status):
        if status != "DISMISSED":
            return True
        routes = await self.routes_repository.get_by_driver(entity.id)
        return not any(r.status in ACTIVE_ROUTE_STATUSES for r in routes)

    def to_fields(self, data):
        fields = data.model_dump()
        fields["medical_valid_until"] = medical_valid_until(data.medical_check_date)
        return fields

    async def get_by_user_id(self, user_id):
        driver = await self.repository.get_by_user_id(user_id)
        if not driver:
            raise EntityNotFoundError(
                "Ваш обліковий запис ще не пов'язаний із профілем водія. "
                "Зверніться до адміністратора."
            )
        return driver

    async def get_by_driver(self, driver_id):
        return [await self.get_by_id(driver_id)]

    async def get_license_expiring(self, until):
        return await self.repository.get_license_expiring(until)

    async def get_medical_check_due(self, until):
        return await self.repository.get_medical_check_due(until)
