from abc import ABC, abstractmethod
from datetime import datetime


class RouteActionNotAllowed(Exception):
    pass


ROUTE_STATUS_LABELS = {
    "PLANNED": "Заплановано",
    "IN_PROGRESS": "У дорозі",
    "COMPLETED": "Завершено",
    "CANCELLED": "Скасовано",
}


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
        self._reject("змінити водія")

    def reassign_vehicle(self, route, vehicle):
        self._reject("змінити транспорт")

    def reschedule(self, route, departure_at):
        self._reject("перенести")

    def change_distance(self, route, distance):
        self._reject("редагувати")

    def edit_stops(self, route, stops):
        self._reject("змінити зупинки")

    def start(self, route, started_at):
        self._reject("розпочати")

    def arrive_at_stop(self, route, stop):
        self._reject("відмітити прибуття на зупинку")

    def complete(self, route, returned_at):
        self._reject("завершити")

    def cancel(self, route):
        self._reject("скасувати")

    def _reject(self, action):
        raise RouteActionNotAllowed(
            f"Маршрут має статус «{ROUTE_STATUS_LABELS[self.status()]}», "
            f"тому його не можна {action}."
        )


def _ensure_not_in_future(moment, name):
    if moment > datetime.now():
        raise RouteActionNotAllowed(f"{name} не може бути в майбутньому.")


class PlannedState(RouteState):
    def status(self):
        return "PLANNED"

    def reassign_driver(self, route, driver):
        route.driver_id = driver.id

    def reassign_vehicle(self, route, vehicle):
        route.vehicle_id = vehicle.id

    def reschedule(self, route, departure_at):
        route.departure_at = departure_at

    def change_distance(self, route, distance):
        route.distance = distance

    def edit_stops(self, route, stops):
        if not stops:
            raise RouteActionNotAllowed("Маршрут повинен мати хоча б одну зупинку.")
        existing_count = len(route.stops)
        for position, stop in enumerate(stops, 1):
            if position <= existing_count:
                route.stops[position - 1].address = stop.address
            else:
                stop.order_no = position
                route.stops.append(stop)
        del route.stops[len(stops) :]

    def start(self, route, started_at):
        self._ensure_assigned(route)
        if started_at is None:
            started_at = datetime.now()
        else:
            _ensure_not_in_future(started_at, "Час початку")
        route.started_at = started_at
        route.set_state(InProgressState())

    def complete(self, route, returned_at):
        if returned_at is None:
            raise RouteActionNotAllowed(
                "Цей маршрут не було розпочато, тому для завершення вкажіть час повернення."
            )
        self._ensure_assigned(route)
        _ensure_not_in_future(returned_at, "Час повернення")
        if returned_at < route.departure_at:
            raise RouteActionNotAllowed(
                f"Час повернення ({returned_at:%d/%m/%Y %H:%M}) не може бути "
                f"раніше за час виїзду ({route.departure_at:%d/%m/%Y %H:%M})."
            )
        route.completed_at = returned_at
        route.set_state(CompletedState())

    def cancel(self, route):
        route.set_state(CancelledState())

    def _ensure_assigned(self, route):
        if route.driver_id is None or route.vehicle_id is None:
            raise RouteActionNotAllowed("Спершу призначте маршруту водія і транспорт.")


class InProgressState(RouteState):
    def status(self):
        return "IN_PROGRESS"

    def arrive_at_stop(self, route, stop):
        if stop not in route.stops:
            raise RouteActionNotAllowed("Ця зупинка належить іншому маршруту.")
        if stop.arrived_at is not None:
            raise RouteActionNotAllowed("Ви вже відмітили прибуття на цю зупинку.")
        if any(
            s.arrived_at is not None and s.order_no > stop.order_no for s in route.stops
        ):
            raise RouteActionNotAllowed(
                "Ви вже відмітили прибуття на одну з наступних зупинок. "
                "Зупинки відмічаються по черзі."
            )
        stop.arrived_at = datetime.now()

    def complete(self, route, returned_at):
        if returned_at is None:
            returned_at = datetime.now()
        else:
            _ensure_not_in_future(returned_at, "Час повернення")
            if returned_at < route.started_at:
                raise RouteActionNotAllowed(
                    f"Час повернення ({returned_at:%d/%m/%Y %H:%M}) не може бути "
                    f"раніше за час початку ({route.started_at:%d/%m/%Y %H:%M})."
                )
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
