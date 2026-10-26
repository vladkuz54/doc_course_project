from ..db_models import Users
from ..interfaces.users_interfaces import IUsersRepository
from .base_repository import BaseRepository


class UsersRepository(IUsersRepository, BaseRepository):
    def __init__(self, session):
        super().__init__(session, Users)

    async def get_by_username(self, username):
        return await self._first(self.model.username == username)
