from sqlalchemy import select

from ..db_models import Drivers, Users
from ..interfaces.users_interfaces import IUsersRepository
from .base_repository import BaseRepository


class UsersRepository(IUsersRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Users)

    async def get_by_username(self, username):
        return await self._first(self.model.username == username)

    async def get_by_driver(self, driver_id):
        result = await self.session.execute(
            select(self.model)
            .join(Drivers, Drivers.user_id == self.model.id)
            .where(Drivers.id == driver_id)
        )
        return result.scalars().all()
