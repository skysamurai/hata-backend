from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.core.db import get_db
from app.models.listing import Listing

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("")
async def list_listings(
    region_id: int | None = None,
    rooms: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    metro: str | None = None,
    source: str | None = None,
    is_agent: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Listing.is_active == True]
    if region_id:
        conditions.append(Listing.region_id == region_id)
    if rooms is not None:
        conditions.append(Listing.rooms == rooms)
    if price_min is not None:
        conditions.append(Listing.price >= price_min)
    if price_max is not None:
        conditions.append(Listing.price <= price_max)
    if metro:
        conditions.append(Listing.metro.ilike(f"%{metro}%"))
    if source:
        conditions.append(Listing.source == source)
    if is_agent is not None:
        conditions.append(Listing.is_agent == is_agent)

    where_clause = and_(*conditions)

    # Get total count
    count_query = select(func.count(Listing.id)).where(where_clause)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get paginated items
    query = (
        select(Listing)
        .where(where_clause)
        .order_by(Listing.last_seen.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    listings = result.scalars().all()

    return {"items": listings, "total": total, "page": page, "per_page": per_page}


@router.get("/{listing_id}")
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        return {"error": "Not found"}
    return listing
