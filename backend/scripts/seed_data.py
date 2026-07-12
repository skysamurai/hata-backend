import asyncio
import sys
sys.path.insert(0, '.')
from app.core.db import async_session
from app.models.region import Region

REGIONS = [
    {"name": "Казань", "slug": "kazan", "avito_location_id": 648130, "cian_region_id": 4772},
    {"name": "Москва", "slug": "moscow", "avito_location_id": 637640, "cian_region_id": 1},
    {"name": "Санкт-Петербург", "slug": "spb", "avito_location_id": 653240, "cian_region_id": 2},
    {"name": "Екатеринбург", "slug": "ekb", "avito_location_id": 650370, "cian_region_id": 4741},
    {"name": "Новосибирск", "slug": "nsk", "avito_location_id": 656510, "cian_region_id": 4828},
    {"name": "Нижний Новгород", "slug": "nn", "avito_location_id": 647530, "cian_region_id": 4885},
    {"name": "Краснодар", "slug": "krasnodar", "avito_location_id": 647010, "cian_region_id": 4835},
    {"name": "Сочи", "slug": "sochi", "avito_location_id": 648820, "cian_region_id": 12630},
    {"name": "Уфа", "slug": "ufa", "avito_location_id": 656880, "cian_region_id": 4793},
    {"name": "Самара", "slug": "samara", "avito_location_id": 654650, "cian_region_id": 4859},
]

async def seed():
    async with async_session() as db:
        for r in REGIONS:
            # Check if region already exists
            from sqlalchemy import select
            result = await db.execute(select(Region).where(Region.slug == r["slug"]))
            if not result.scalar_one_or_none():
                db.add(Region(**r))
        await db.commit()
        print(f"Seeded {len(REGIONS)} regions")

if __name__ == "__main__":
    asyncio.run(seed())
