from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from ...dal.db_models import (
    ACTIVE_ROUTE_STATUSES,
    LICENSE_CATEGORIES,
    medical_valid_until,
)
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
    employment_status: Literal["ACTIVE", "DISMISSED"] = "ACTIVE"


class DriverUpdateData(DriverData):
    experience_years: int = Field(ge=0, le=60)
    employment_status: Literal["ACTIVE", "DISMISSED"]


class DriverStatusData(BaseModel):
    employment_status: Literal["ACTIVE", "DISMISSED"]


REQUEST_TYPE_LABELS = {
    "LICENSE_UPDATE": "оновлення посвідчення",
    "MEDICAL_CHECK": "підтвердження медогляду",
}
REQUEST_STATUS_LABELS = {"APPROVED": "схвалено", "REJECTED": "відхилено"}


def _license_details(request):
    details = f"дійсне до {request.new_license_expiry_date:%d.%m.%Y}"
    if request.new_license_category:
        details += f", категорія {request.new_license_category}"
    return details


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
        driver_requests_repository: IDriverRequestsRepository,
    ):
        super().__init__(repository)
        self.users_repository = users_repository
        self.routes_repository = routes_repository
        self.driver_requests_repository = driver_requests_repository

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

    async def submit_request(self, data):
        await self._validate_request(data)
        request = await self.driver_requests_repository.create(
            self.driver_requests_repository.model(**data.model_dump(), status="PENDING")
        )
        driver = await self.get_by_id(request.driver_id)
        if request.type == "LICENSE_UPDATE":
            type = "LICENSE_UPDATE_REQUEST"
            text = f"{driver.full_name} повідомляє про нове посвідчення, {_license_details(request)}"
        else:
            type = "MEDICAL_CHECK_REQUEST"
            text = f"{driver.full_name} повідомляє про медогляд {request.medical_check_date:%d.%m.%Y}"
        await self._notify(DomainEvent(type, "driver_requests", request.id, text))
        return request

    async def approve_license_update(self, request_id):
        request = await self._get_pending_request(request_id, "LICENSE_UPDATE")
        driver = await self.get_by_id(request.driver_id)
        if request.new_license_category:
            driver.license_categories = [
                *driver.license_categories,
                request.new_license_category,
            ]
        driver.license_expiry_date = request.new_license_expiry_date
        request.status = "APPROVED"
        return await self._save_decision(request, "REQUEST_APPROVED", "схвалено")

    async def approve_medical_check(self, request_id):
        request = await self._get_pending_request(request_id, "MEDICAL_CHECK")
        driver = await self.get_by_id(request.driver_id)
        driver.medical_check_date = request.medical_check_date
        driver.medical_valid_until = medical_valid_until(request.medical_check_date)
        request.status = "APPROVED"
        return await self._save_decision(request, "REQUEST_APPROVED", "схвалено")

    async def reject_request(self, request_id):
        request = await self._get_pending_request(request_id)
        request.status = "REJECTED"
        return await self._save_decision(request, "REQUEST_REJECTED", "відхилено")

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
                    "Запит на медогляд не може містити категорію чи термін "
                    "дії посвідчення."
                )
            if data.medical_check_date is None:
                raise BusinessRuleError("Вкажіть дату, коли ви пройшли медогляд.")
            if data.medical_check_date > date.today():
                raise BusinessRuleError("Дата медогляду не може бути в майбутньому.")
            if pending:
                raise BusinessRuleError(
                    "Ви вже подали запит на підтвердження медогляду. Зачекайте, "
                    "доки адміністратор його розгляне."
                )
            return
        if data.medical_check_date is not None:
            raise BusinessRuleError(
                "Запит на оновлення посвідчення не може містити дату медогляду."
            )
        if data.new_license_expiry_date is None:
            raise BusinessRuleError("Вкажіть, до якої дати дійсне нове посвідчення.")
        if data.new_license_expiry_date <= max(
            date.today(), driver.license_expiry_date
        ):
            raise BusinessRuleError(
                "Нове посвідчення має бути дійсним довше, ніж поточне "
                f"(до {driver.license_expiry_date:%d/%m/%Y})."
            )
        if data.new_license_category in driver.license_categories:
            raise BusinessRuleError(
                f"У вас уже є категорія {data.new_license_category}."
            )
        if pending:
            raise BusinessRuleError(
                "Ви вже подали запит на оновлення посвідчення. Зачекайте, "
                "доки адміністратор його розгляне."
            )

    async def _save_decision(self, request, type, verb):
        request = await self.driver_requests_repository.update(request)
        driver = await self.get_by_id(request.driver_id)
        if request.type == "LICENSE_UPDATE":
            subject = f"оновлення посвідчення ({_license_details(request)})"
        else:
            subject = "підтвердження медогляду"
        await self._notify(
            DomainEvent(
                type,
                "driver_requests",
                request.id,
                f"Ваш запит на {subject} {verb}",
                driver.user_id,
            )
        )
        return request

    async def _get_pending_request(self, request_id, type=None):
        request = await self.driver_requests_repository.get_by_id(request_id)
        if not request:
            raise EntityNotFoundError(
                "Запит не знайдено. Можливо, запис уже видалено — оновіть сторінку."
            )
        if type is not None and request.type != type:
            raise BusinessRuleError(
                f"Це запит на {REQUEST_TYPE_LABELS[request.type]}, "
                f"а не на {REQUEST_TYPE_LABELS[type]}."
            )
        if request.status != "PENDING":
            raise BusinessRuleError(
                f"Цей запит уже {REQUEST_STATUS_LABELS[request.status]}. "
                "Оновіть сторінку, щоб побачити його стан."
            )
        return request
