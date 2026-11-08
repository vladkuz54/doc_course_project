from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..dal.db_models import Drivers, Routes, Vehicles
from .services.repair_records_service import MAINTENANCE_TYPE_LABELS

MIN_ROUTE_GAP_MINUTES = 10


@dataclass
class AssignmentRequest:
    route: Routes
    driver: Drivers | None
    vehicle: Vehicles | None
    other_routes: list[Routes]


@dataclass
class CheckResult:
    passed: bool
    reason: str | None = None


def _departure(request):
    return request.route.departure_at.date()


class AssignmentHandler(ABC):
    def __init__(self):
        self._next = None

    def set_next(self, handler):
        self._next = handler
        return handler

    async def handle(self, request):
        result = await self._check(request)
        if not result.passed or self._next is None:
            return result
        return await self._next.handle(request)

    @abstractmethod
    async def _check(self, request):
        pass


class DriverActiveHandler(AssignmentHandler):
    async def _check(self, request):
        if request.driver and request.driver.employment_status != "ACTIVE":
            return CheckResult(
                False,
                f"Водій {request.driver.full_name} звільнений, тому його не можна "
                "призначити на маршрут. Оберіть іншого водія.",
            )
        return CheckResult(True)


class LicenseCategoryHandler(AssignmentHandler):
    async def _check(self, request):
        driver, vehicle = request.driver, request.vehicle
        if not driver or not vehicle:
            return CheckResult(True)
        category = vehicle.required_license_category
        if category not in driver.license_categories:
            return CheckResult(
                False,
                f"Для {vehicle.make} потрібна категорія {category}, а у водія "
                f"{driver.full_name} її немає. Оберіть іншого водія або транспорт.",
            )
        if driver.license_expiry_date < _departure(request):
            return CheckResult(
                False,
                f"Посвідчення водія {driver.full_name} дійсне до "
                f"{driver.license_expiry_date:%d/%m/%Y}, а виїзд — "
                f"{_departure(request):%d/%m/%Y}. Оберіть іншого водія або "
                "спершу оновіть посвідчення.",
            )
        return CheckResult(True)


class MedicalCheckHandler(AssignmentHandler):
    async def _check(self, request):
        driver = request.driver
        if not driver:
            return CheckResult(True)
        if driver.medical_check_status != "VALID":
            state = (
                "ще чекає на підтвердження"
                if driver.medical_check_status == "PENDING"
                else "прострочений"
            )
            return CheckResult(
                False,
                f"Медогляд водія {driver.full_name} {state}. Підтвердьте медогляд "
                "або оберіть іншого водія.",
            )
        if driver.medical_valid_until < _departure(request):
            return CheckResult(
                False,
                f"Медогляд водія {driver.full_name} дійсний до "
                f"{driver.medical_valid_until:%d/%m/%Y}, а виїзд — "
                f"{_departure(request):%d/%m/%Y}. Оберіть іншого водія або "
                "спершу оновіть медогляд.",
            )
        return CheckResult(True)


class VehicleActiveHandler(AssignmentHandler):
    async def _check(self, request):
        if request.vehicle and request.vehicle.status != "ACTIVE":
            return CheckResult(
                False,
                f"Транспорт {request.vehicle.make} ({request.vehicle.vin}) списаний. "
                "Оберіть інший транспорт.",
            )
        return CheckResult(True)


class VehicleMaintenanceHandler(AssignmentHandler):
    def __init__(self, repair_records_service):
        super().__init__()
        self.repair_records_service = repair_records_service

    async def _check(self, request):
        if not request.vehicle:
            return CheckResult(True)
        departure = _departure(request)
        planned_return = request.route.planned_return_at.date()
        for repair in await self.repair_records_service.get_by_vehicle(
            request.vehicle.id
        ):
            if (
                repair.status == "PLANNED"
                and departure <= repair.date <= planned_return
            ):
                return CheckResult(
                    False,
                    f"На {repair.date:%d/%m/%Y} для {request.vehicle.make} "
                    f"заплановано {MAINTENANCE_TYPE_LABELS[repair.type]}, а це "
                    "припадає на час маршруту. Оберіть інший транспорт або "
                    "перенесіть маршрут чи обслуговування.",
                )
        return CheckResult(True)


class InsuranceHandler(AssignmentHandler):
    def __init__(self, insurance_policies_service):
        super().__init__()
        self.insurance_policies_service = insurance_policies_service

    async def _check(self, request):
        if not request.vehicle:
            return CheckResult(True)
        departure = _departure(request)
        policies = await self.insurance_policies_service.get_by_vehicle(
            request.vehicle.id
        )
        if any(p.start_date <= departure <= p.end_date for p in policies):
            return CheckResult(True)
        return CheckResult(
            False,
            f"Транспорт {request.vehicle.make} не має страхового поліса на дату "
            f"виїзду {departure:%d/%m/%Y}. Додайте поліс або оберіть інший транспорт.",
        )


def _end_of(route):
    if route.status == "IN_PROGRESS":
        return max(route.planned_return_at, datetime.now())
    return route.planned_return_at


class ScheduleConflictHandler(AssignmentHandler):
    async def _check(self, request):
        route = request.route
        gap = timedelta(minutes=MIN_ROUTE_GAP_MINUTES)
        for other in request.other_routes:
            end = _end_of(other)
            if (
                route.departure_at - end < gap
                and other.departure_at - _end_of(route) < gap
            ):
                busy = (
                    "Водій"
                    if route.driver_id is not None
                    and other.driver_id == route.driver_id
                    else "Транспорт"
                )
                return CheckResult(
                    False,
                    f"{busy} уже зайнятий на маршруті №{other.id} "
                    f"({other.departure_at:%d/%m/%Y %H:%M} – "
                    f"{end:%d/%m/%Y %H:%M}). Маршрути не можуть перетинатися, "
                    f"і між ними має бути щонайменше {MIN_ROUTE_GAP_MINUTES} "
                    "хвилин. Оберіть інший час, водія або транспорт.",
                )
        return CheckResult(True)
