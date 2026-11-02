from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..dal.db_models import Drivers, Routes, Vehicles

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
            return CheckResult(False, "The driver is not active")
        return CheckResult(True)


class LicenseCategoryHandler(AssignmentHandler):
    async def _check(self, request):
        driver, vehicle = request.driver, request.vehicle
        if not driver or not vehicle:
            return CheckResult(True)
        category = vehicle.required_license_category
        if category not in driver.license_categories:
            return CheckResult(False, f"The driver has no license category {category}")
        if driver.license_expiry_date < _departure(request):
            return CheckResult(False, "The driver's license expires before departure")
        return CheckResult(True)


class MedicalCheckHandler(AssignmentHandler):
    async def _check(self, request):
        driver = request.driver
        if not driver:
            return CheckResult(True)
        if driver.medical_check_status != "VALID":
            return CheckResult(False, "The driver's medical check is not valid")
        if driver.medical_valid_until < _departure(request):
            return CheckResult(
                False, "The driver's medical check expires before departure"
            )
        return CheckResult(True)


class VehicleActiveHandler(AssignmentHandler):
    async def _check(self, request):
        if request.vehicle and request.vehicle.status != "ACTIVE":
            return CheckResult(False, "The vehicle is not active")
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
                    False, f"The vehicle has maintenance planned on {repair.date}"
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
        return CheckResult(False, "The vehicle has no insurance on the departure date")


class ScheduleConflictHandler(AssignmentHandler):
    async def _check(self, request):
        route = request.route
        gap = timedelta(minutes=MIN_ROUTE_GAP_MINUTES)
        for other in request.other_routes:
            end = other.planned_return_at
            if other.status == "IN_PROGRESS":
                end = max(end, datetime.now())
            if (
                route.departure_at < end + gap
                and other.departure_at < route.planned_return_at + gap
            ):
                return CheckResult(
                    False,
                    f"The route needs at least {MIN_ROUTE_GAP_MINUTES} minutes "
                    f"between it and route {other.id}",
                )
        return CheckResult(True)
