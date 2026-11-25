from sqlalchemy import select, insert

from app.database import async_session_maker


class BaseDAO:
    model = None

    @classmethod
    async def find_all(cls, **filter_by) -> list:
        async with async_session_maker() as session:
            query = (
                select(cls.model.__table__.columns)
                .filter_by(**filter_by)
                .order_by(cls.model.id.desc())
            )
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def add(cls, **values) -> None:
        async with async_session_maker.begin() as session:
            query = insert(cls.model).values(**values)
            await session.execute(query)
