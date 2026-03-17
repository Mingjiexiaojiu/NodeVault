import asyncio
import sys
sys.path.insert(0, ".")
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.core.config import settings
from backend.models.node import Node


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sf() as db:
        total = (await db.execute(select(func.count()).select_from(Node))).scalar()
        public = (await db.execute(
            select(func.count()).select_from(Node).where(Node.visibility == "public")
        )).scalar()
        print(f"Total nodes: {total}")
        print(f"Public nodes: {public}")
        print(f"Private nodes: {total - public}")
    await engine.dispose()


asyncio.run(main())
