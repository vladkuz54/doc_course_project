from sqlalchemy import select

from ..interfaces.base_interfaces import IBaseRepository


class BaseRepository(IBaseRepository):
    def __init__(self, session, model):
        self.session = session
        self.model = model

    async def get_all(self):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def get_by_id(self, id):
        return await self.session.get(self.model, id)

    async def create(self, obj):
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj):
        obj_to_update = await self.session.merge(obj)
        await self.session.commit()
        await self.session.refresh(obj_to_update)
        return obj_to_update

    async def delete(self, id):
        obj_to_delete = await self.get_by_id(id)
        if obj_to_delete is None:
            return None
        await self.session.delete(obj_to_delete)
        await self.session.commit()
        return obj_to_delete

    async def _where(self, *conditions):
        result = await self.session.execute(select(self.model).where(*conditions))
        return result.scalars().all()

    async def _first(self, *conditions):
        result = await self.session.execute(select(self.model).where(*conditions))
        return result.scalars().first()
