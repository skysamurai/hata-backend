import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.phone_stat import PhoneStat
from app.models.phone_def import PhoneDef
from app.models.blacklist import Blacklist
from app.models.listing import Listing, ListingSource
from app.models.region import Region
from app.parsers.base import ParsedListing
from app.core.config import settings


class RealtorDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_listing(self, pl: ParsedListing, region_id: int) -> bool:
        """Process a parsed listing through all 5 detection layers.
        Returns True if new listing was created, False if it already existed."""
        return await self._save_listing(pl, region_id)

    async def _save_listing(self, pl: ParsedListing, region_id: int) -> bool:
        from sqlalchemy import func

        # Check if listing already exists
        result = await self.db.execute(
            select(Listing).where(Listing.external_id == pl.external_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.last_seen = func.now()
            existing.is_active = True
            if pl.price:
                existing.price = pl.price
            await self.db.commit()
            return False

        # --- New listing: calculate agent score ---
        agent_score = 0
        phone_hash_val = None

        if pl.phone_formatted:
            phone_hash_val = hashlib.sha256(
                pl.phone_formatted.encode()
            ).hexdigest()

            # === LAYER 2: Frequency Check ===
            result = await self.db.execute(
                select(PhoneStat).where(PhoneStat.phone_hash == phone_hash_val)
            )
            phone_stat = result.scalar_one_or_none()

            if phone_stat:
                count = phone_stat.count_listings
                if count >= 11:
                    agent_score += 90
                elif count >= 4:
                    agent_score += 50
                elif count >= 2:
                    agent_score += 20

                # === LAYER 4: Cross-platform Check ===
                if phone_stat.count_sources >= 2:
                    agent_score += 25

                # Update phone stats
                phone_stat.count_listings += 1
                sources = list(phone_stat.regions or [])
                if pl.source not in sources:
                    sources.append(pl.source)
                phone_stat.count_sources = len(sources)
                phone_stat.regions = sources
                phone_stat.last_seen = func.now()
            else:
                phone_stat = PhoneStat(
                    phone_hash=phone_hash_val,
                    count_listings=1,
                    count_sources=1,
                    regions=[pl.source],
                )
                self.db.add(phone_stat)

            # === LAYER 3: Regional Mismatch Check ===
            # Only meaningful for phones seen first time
            if phone_stat and phone_stat.count_listings == 1:
                mismatch_score = await self._get_regional_mismatch_score(pl, region_id)
                agent_score += mismatch_score

            # === LAYER 5: Blacklist Check ===
            result = await self.db.execute(
                select(Blacklist).where(Blacklist.phone_hash == phone_hash_val)
            )
            if result.scalar_one_or_none():
                agent_score = 100

        # Save the listing
        is_agent = agent_score >= settings.AGENT_SCORE_THRESHOLD

        listing = Listing(
            source=ListingSource(pl.source),
            external_id=pl.external_id,
            url=pl.url,
            title=pl.title,
            price=pl.price,
            address=pl.address,
            metro=pl.metro,
            rooms=pl.rooms,
            area=pl.area,
            floor=pl.floor,
            total_floors=pl.total_floors,
            description=pl.description,
            phone_raw=pl.phone_raw,
            phone_formatted=pl.phone_formatted,
            region_id=region_id,
            is_agent=is_agent,
            agent_score=min(agent_score, 100),
        )
        self.db.add(listing)
        await self.db.commit()
        return True

    async def _get_regional_mismatch_score(self, pl: ParsedListing, region_id: int) -> int:
        """Check if phone DEF region matches listing region.
        Returns -10 (same region = private) or +30 (different region = likely realtor)."""
        if not pl.phone_formatted or len(pl.phone_formatted) < 5:
            return 0

        try:
            phone_num = pl.phone_formatted[2:]  # digits after +7
            def_code = int(pl.phone_formatted[2:5])
            full_num = int(phone_num)

            # Look up in phone_defs
            result = await self.db.execute(
                select(PhoneDef).where(
                    PhoneDef.prefix == def_code,
                    PhoneDef.range_start <= full_num,
                    PhoneDef.range_end >= full_num,
                ).limit(1)
            )
            phone_def = result.scalar_one_or_none()

            if not phone_def:
                return 0

            # Get listing region
            result = await self.db.execute(
                select(Region).where(Region.id == region_id)
            )
            region = result.scalar_one_or_none()

            if not region:
                return 0

            phone_region_lower = phone_def.region.lower()
            listing_region_lower = region.name.lower()

            # Check if regions match (partial or exact)
            if (listing_region_lower in phone_region_lower or
                    phone_region_lower in listing_region_lower):
                return -10  # Same region -> likely private owner
            else:
                return 30  # Different region -> likely realtor/agent
        except (ValueError, IndexError):
            return 0
