"""将所有种子数据节点改为 public visibility"""
import asyncio
import sys
sys.path.insert(0, ".")
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.core.config import settings
from backend.models.node import Node


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sf() as db:
        result = await db.execute(
            update(Node).values(visibility="public").returning(Node.name)
        )
        names = result.scalars().all()
        await db.commit()
        print(f"Updated {len(names)} nodes to public:")
        for n in names:
            print(f"  - {n}")
    await engine.dispose()


asyncio.run(main())
