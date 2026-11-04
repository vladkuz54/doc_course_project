from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declared_attr, relationship

from . import Base, engine
from .route_states import RouteActionNotAllowed, RouteState


def StrEnum(*values, name):
    return Enum(*values, name=name, native_enum=False, create_constraint=True)


LICENSE_CATEGORIES = (
    "A1",
    "A",
    "B1",
    "B",
    "BE",
    "C1",
    "C1E",
    "C",
    "CE",
    "D1",
    "D1E",
    "D",
    "DE",
    "T",
)
MIN_VEHICLE_YEAR = 1980
ACTIVE_ROUTE_STATUSES = ("PLANNED", "IN_PROGRESS")
AVERAGE_SPEED_KMH = 60
MINUTES_PER_STOP = 15


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(StrEnum("DRIVER", "ADMIN", name="user_role"), nullable=False)

    driver = relationship(
        "Drivers", back_populates="user", uselist=False, passive_deletes="all"
    )


class Drivers(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint("experience_years >= 0", name="ck_drivers_experience"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    experience_years = Column(Integer, nullable=False, default=0)
    license_expiry_date = Column(Date, nullable=False)
    medical_check_date = Column(Date, nullable=False)
    medical_valid_until = Column(Date, nullable=False)
    medical_check_status = Column(
        StrEnum("VALID", "EXPIRED", "PENDING", name="medical_check_status"),
        nullable=False,
        default="VALID",
    )
    employment_status = Column(
        StrEnum("ACTIVE", "DISMISSED", name="employment_status"),
        nullable=False,
        default="ACTIVE",
    )

    user = relationship("Users", back_populates="driver")
    requests = relationship(
        "DriverRequests", back_populates="driver", passive_deletes="all"
    )
    routes = relationship("Routes", back_populates="driver", passive_deletes="all")
    categories = relationship(
        "DriverLicenseCategories",
        back_populates="driver",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def license_categories(self):
        return sorted(
            (c.category for c in self.categories), key=LICENSE_CATEGORIES.index
        )

    @license_categories.setter
    def license_categories(self, values):
        existing = {c.category: c for c in self.categories}
        self.categories = [
            existing.get(v) or DriverLicenseCategories(category=v)
            for v in dict.fromkeys(values)
        ]


class DriverLicenseCategories(Base):
    __tablename__ = "driver_license_categories"

    driver_id = Column(
        Integer, ForeignKey("drivers.id", ondelete="CASCADE"), primary_key=True
    )
    category = Column(
        StrEnum(*LICENSE_CATEGORIES, name="license_category"), primary_key=True
    )

    driver = relationship("Drivers", back_populates="categories")


class DriverRequests(Base):
    __tablename__ = "driver_requests"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    type = Column(
        StrEnum("LICENSE_UPDATE", "MEDICAL_CHECK", name="request_type"), nullable=False
    )
    status = Column(
        StrEnum("PENDING", "APPROVED", "REJECTED", name="request_status"),
        nullable=False,
        default="PENDING",
    )
    new_license_category = Column(
        StrEnum(*LICENSE_CATEGORIES, name="new_license_category"), nullable=True
    )
    new_license_expiry_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    driver = relationship("Drivers", back_populates="requests")


class Vehicles(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("length(vin) = 17", name="ck_vehicles_vin_length"),
        CheckConstraint(f"year >= {MIN_VEHICLE_YEAR}", name="ck_vehicles_year"),
    )

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    vin = Column(String, unique=True, nullable=False, index=True)
    required_license_category = Column(
        StrEnum(*LICENSE_CATEGORIES, name="required_license_category"), nullable=False
    )
    technical_state = Column(String, nullable=False)
    status = Column(
        StrEnum("ACTIVE", "DECOMMISSIONED", name="vehicle_status"),
        nullable=False,
        default="ACTIVE",
    )

    routes = relationship("Routes", back_populates="vehicle", passive_deletes="all")
    fuel_records = relationship(
        "FuelRecords", back_populates="vehicle", passive_deletes="all"
    )
    repair_records = relationship(
        "RepairRecords", back_populates="vehicle", passive_deletes="all"
    )
    insurance_policies = relationship(
        "InsurancePolicies", back_populates="vehicle", passive_deletes="all"
    )


class Routes(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    distance = Column(Float, nullable=False)
    departure_at = Column(DateTime, nullable=False)
    planned_return_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(
        StrEnum(
            "PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="route_status"
        ),
        nullable=False,
        default="PLANNED",
    )

    driver = relationship("Drivers", back_populates="routes")
    vehicle = relationship("Vehicles", back_populates="routes")
    stops = relationship(
        "RouteStops",
        back_populates="route",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RouteStops.order_no",
    )

    @property
    def state(self):
        return RouteState.from_status(self.status)

    def set_state(self, state):
        self.status = state.status()

    def reassign_driver(self, driver):
        self.state.reassign_driver(self, driver)

    def reassign_vehicle(self, vehicle):
        self.state.reassign_vehicle(self, vehicle)

    def reschedule(self, departure_at):
        self.state.reschedule(self, departure_at)

    def edit_stops(self, stops):
        self.state.edit_stops(self, stops)

    def start(self, started_at=None):
        self.state.start(self, started_at)

    def arrive_at_stop(self, stop):
        self.state.arrive_at_stop(self, stop)

    def complete(self, returned_at=None):
        self.state.complete(self, returned_at)

    def cancel(self):
        self.state.cancel(self)

    def delete(self):
        self.state.delete(self)

    def update_planned_return(self):
        try:
            self.planned_return_at = self.departure_at + timedelta(
                hours=self.distance / AVERAGE_SPEED_KMH,
                minutes=MINUTES_PER_STOP * len(self.stops),
            )
        except OverflowError:
            raise RouteActionNotAllowed("The departure time is too far in the future")


class RouteStops(Base):
    __tablename__ = "route_stops"
    __table_args__ = (UniqueConstraint("route_id", "order_no", name="uq_route_stop"),)

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(
        Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    order_no = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    arrived_at = Column(DateTime, nullable=True)

    route = relationship("Routes", back_populates="stops")


class AccountingRecord(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    @declared_attr
    def vehicle_id(cls):
        return Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)


class InsurancePolicies(AccountingRecord):
    __tablename__ = "insurance_policies"

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    vehicle = relationship("Vehicles", back_populates="insurance_policies")


class FuelRecords(AccountingRecord):
    __tablename__ = "fuel_records"

    liters = Column(Float, nullable=False)

    vehicle = relationship("Vehicles", back_populates="fuel_records")


class RepairRecords(AccountingRecord):
    __tablename__ = "repair_records"

    amount = Column(Numeric(10, 2), nullable=True)
    type = Column(
        StrEnum("SERVICE_TO", "INSPECTION", "REPAIR", name="maintenance_type"),
        nullable=False,
    )
    description = Column(String, nullable=False, default="")
    status = Column(
        StrEnum("PLANNED", "DONE", name="maintenance_status"),
        nullable=False,
        default="PLANNED",
    )

    vehicle = relationship("Vehicles", back_populates="repair_records")


class Notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(
        StrEnum(
            "LICENSE_UPDATE_REQUEST",
            "MEDICAL_CHECK_REQUEST",
            "MAINTENANCE_SCHEDULED",
            "MAINTENANCE_DUE",
            "INSURANCE_EXPIRING",
            "LICENSE_EXPIRING",
            "MEDICAL_CHECK_DUE",
            "ROUTE_ASSIGNED",
            "REQUEST_APPROVED",
            "REQUEST_REJECTED",
            name="notification_type",
        ),
        nullable=False,
    )
    text = Column(String, nullable=False)
    related_entity = Column(String, nullable=False)
    related_id = Column(Integer, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class DBModels:
    async def init_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
