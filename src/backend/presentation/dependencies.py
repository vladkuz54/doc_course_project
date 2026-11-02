from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..bll.services.deadline_monitor import DeadlineMonitor
from ..bll.services.driver_requests_service import DriverRequestsService
from ..bll.services.drivers_service import DriversService
from ..bll.services.fuel_records_service import FuelRecordsService
from ..bll.services.insurance_policies_service import InsurancePoliciesService
from ..bll.services.notifications_service import NotificationsService
from ..bll.services.repair_records_service import RepairRecordsService
from ..bll.services.route_stops_service import RouteStopsService
from ..bll.services.routes_service import RoutesService
from ..bll.services.users_service import UsersService
from ..bll.services.vehicles_service import VehiclesService
from ..dal import Session
from ..dal.repositories.driver_requests_repository import DriverRequestsRepository
from ..dal.repositories.drivers_repository import DriversRepository
from ..dal.repositories.fuel_records_repository import FuelRecordsRepository
from ..dal.repositories.insurance_policies_repository import InsurancePoliciesRepository
from ..dal.repositories.notifications_repository import NotificationsRepository
from ..dal.repositories.repair_records_repository import RepairRecordsRepository
from ..dal.repositories.route_stops_repository import RouteStopsRepository
from ..dal.repositories.routes_repository import RoutesRepository
from ..dal.repositories.users_repository import UsersRepository
from ..dal.repositories.vehicles_repository import VehiclesRepository


async def get_db_session():
    async with Session() as session:
        yield session


def get_users_service(
    session: AsyncSession = Depends(get_db_session),
) -> UsersService:
    return UsersService(UsersRepository(session))


def get_notifications_service(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationsService:
    return NotificationsService(
        NotificationsRepository(session),
        DriversRepository(session),
        VehiclesRepository(session),
        RoutesRepository(session),
        DriverRequestsRepository(session),
    )


def get_drivers_service(
    session: AsyncSession = Depends(get_db_session),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> DriversService:
    service = DriversService(
        DriversRepository(session),
        UsersRepository(session),
        RoutesRepository(session),
        DriverRequestsRepository(session),
    )
    service.attach(notifications)
    return service


def get_driver_requests_service(
    session: AsyncSession = Depends(get_db_session),
) -> DriverRequestsService:
    return DriverRequestsService(DriverRequestsRepository(session))


def get_repair_records_service(
    session: AsyncSession = Depends(get_db_session),
) -> RepairRecordsService:
    return RepairRecordsService(
        RepairRecordsRepository(session), VehiclesRepository(session)
    )


def get_vehicles_service(
    session: AsyncSession = Depends(get_db_session),
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> VehiclesService:
    service = VehiclesService(
        VehiclesRepository(session), RoutesRepository(session), repair_records_service
    )
    service.attach(notifications)
    return service


def get_routes_service(
    session: AsyncSession = Depends(get_db_session),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> RoutesService:
    service = RoutesService(
        RoutesRepository(session),
        DriversRepository(session),
        VehiclesRepository(session),
        RouteStopsRepository(session),
    )
    service.attach(notifications)
    return service


def get_route_stops_service(
    session: AsyncSession = Depends(get_db_session),
) -> RouteStopsService:
    return RouteStopsService(RouteStopsRepository(session))


def get_fuel_records_service(
    session: AsyncSession = Depends(get_db_session),
) -> FuelRecordsService:
    return FuelRecordsService(
        FuelRecordsRepository(session), VehiclesRepository(session)
    )


def get_insurance_policies_service(
    session: AsyncSession = Depends(get_db_session),
) -> InsurancePoliciesService:
    return InsurancePoliciesService(
        InsurancePoliciesRepository(session), VehiclesRepository(session)
    )


def get_deadline_monitor(
    repair_records_service: RepairRecordsService = Depends(get_repair_records_service),
    insurance_policies_service: InsurancePoliciesService = Depends(
        get_insurance_policies_service
    ),
    drivers_service: DriversService = Depends(get_drivers_service),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> DeadlineMonitor:
    monitor = DeadlineMonitor(
        repair_records_service, insurance_policies_service, drivers_service
    )
    monitor.attach(notifications)
    return monitor
