import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .bll.exceptions import (
    BusinessRuleError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from .dal.route_states import RouteActionNotAllowed
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

app = FastAPI(title="Fleet Management API")

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


@app.exception_handler(BusinessRuleError)
async def business_rule_error_handler(request: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RouteActionNotAllowed)
async def route_action_not_allowed_handler(
    request: Request, exc: RouteActionNotAllowed
):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    if "FOREIGN KEY" in str(exc.orig):
        detail = "Record is used by other records and cannot be deleted or changed"
    else:
        detail = f"Database constraint violated: {exc.orig}"
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
