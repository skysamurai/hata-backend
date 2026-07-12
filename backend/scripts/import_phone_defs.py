import asyncio
import sys
sys.path.insert(0, '.')
from app.core.db import async_session
from app.models.phone_def import PhoneDef
from sqlalchemy import select

async def import_defs(filepath: str):
    """Parse opss.db format: prefix;rangeStart;rangeEnd;operator;region"""
    async with async_session() as db:
        # Skip if already imported
        result = await db.execute(select(PhoneDef).limit(1))
        if result.scalar_one_or_none():
            print("PhoneDefs already imported, skipping.")
            return

        count = 0
        with open(filepath, "r", encoding="cp1251") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(";")
                if len(parts) == 5:
                    try:
                        prefix, start, end, operator, region = parts
                        db.add(PhoneDef(
                            prefix=int(prefix),
                            range_start=int(start),
                            range_end=int(end),
                            operator=operator,
                            region=region
                        ))
                        count += 1
                        if count % 5000 == 0:
                            await db.flush()
                            print(f"Imported {count} records...")
                    except ValueError:
                        continue  # Skip malformed lines
        await db.commit()
        print(f"Imported {count} phone DEF records in total")

if __name__ == "__main__":
    asyncio.run(import_defs("C:/work/Hata/_extracted/Bin/opss.db"))
