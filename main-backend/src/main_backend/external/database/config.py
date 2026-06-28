from sqlalchemy.ext.asyncio import (

    AsyncSession,

    async_sessionmaker,

    create_async_engine,

)

from ...config import settings

engine = create_async_engine(

    settings.db_url,

    echo=settings.DEBUG,

    pool_size=10,

    max_overflow=20,

    pool_pre_ping=True,

)

async_session_factory = async_sessionmaker(

    engine,

    class_=AsyncSession,

    expire_on_commit=False,

)

async def get_session() -> AsyncSession:

    async with async_session_factory() as session:

        yield session
