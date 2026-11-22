from .observer import DomainEvent


def _to_driver(driver, type, route, text):
    return DomainEvent(type, "routes", route.id, text, driver.user_id)


def _when(route):
    return f"{route.departure_at:%d.%m.%Y %H:%M}"


CHANGE_TEXT = {
    "vehicle": lambda make: f"транспорт {make}",
    "departure_at": lambda at: f"час виїзду {at:%d.%m.%Y %H:%M}",
    "distance": lambda km: f"відстань {km:g} км",
    "stops": lambda addresses: f"зупинки {' → '.join(addresses)}",
}
ACTION_TEXT = {"restored": "відновлено", "created": "створено"}
MISSING_TEXT = {
    "driver": ("водія", "Призначте водія пізніше."),
    "vehicle": ("транспорту", "Призначте транспорт пізніше."),
}


def warning_text(route, action, missing, reason):
    name, advice = MISSING_TEXT[missing]
    return f"Маршрут №{route.id} {ACTION_TEXT[action]} без {name}. {reason} {advice}"


class RouteEvents:
    @staticmethod
    def assigned(route, driver):
        return _to_driver(
            driver,
            "ROUTE_ASSIGNED",
            route,
            f"Вам було призначено маршрут №{route.id} на {_when(route)}",
        )

    @staticmethod
    def unassigned(route, driver):
        return _to_driver(
            driver,
            "ROUTE_UNASSIGNED",
            route,
            f"Ваш маршрут №{route.id} на {_when(route)} передано іншому водію",
        )

    @staticmethod
    def updated(route, driver, changes):
        return _to_driver(
            driver,
            "ROUTE_UPDATED",
            route,
            f"У вашому маршруті №{route.id} змінено: "
            + "; ".join(CHANGE_TEXT[key](value) for key, value in changes.items()),
        )

    @staticmethod
    def restored(route, driver):
        return _to_driver(
            driver,
            "ROUTE_ASSIGNED",
            route,
            f"Ваш маршрут №{route.id} на {_when(route)} відновлено",
        )

    @staticmethod
    def cancelled(route, driver):
        return _to_driver(
            driver,
            "ROUTE_CANCELLED",
            route,
            f"Ваш маршрут №{route.id} на {_when(route)} скасовано",
        )
