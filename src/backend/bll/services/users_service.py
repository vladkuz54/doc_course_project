from typing import Literal

import bcrypt
from pydantic import BaseModel

from ...dal.interfaces.users_interfaces import IUsersRepository
from ..exceptions import EntityAlreadyExistsError
from ..interfaces.users_interface import IUsersService
from .base_service import BaseService


class UserData(BaseModel):
    username: str
    password: str
    role: Literal["DRIVER", "ADMIN"]


class UsersService(IUsersService, BaseService):
    entity_name = "User"

    def __init__(self, repository: IUsersRepository):
        super().__init__(repository)

    async def validate(self, data, id=None):
        existing = await self.repository.get_by_username(data.username)
        if existing and existing.id != id:
            raise EntityAlreadyExistsError(f"User {data.username} already exists")

    def to_fields(self, data):
        fields = data.model_dump(exclude={"password"})
        fields["password_hash"] = bcrypt.hashpw(
            data.password.encode(), bcrypt.gensalt()
        ).decode()
        return fields
