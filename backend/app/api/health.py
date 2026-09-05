from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(
    prefix="/api/health",
    tags=["Health"],
)


@router.get("")
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    try:
        await db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "healthy",
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "unhealthy",
        }