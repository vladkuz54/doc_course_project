from datetime import datetime, time
from typing import Annotated, Literal

from pydantic import BaseModel, Field, NaiveDatetime, StringConstraints

from ...dal.db_models import ACTIVE_ROUTE_STATUSES, RouteStops
from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.route_stops_interfaces import IRouteStopsRepository
from ...dal.interfaces.routes_interfaces import IRoutesRepository
from ...dal.interfaces.vehicles_interfaces import IVehiclesRepository
from ...dal.route_states import ROUTE_STATUS_LABELS, RouteActionNotAllowed
from ..assignment_checks import (
    AssignmentRequest,
    DriverActiveHandler,
    InsuranceHandler,
    LicenseCategoryHandler,
    MedicalCheckHandler,
    ScheduleConflictHandler,
    VehicleActiveHandler,
    VehicleMaintenanceHandler,
)
from ..exceptions import BusinessRuleError, EntityNotFoundError
from ..interfaces.insurance_policies_interface import IInsurancePoliciesService
from ..interfaces.repair_records_interface import IRepairRecordsService
from ..interfaces.routes_interface import IRoutesService
from ..observer import DomainEvent
from .entity_management import EntityManagement

StopAddress = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RouteData(BaseModel):
    driver_id: int | None = None
    vehicle_id: int | None = None
    distance: float = Field(gt=0, le=100000)
    departure_at: NaiveDatetime


class RouteCreateData(RouteData):
    stops: list[StopAddress] = Field(min_length=1)


class RouteStatusData(BaseModel):
    status: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]


class RouteStopsData(BaseModel):
    stops: list[StopAddress]


class RouteDriverData(BaseModel):
    driver_id: int


class RouteVehicleData(BaseModel):
    vehicle_id: int


class RouteStartData(BaseModel):
    started_at: NaiveDatetime | None = None


class RouteCompleteData(BaseModel):
    returned_at: NaiveDatetime | None = None


class RoutesService(IRoutesService, EntityManagement):
    entity_name = "Маршрут"
    status_labels = ROUTE_STATUS_LABELS

    def __init__(
        self,
        repository: IRoutesRepository,
        drivers_repository: IDriversRepository,
        vehicles_repository: IVehiclesRepository,
        route_stops_repository: IRouteStopsRepository,
        repair_records_service: IRepairRecordsService,
        insurance_policies_service: IInsurancePoliciesService,
    ):
        super().__init__(repository)
        self.drivers_repository = drivers_repository
        self.vehicles_repository = vehicles_repository
        self.route_stops_repository = route_stops_repository
        self._assignment_chain = DriverActiveHandler()
        self._assignment_chain.set_next(LicenseCategoryHandler()).set_next(
            MedicalCheckHandler()
        ).set_next(VehicleActiveHandler()).set_next(
            VehicleMaintenanceHandler(repair_records_service)
        ).set_next(
            InsuranceHandler(insurance_policies_service)
        ).set_next(
            ScheduleConflictHandler()
        )

    async def _validate(self, data, id=None):
        if data.driver_id is not None:
            await self._get_driver(data.driver_id)
        if data.vehicle_id is not None:
            await self._get_vehicle(data.vehicle_id)
        if id is None and (data.driver_id is not None or data.vehicle_id is not None):
            await self._check_assignment(self._build_route(data))

    def to_fields(self, data):
        return data.model_dump(exclude={"stops"})

    async def _save(self, data):
        return await self.repository.create(self._build_route(data))

    async def _after_add(self, entity):
        if entity.driver_id is not None:
            await self._publish_assigned(
                entity, await self._get_driver(entity.driver_id)
            )

    async def update(self, id, data):
        route = await self.get_by_id(id)
        old_driver_id, old_distance = route.driver_id, route.distance
        route.change_distance(data.distance)
        await self._validate(data, id)
        if data.driver_id is None and route.driver_id is not None:
            raise BusinessRuleError(
                "Не можна прибрати водія із запланованого маршруту. "
                "Призначте іншого водія або скасуйте маршрут."
            )
        if data.vehicle_id is None and route.vehicle_id is not None:
            raise BusinessRuleError(
                "Не можна прибрати транспорт із запланованого маршруту. "
                "Призначте інший транспорт або скасуйте маршрут."
            )
        new_driver = None
        changes = []
        if data.driver_id != route.driver_id:
            new_driver = await self._get_driver(data.driver_id)
            route.reassign_driver(new_driver)
        if data.vehicle_id != route.vehicle_id:
            vehicle = await self._get_vehicle(data.vehicle_id)
            route.reassign_vehicle(vehicle)
            changes.append(f"транспорт {vehicle.make}")
        if data.departure_at != route.departure_at:
            route.reschedule(data.departure_at)
            changes.append(f"час виїзду {data.departure_at:%d.%m.%Y %H:%M}")
        if data.distance != old_distance:
            changes.append(f"відстань {data.distance:g} км")
        route.update_planned_return()
        await self._check_assignment(route)
        route = await self.repository.update(route)
        if new_driver:
            await self._publish_moved(route, old_driver_id, new_driver)
        elif changes:
            await self._publish_updated(route, changes)
        return route

    async def delete(self, id):
        route = await self.get_by_id(id)
        route.delete()
        return await self.repository.delete(id)

    async def _apply_status(self, entity, status):
        if status == "IN_PROGRESS":
            await self.start(entity.id)
        elif status == "COMPLETED":
            await self.complete(entity.id)
        elif status == "CANCELLED":
            await self.cancel(entity.id)
        else:
            raise BusinessRuleError(
                "Маршрут не можна повернути до статусу «Заплановано»."
            )

    async def list_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)

    async def list(self, period_from, period_to, vehicle=None):
        return await self.repository.get_between_dates(
            datetime.combine(period_from, time.min),
            datetime.combine(period_to, time.max),
            vehicle.id if vehicle else None,
        )

    async def assign_driver(self, route_id, driver_id):
        route = await self.get_by_id(route_id)
        driver = await self._get_driver(driver_id)
        old_driver_id = route.driver_id
        route.reassign_driver(driver)
        await self._check_assignment(route)
        route = await self.repository.update(route)
        await self._publish_moved(route, old_driver_id, driver)
        return route

    async def assign_vehicle(self, route_id, vehicle_id):
        route = await self.get_by_id(route_id)
        vehicle = await self._get_vehicle(vehicle_id)
        changed = vehicle.id != route.vehicle_id
        route.reassign_vehicle(vehicle)
        await self._check_assignment(route)
        route = await self.repository.update(route)
        if changed:
            await self._publish_updated(route, [f"транспорт {vehicle.make}"])
        return route

    async def reschedule(self, route_id, departure_at):
        route = await self.get_by_id(route_id)
        route.reschedule(departure_at)
        route.update_planned_return()
        await self._check_assignment(route)
        route = await self.repository.update(route)
        await self._publish_updated(
            route, [f"час виїзду {departure_at:%d.%m.%Y %H:%M}"]
        )
        return route

    async def edit_stops(self, route_id, stops):
        route = await self.get_by_id(route_id)
        route.edit_stops(stops)
        route.update_planned_return()
        await self._check_assignment(route)
        addresses = " → ".join(stop.address for stop in route.stops)
        route = await self.repository.update(route)
        await self._publish_updated(route, [f"зупинки {addresses}"])
        return route

    async def start(self, route_id, started_at=None):
        route = await self.get_by_id(route_id)
        await self._ensure_nothing_in_progress(route)
        route.start(started_at)
        await self._check_assignment(route)
        return await self.repository.update(route)

    async def arrive_at_stop(self, route_id, stop_id):
        route = await self.get_by_id(route_id)
        stop = await self.route_stops_repository.get_by_id(stop_id)
        if not stop:
            raise EntityNotFoundError(
                "Цю зупинку не знайдено. Можливо, маршрут змінили — "
                "оновіть сторінку."
            )
        route.arrive_at_stop(stop)
        return await self.repository.update(route)

    async def complete(self, route_id, returned_at=None):
        route = await self.get_by_id(route_id)
        route.complete(returned_at)
        return await self.repository.update(route)

    async def cancel(self, route_id):
        route = await self.get_by_id(route_id)
        route.cancel()
        route = await self.repository.update(route)
        if route.driver_id is not None:
            await self._publish_to_driver(
                route.driver_id,
                "ROUTE_CANCELLED",
                route,
                f"Маршрут №{route.id} на {route.departure_at:%d.%m.%Y %H:%M} скасовано",
            )
        return route

    def _build_route(self, data):
        route = self.repository.model(
            **self.to_fields(data),
            stops=[
                RouteStops(order_no=number, address=address)
                for number, address in enumerate(data.stops, 1)
            ],
        )
        route.update_planned_return()
        return route

    async def _check_assignment(self, route):
        driver = vehicle = None
        others = []
        if route.driver_id is not None:
            driver = await self.drivers_repository.get_by_id(route.driver_id)
            others += await self.repository.get_by_driver(route.driver_id)
        if route.vehicle_id is not None:
            vehicle = await self.vehicles_repository.get_by_id(route.vehicle_id)
            others += await self.repository.get_by_vehicle(route.vehicle_id)
        other_routes = {
            r.id: r
            for r in others
            if r.status in ACTIVE_ROUTE_STATUSES and r.id != route.id
        }
        result = await self._assignment_chain.handle(
            AssignmentRequest(route, driver, vehicle, [*other_routes.values()])
        )
        if not result.passed:
            raise BusinessRuleError(result.reason)

    async def _get_driver(self, driver_id):
        driver = await self.drivers_repository.get_by_id(driver_id)
        if not driver:
            raise EntityNotFoundError(
                "Обраного водія не знайдено. Оновіть сторінку й оберіть іншого."
            )
        return driver

    async def _get_vehicle(self, vehicle_id):
        vehicle = await self.vehicles_repository.get_by_id(vehicle_id)
        if not vehicle:
            raise EntityNotFoundError(
                "Обраний транспорт не знайдено. Оновіть сторінку й оберіть інший."
            )
        return vehicle

    async def _ensure_nothing_in_progress(self, route):
        others = []
        if route.driver_id is not None:
            others += await self.repository.get_by_driver(route.driver_id)
        if route.vehicle_id is not None:
            others += await self.repository.get_by_vehicle(route.vehicle_id)
        for other in others:
            if other.id != route.id and other.status == "IN_PROGRESS":
                busy = (
                    "Водій"
                    if route.driver_id is not None
                    and other.driver_id == route.driver_id
                    else "Транспорт"
                )
                raise BusinessRuleError(
                    f"{busy} ще на маршруті №{other.id}, який не завершено. "
                    "Спочатку завершіть той маршрут."
                )

    async def _publish_moved(self, route, old_driver_id, new_driver):
        if old_driver_id is not None and old_driver_id != new_driver.id:
            await self._publish_to_driver(
                old_driver_id,
                "ROUTE_UNASSIGNED",
                route,
                f"Маршрут №{route.id} на {route.departure_at:%d.%m.%Y %H:%M} "
                "передано іншому водію",
            )
        await self._publish_assigned(route, new_driver)

    async def _publish_updated(self, route, changes):
        if route.driver_id is not None:
            await self._publish_to_driver(
                route.driver_id,
                "ROUTE_UPDATED",
                route,
                f"Маршрут №{route.id} змінено: {'; '.join(changes)}",
            )

    async def _publish_to_driver(self, driver_id, type, route, text):
        driver = await self._get_driver(driver_id)
        await self._notify(DomainEvent(type, "routes", route.id, text, driver.user_id))

    async def _publish_assigned(self, route, driver):
        await self._notify(
            DomainEvent(
                "ROUTE_ASSIGNED",
                "routes",
                route.id,
                f"Вам призначено маршрут №{route.id} на {route.departure_at:%d.%m.%Y %H:%M}",
                driver.user_id,
            )
        )
