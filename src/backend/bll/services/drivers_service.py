from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from ...dal.db_models import ACTIVE_ROUTE_STATUSES, LICENSE_CATEGORIES
from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.users_interfaces import IUsersRepository
from ..exceptions import (
    BusinessRuleError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from ..interfaces.drivers_interface import IDriversService
from ..observer import DomainEvent
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
    employment_status: Literal["ACTIVE", "DISMISSED"] = "ACTIVE"


class DriverUpdateData(DriverData):
    experience_years: int = Field(ge=0, le=60)
    medical_check_status: Literal["VALID", "EXPIRED", "PENDING"]
    employment_status: Literal["ACTIVE", "DISMISSED"]


class DriverStatusData(BaseModel):
    employment_status: Literal["ACTIVE", "DISMISSED"]


class MedicalApprovalData(BaseModel):
    valid_until: date


class DriversService(IDriversService, EntityManagement):
    entity_name = "Driver"
    status_field = "employment_status"

    def __init__(
        self,
        repository: IDriversRepository,
        users_repository: IUsersRepository,
        routes_repository: IRoutesRepository,
        driver_requests_repository: IDriverRequestsRepository,
    ):
        super().__init__(repository)
        self.users_repository = users_repository
        self.routes_repository = routes_repository
        self.driver_requests_repository = driver_requests_repository

    async def _validate(self, data, id=None):
        if not await self.users_repository.get_by_id(data.user_id):
            raise EntityNotFoundError(f"User with ID {data.user_id} not found")
        existing = await self.repository.get_by_user_id(data.user_id)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"User with ID {data.user_id} already has a driver profile"
            )

    async def _can_change_status(self, entity, status):
        if status != "DISMISSED":
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

    async def submit_request(self, data):
        await self._validate_request(data)
        request = await self.driver_requests_repository.create(
            self.driver_requests_repository.model(**data.model_dump(), status="PENDING")
        )
        driver = await self.get_by_id(request.driver_id)
        if request.type == "LICENSE_UPDATE":
            type = "LICENSE_UPDATE_REQUEST"
            text = f"{driver.full_name} просить оновити посвідчення до категорії {request.new_license_category}"
        else:
            type = "MEDICAL_CHECK_REQUEST"
            text = f"{driver.full_name} подав запит на підтвердження медогляду"
        await self._notify(DomainEvent(type, "driver_requests", request.id, text))
        return request

    async def approve_license_update(self, request_id):
        request = await self._get_pending_request(request_id, "LICENSE_UPDATE")
        driver = await self.get_by_id(request.driver_id)
        driver.license_categories = [
            *driver.license_categories,
            request.new_license_category,
        ]
        if request.new_license_expiry_date:
            driver.license_expiry_date = request.new_license_expiry_date
        request.status = "APPROVED"
        return await self.driver_requests_repository.update(request)

    async def approve_medical_check(self, request_id, valid_until):
        request = await self._get_pending_request(request_id, "MEDICAL_CHECK")
        if valid_until <= date.today():
            raise BusinessRuleError("valid_until must be after today")
        driver = await self.get_by_id(request.driver_id)
        driver.medical_valid_until = valid_until
        driver.medical_check_date = date.today()
        driver.medical_check_status = "VALID"
        request.status = "APPROVED"
        return await self.driver_requests_repository.update(request)

    async def get_license_expiring(self, until):
        return await self.repository.get_license_expiring(until)

    async def get_medical_check_due(self, until):
        return await self.repository.get_medical_check_due(until)

    async def _validate_request(self, data):
        driver = await self.get_by_id(data.driver_id)
        pending = [
            r
            for r in await self.driver_requests_repository.get_by_driver(data.driver_id)
            if r.status == "PENDING" and r.type == data.type
        ]
        if data.type == "MEDICAL_CHECK":
            if data.new_license_category or data.new_license_expiry_date:
                raise BusinessRuleError(
                    "Medical check request cannot contain license fields"
                )
            if pending:
                raise BusinessRuleError(
                    "Driver already has a pending medical check request"
                )
            return
        if data.new_license_category is None:
            raise BusinessRuleError("License update request needs new_license_category")
        if data.new_license_category in driver.license_categories:
            raise BusinessRuleError(
                f"Driver already has license category {data.new_license_category}"
            )
        if any(r.new_license_category == data.new_license_category for r in pending):
            raise BusinessRuleError(
                f"Driver already has a pending request for category {data.new_license_category}"
            )

    async def _get_pending_request(self, request_id, type):
        request = await self.driver_requests_repository.get_by_id(request_id)
        if not request:
            raise EntityNotFoundError(f"Driver request with ID {request_id} not found")
        if request.type != type:
            raise BusinessRuleError(
                f"Driver request with ID {request_id} is not a {type} request"
            )
        if request.status != "PENDING":
            raise BusinessRuleError(
                f"Driver request with ID {request_id} is not pending"
            )
        return request
