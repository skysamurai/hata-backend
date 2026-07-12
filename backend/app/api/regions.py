from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.models.region import Region

router = APIRouter(prefix="/api/regions", tags=["regions"])

@router.get("")
async def list_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region).order_by(Region.name))
    return result.scalars().all()

@router.get("/{region_id}")
async def get_region(region_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region).where(Region.id == region_id))
    return result.scalar_one_or_none()
