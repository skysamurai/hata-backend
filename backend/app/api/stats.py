from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from app.core.db import get_db
from app.models.listing import Listing

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(region_id: int | None = None, db: AsyncSession = Depends(get_db)):
    conditions = [Listing.is_active == True]
    if region_id:
        conditions.append(Listing.region_id == region_id)

    # Total
    total_q = select(func.count(Listing.id)).where(*conditions)
    total = (await db.execute(total_q)).scalar() or 0

    # Agent count
    agent_q = select(func.count(Listing.id)).where(
        Listing.is_agent == True, *conditions
    )
    agent_count = (await db.execute(agent_q)).scalar() or 0

    # Private count
    private_q = select(func.count(Listing.id)).where(
        Listing.is_agent == False, *conditions
    )
    private_count = (await db.execute(private_q)).scalar() or 0

    # New today
    today_q = select(func.count(Listing.id)).where(
        Listing.first_seen >= date.today(), *conditions
    )
    new_today = (await db.execute(today_q)).scalar() or 0

    # Per-source counts
    avito_q = select(func.count(Listing.id)).where(
        Listing.source == "avito", *conditions
    )
    avito_count = (await db.execute(avito_q)).scalar() or 0

    cian_q = select(func.count(Listing.id)).where(
        Listing.source == "cian", *conditions
    )
    cian_count = (await db.execute(cian_q)).scalar() or 0

    return {
        "total": total,
        "agent_count": agent_count,
        "private_count": private_count,
        "new_today": new_today,
        "by_source": {"avito": avito_count, "cian": cian_count},
    }
