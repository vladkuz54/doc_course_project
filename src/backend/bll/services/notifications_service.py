from typing import Literal

from pydantic import BaseModel

from ...dal.interfaces.notifications_interfaces import INotificationsRepository
from ..interfaces.notifications_interface import INotificationsService
from .base_service import BaseService


class NotificationData(BaseModel):
    type: Literal[
        "LICENSE_UPDATE_REQUEST",
        "MEDICAL_CHECK_REQUEST",
        "MAINTENANCE_SCHEDULED",
        "MAINTENANCE_DUE",
        "INSURANCE_EXPIRING",
        "LICENSE_EXPIRING",
        "MEDICAL_CHECK_DUE",
    ]
    text: str
    related_entity: Literal["drivers", "vehicles", "routes", "driver_requests"]
    related_id: int
    is_read: bool = False


class NotificationsService(INotificationsService, BaseService):
    entity_name = "Notification"

    def __init__(self, repository: INotificationsRepository):
        super().__init__(repository)
