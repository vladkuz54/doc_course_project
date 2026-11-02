from abc import ABC, abstractmethod
from datetime import datetime


class RouteActionNotAllowed(Exception):
    pass


class RouteState(ABC):
    @staticmethod
    def from_status(status):
        return {
            "PLANNED": PlannedState,
            "IN_PROGRESS": InProgressState,
            "COMPLETED": CompletedState,
            "CANCELLED": CancelledState,
        }[status]()

    @abstractmethod
    def status(self):
        pass

    def reassign_driver(self, route, driver):
        self._reject("reassign the driver of")

    def reassign_vehicle(self, route, vehicle):
        self._reject("reassign the vehicle of")

    def reschedule(self, route, departure_at):
        self._reject("reschedule")

    def edit_stops(self, route, stops):
        self._reject("edit the stops of")

    def start(self, route):
        self._reject("start")

    def arrive_at_stop(self, route, stop):
        self._reject("clock a stop of")

    def complete(self, route, returned_at):
        self._reject("complete")

    def cancel(self, route):
        self._reject("cancel")

    def delete(self, route):
        self._reject("delete")

    def _reject(self, action):
        raise RouteActionNotAllowed(f"Cannot {action} a {self.status()} route")


def _ensure_not_in_future(returned_at):
    if returned_at > datetime.now():
        raise RouteActionNotAllowed("Return time cannot be in the future")


class PlannedState(RouteState):
    def status(self):
        return "PLANNED"

    def reassign_driver(self, route, driver):
        route.driver_id = driver.id

    def reassign_vehicle(self, route, vehicle):
        route.vehicle_id = vehicle.id

    def reschedule(self, route, departure_at):
        route.departure_at = departure_at

    def edit_stops(self, route, stops):
        if not stops:
            raise RouteActionNotAllowed("A route must have at least one stop")
        # In place, because SQLAlchemy inserts before it deletes, which would break uq_route_stop
        existing_count = len(route.stops)
        for position, stop in enumerate(stops, 1):
            if position <= existing_count:
                route.stops[position - 1].address = stop.address
            else:
                stop.order_no = position
                route.stops.append(stop)
        del route.stops[len(stops) :]

    def start(self, route):
        self._ensure_assigned(route)
        route.started_at = datetime.now()
        route.set_state(InProgressState())

    def complete(self, route, returned_at):
        if returned_at is None:
            raise RouteActionNotAllowed(
                "A route that was never started needs a return time"
            )
        self._ensure_assigned(route)
        _ensure_not_in_future(returned_at)
        if returned_at < route.departure_at:
            raise RouteActionNotAllowed("Return time cannot be before the departure")
        route.completed_at = returned_at
        route.set_state(CompletedState())

    def cancel(self, route):
        route.set_state(CancelledState())

    def delete(self, route):
        pass

    def _ensure_assigned(self, route):
        if route.driver_id is None or route.vehicle_id is None:
            raise RouteActionNotAllowed("A route needs a driver and a vehicle")


class InProgressState(RouteState):
    def status(self):
        return "IN_PROGRESS"

    def arrive_at_stop(self, route, stop):
        if stop not in route.stops:
            raise RouteActionNotAllowed("The stop belongs to another route")
        if stop.arrived_at is not None:
            raise RouteActionNotAllowed("The stop is already clocked")
        if any(
            s.arrived_at is not None and s.order_no > stop.order_no for s in route.stops
        ):
            raise RouteActionNotAllowed("A later stop is already clocked")
        stop.arrived_at = datetime.now()

    def complete(self, route, returned_at):
        if returned_at is None:
            returned_at = datetime.now()
        else:
            _ensure_not_in_future(returned_at)
            if returned_at < route.started_at:
                raise RouteActionNotAllowed("Return time cannot be before the start")
        route.completed_at = returned_at
        route.set_state(CompletedState())

    def cancel(self, route):
        route.set_state(CancelledState())


class CompletedState(RouteState):
    def status(self):
        return "COMPLETED"


class CancelledState(RouteState):
    def status(self):
        return "CANCELLED"
