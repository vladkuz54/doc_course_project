from typing import Literal

import bcrypt
from pydantic import BaseModel

from ...dal.interfaces.drivers_interfaces import IDriversRepository
from ...dal.interfaces.users_interfaces import IUsersRepository
from ..exceptions import (
    AccountDisabledError,
    BusinessRuleError,
    EntityAlreadyExistsError,
)
from ..interfaces.users_interface import IUsersService
from .base_service import BaseService


class UserData(BaseModel):
    username: str
    password: str
    role: Literal["DRIVER", "ADMIN"]


class UsersService(IUsersService, BaseService):
    entity_name = "Користувача"

    def __init__(
        self, repository: IUsersRepository, drivers_repository: IDriversRepository
    ):
        super().__init__(repository)
        self.drivers_repository = drivers_repository

    async def authenticate(self, username, password):
        user = await self.repository.get_by_username(username)
        if not user or not bcrypt.checkpw(
            password.encode(), user.password_hash.encode()
        ):
            return None
        driver = await self.drivers_repository.get_by_user_id(user.id)
        if driver and driver.employment_status == "DISMISSED":
            raise AccountDisabledError(
                "Ваш обліковий запис водія деактивовано. Зверніться до "
                "адміністратора."
            )
        return user

    async def _validate(self, data, id=None):
        existing = await self.repository.get_by_username(data.username)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(
                f"Ім'я користувача «{data.username}» уже зайняте. Оберіть інше."
            )
        if (
            id is not None
            and data.role != "DRIVER"
            and await self.drivers_repository.get_by_user_id(id)
        ):
            raise BusinessRuleError(
                "Цей обліковий запис має профіль водія, тому його роль має "
                "залишатися «Водій». Щоб змінити роль, спершу видаліть профіль водія."
            )

    def to_fields(self, data):
        fields = data.model_dump(exclude={"password"})
        fields["password_hash"] = bcrypt.hashpw(
            data.password.encode(), bcrypt.gensalt()
        ).decode()
        return fields

    async def get_by_driver(self, driver_id):
        return await self.repository.get_by_driver(driver_id)
