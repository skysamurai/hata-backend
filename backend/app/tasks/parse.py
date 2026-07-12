import asyncio
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.models.region import Region
from app.models.parse_task import ParseTask
from app.core.db import async_session
from sqlalchemy import select

# These will be available after Tasks 5, 6, 7
try:
    from app.parsers.avito import AvitoParser
except ImportError:
    AvitoParser = None
try:
    from app.parsers.cian import CianParser
except ImportError:
    CianParser = None
try:
    from app.filters.detector import RealtorDetector
except ImportError:
    RealtorDetector = None


@celery_app.task
def parse_region_task(region_id: int, source: str):
    """Parse listings for a region from a specific source."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_parse_region(region_id, source))
    finally:
        loop.close()


async def _parse_region(region_id: int, source: str):
    async with async_session() as db:
        # Get region
        result = await db.execute(select(Region).where(Region.id == region_id))
        region = result.scalar_one_or_none()
        if not region:
            return {"error": f"Region {region_id} not found"}

        task = ParseTask(
            region_id=region_id, source=source,
            status="running", started_at=datetime.utcnow()
        )
        db.add(task)
        await db.commit()

        try:
            # Run parser
            if source == "avito":
                if AvitoParser is None:
                    raise ImportError("AvitoParser not yet implemented")
                parser = AvitoParser()
                listings = await parser.parse_region(region_id, region.avito_location_id, None)
            elif source == "cian":
                if CianParser is None:
                    raise ImportError("CianParser not yet implemented")
                parser = CianParser()
                listings = await parser.parse_region(region_id, None, region.cian_region_id)
            else:
                raise ValueError(f"Unknown source: {source}")

            # Run realtor detection
            if RealtorDetector is None:
                raise ImportError("RealtorDetector not yet implemented")
            detector = RealtorDetector(db)
            new_count = 0
            for pl in listings:
                is_new = await detector.process_listing(pl, region_id)
                if is_new:
                    new_count += 1

            task.status = "done"
            task.listings_found = len(listings)
            task.listings_new = new_count
        except Exception as e:
            task.status = "error"
            task.error_log = str(e)
        finally:
            task.finished_at = datetime.utcnow()
            await db.commit()

        return {
            "status": task.status,
            "listings_found": task.listings_found,
            "listings_new": task.listings_new,
        }
