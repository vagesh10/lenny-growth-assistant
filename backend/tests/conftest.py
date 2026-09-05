import pytest_asyncio

from app.database import AsyncSessionLocal


@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session