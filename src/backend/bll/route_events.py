from .observer import DomainEvent


def _to_driver(driver, type, route, text):
    return DomainEvent(type, "routes", route.id, text, driver.user_id)


def _when(route):
    return f"{route.departure_at:%d.%m.%Y %H:%M}"


class RouteEvents:
    @staticmethod
    def assigned(route, driver):
        return _to_driver(
            driver,
            "ROUTE_ASSIGNED",
            route,
            f"Вам призначено маршрут №{route.id} на {_when(route)}",
        )

    @staticmethod
    def restored(route, driver):
        return _to_driver(
            driver,
            "ROUTE_ASSIGNED",
            route,
            f"Маршрут №{route.id} на {_when(route)} відновлено",
        )

    @staticmethod
    def unassigned(route, driver):
        return _to_driver(
            driver,
            "ROUTE_UNASSIGNED",
            route,
            f"Маршрут №{route.id} на {_when(route)} передано іншому водію",
        )

    @staticmethod
    def updated(route, driver, changes):
        return _to_driver(
            driver,
            "ROUTE_UPDATED",
            route,
            f"Маршрут №{route.id} змінено: {'; '.join(changes)}",
        )

    @staticmethod
    def cancelled(route, driver):
        return _to_driver(
            driver,
            "ROUTE_CANCELLED",
            route,
            f"Маршрут №{route.id} на {_when(route)} скасовано",
        )

    @staticmethod
    def warning(route, text):
        return DomainEvent("ROUTE_UPDATED", "routes", route.id, text)
