import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .bll.exceptions import (
    AccountDisabledError,
    BusinessRuleError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from .dal.route_states import RouteActionNotAllowed
from .presentation.dependencies import run_deadline_checks
from .presentation.routers.auth import router as auth_router
from .presentation.routers.driver_requests_router import (
    router as driver_requests_router,
)
from .presentation.routers.drivers_router import router as drivers_router
from .presentation.routers.fuel_records_router import router as fuel_records_router
from .presentation.routers.insurance_policies_router import (
    router as insurance_policies_router,
)
from .presentation.routers.notifications_router import router as notifications_router
from .presentation.routers.repair_records_router import router as repair_records_router
from .presentation.routers.reports_router import router as reports_router
from .presentation.routers.route_stops_router import router as route_stops_router
from .presentation.routers.routes_router import router as routes_router
from .presentation.routers.users_router import router as users_router
from .presentation.routers.vehicles_router import router as vehicles_router

DEADLINE_CHECK_INTERVAL_SECONDS = 3600
logger = logging.getLogger(__name__)


async def check_deadlines_every_hour():
    while True:
        try:
            await run_deadline_checks()
        except Exception:
            logger.exception("Scheduled deadline check failed")
        await asyncio.sleep(DEADLINE_CHECK_INTERVAL_SECONDS)


class RunDeadlineChecksAfterChanges:
    skipped_paths = ("/notifications", "/auth")

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope["method"] in ("GET", "HEAD", "OPTIONS")
            or scope["path"].startswith(self.skipped_paths)
        ):
            await self.app(scope, receive, send)
            return
        status = {}

        async def remember_status(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        await self.app(scope, receive, remember_status)
        if status.get("code", 500) < 400:
            try:
                await run_deadline_checks()
            except Exception:
                logger.exception("Deadline check after a change failed")


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(check_deadlines_every_hour())
    yield
    task.cancel()


app = FastAPI(title="Fleet Management API", lifespan=lifespan)

app.add_middleware(RunDeadlineChecksAfterChanges)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(EntityAlreadyExistsError)
async def entity_already_exists_handler(
    request: Request, exc: EntityAlreadyExistsError
):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(AccountDisabledError)
async def account_disabled_handler(request: Request, exc: AccountDisabledError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(BusinessRuleError)
async def business_rule_error_handler(request: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RouteActionNotAllowed)
async def route_action_not_allowed_handler(
    request: Request, exc: RouteActionNotAllowed
):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


FIELD_LABELS = {
    "username": "Ім'я користувача",
    "password": "Пароль",
    "make": "Марка",
    "year": "Рік",
    "vin": "VIN",
    "required_license_category": "Потрібна категорія",
    "full_name": "ПІБ",
    "license_categories": "Категорії посвідчення",
    "experience_years": "Стаж",
    "license_expiry_date": "Посвідчення дійсне до",
    "medical_check_date": "Дата медогляду",
    "medical_valid_until": "Медогляд дійсний до",
    "valid_until": "Дійсний до",
    "new_license_category": "Категорія",
    "new_license_expiry_date": "Новий термін дії посвідчення",
    "distance": "Відстань",
    "departure_at": "Час виїзду",
    "started_at": "Час початку",
    "returned_at": "Час повернення",
    "stops": "Зупинки",
    "date": "Дата",
    "amount": "Сума",
    "cost": "Вартість",
    "liters": "Літри",
    "start_date": "Початок покриття",
    "end_date": "Кінець покриття",
    "period_from": "Дата з",
    "period_to": "Дата по",
}


def _validation_message(error):
    fields = [part for part in error["loc"] if isinstance(part, str)]
    field = fields[-1] if fields else ""
    kind, ctx = error["type"], error.get("ctx", {})
    if kind == "missing":
        text = "обов'язкове поле"
    elif kind == "greater_than":
        text = f"має бути більше {ctx['gt']}"
    elif kind == "greater_than_equal":
        text = f"має бути не менше {ctx['ge']}"
    elif kind == "less_than":
        text = f"має бути менше {ctx['lt']}"
    elif kind == "less_than_equal":
        text = f"має бути не більше {ctx['le']}"
    elif kind == "string_pattern_mismatch" and field == "vin":
        text = "має містити 17 символів: великі латинські літери (крім I, O, Q) і цифри"
    elif kind == "string_too_short":
        text = "не може бути порожнім"
    elif kind == "too_short":
        text = "оберіть хоча б одне значення"
    elif kind == "literal_error":
        text = f"оберіть одне зі значень: {ctx['expected'].replace(' or ', ' або ')}"
    elif kind == "value_error":
        text = str(ctx["error"])
    elif kind == "timezone_aware":
        text = "вкажіть час без часового поясу"
    elif kind.startswith(("date", "datetime")):
        text = "вкажіть правильну дату"
    elif kind.startswith(("int", "float", "decimal", "finite")):
        text = "має бути числом"
    else:
        text = "неправильне значення"
    label = FIELD_LABELS.get(field)
    return f"{label}: {text}" if label else text.capitalize()


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    detail = "; ".join(dict.fromkeys(map(_validation_message, exc.errors())))
    return JSONResponse(status_code=422, content={"detail": detail + "."})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    if "FOREIGN KEY" in str(exc.orig):
        detail = (
            "Цей запис пов'язаний з іншими даними, тому його не можна "
            "видалити чи змінити."
        )
    else:
        detail = (
            "Такий запис уже існує або суперечить іншим даним. "
            "Перевірте введені значення."
        )
    return JSONResponse(status_code=409, content={"detail": detail})


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(drivers_router)
app.include_router(driver_requests_router)
app.include_router(vehicles_router)
app.include_router(routes_router)
app.include_router(route_stops_router)
app.include_router(fuel_records_router)
app.include_router(repair_records_router)
app.include_router(insurance_policies_router)
app.include_router(notifications_router)
app.include_router(reports_router)
