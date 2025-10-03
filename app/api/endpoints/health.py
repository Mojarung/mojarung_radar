from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db.redis import get_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Проверка подключения к БД."""
    try:
        await db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/health/redis")
async def health_check_redis():
    """Проверка подключения к Redis."""
    try:
        redis = await get_redis()
        await redis.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}

