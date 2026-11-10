from datetime import date
from typing import Literal

from pydantic import BaseModel

from ...dal.db_models import LICENSE_CATEGORIES
from ...dal.interfaces.driver_requests_interfaces import IDriverRequestsRepository
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ..exceptions import BusinessRuleError, EntityNotFoundError
from ..interfaces.driver_requests_interface import IDriverRequestsService
from ..observer import DomainEvent, Subject
from .read_service import ReadService


class DriverRequestData(BaseModel):
    driver_id: int
    type: Literal["LICENSE_UPDATE", "MEDICAL_CHECK"]
    new_license_category: Literal[LICENSE_CATEGORIES] | None = None
    new_license_expiry_date: date | None = None
    medical_check_date: date | None = None


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


class DriverRequestsService(IDriverRequestsService, ReadService, Subject):
    entity_name = "Запит"

    def __init__(
        self,
        repository: IDriverRequestsRepository,
        drivers_repository: IDriversRepository,
    ):
        ReadService.__init__(self, repository)
        Subject.__init__(self)
        self.drivers_repository = drivers_repository

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

    async def submit_request(self, data):
        await self._validate_request(data)
        request = await self.repository.create(
            self.repository.model(**data.model_dump(), status="PENDING")
        )
        driver = await self._get_driver(request.driver_id)
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
        driver = await self._get_driver(request.driver_id)
        if request.new_license_expiry_date <= driver.license_expiry_date:
            raise BusinessRuleError(
                "Посвідчення водія вже дійсне до "
                f"{driver.license_expiry_date:%d/%m/%Y}, не раніше, ніж у цьому "
                "запиті. Відхиліть запит."
            )
        driver.apply_license_update(request)
        await self.drivers_repository.update(driver)
        request.status = "APPROVED"
        return await self._save_decision(request, "REQUEST_APPROVED", "схвалено")

    async def approve_medical_check(self, request_id):
        request = await self._get_pending_request(request_id, "MEDICAL_CHECK")
        driver = await self._get_driver(request.driver_id)
        if request.medical_check_date <= driver.medical_check_date:
            raise BusinessRuleError(
                f"У водія вже враховано медогляд від {driver.medical_check_date:%d/%m/%Y}, "
                "не раніший за цей запит. Відхиліть запит."
            )
        driver.apply_medical_check(request)
        await self.drivers_repository.update(driver)
        request.status = "APPROVED"
        return await self._save_decision(request, "REQUEST_APPROVED", "схвалено")

    async def reject_request(self, request_id):
        request = await self._get_pending_request(request_id)
        request.reject()
        return await self._save_decision(request, "REQUEST_REJECTED", "відхилено")

    async def _validate_request(self, data):
        driver = await self._get_driver(data.driver_id)
        if driver.is_dismissed():
            raise BusinessRuleError(
                f"{driver.full_name} звільнено, тому запит подати не можна."
            )
        pending = [
            r
            for r in await self.repository.get_by_driver(data.driver_id)
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
            if data.medical_check_date <= driver.medical_check_date:
                raise BusinessRuleError(
                    f"Медогляд від {driver.medical_check_date:%d/%m/%Y} уже "
                    "враховано. Вкажіть дату нового медогляду."
                )
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
        request = await self.repository.update(request)
        driver = await self._get_driver(request.driver_id)
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
        request = await self.get_by_id(request_id)
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

    async def _get_driver(self, driver_id):
        driver = await self.drivers_repository.get_by_id(driver_id)
        if not driver:
            raise EntityNotFoundError(
                "Водія не знайдено. Можливо, запис уже видалено — оновіть сторінку."
            )
        return driver
