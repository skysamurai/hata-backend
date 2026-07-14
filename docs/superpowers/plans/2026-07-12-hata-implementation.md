# Hata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Веб-приложение для парсинга аренды квартир с Avito/Cian (Казань) с 5-слойным детектором риэлторов.

**Architecture:** FastAPI backend + React TS frontend + PostgreSQL + Redis/Celery для фонового парсинга. Парсеры на Playwright. Docker Compose в финале.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Celery, Playwright, React 18, TypeScript, Tailwind CSS, PostgreSQL 16, Redis, Docker

---

## Фаза 1: Фундамент

### Task 1: Структура проекта и конфигурация

**Files:**
- Create: `backend/requirements.txt`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/app/core/db.py`

- [ ] **Step 1: Инициализируем проектную структуру**

```bash
mkdir -p backend/app/{api,parsers,filters,models,tasks,core}
mkdir -p frontend/src/{pages,components,api,hooks}
touch backend/app/__init__.py backend/app/main.py
touch backend/app/core/__init__.py backend/app/core/config.py backend/app/core/db.py
```

- [ ] **Step 2: Пишем backend/requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
alembic==1.13.2
pydantic-settings==2.5.2
celery[redis]==5.4.0
redis==5.1.1
playwright==1.47.0
httpx==0.27.2
beautifulsoup4==4.12.3
python-dotenv==1.0.1
```

- [ ] **Step 3: Пишем backend/app/core/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://hata:hata@localhost:5432/hata"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    PARSER_INTERVAL_MINUTES: int = 5
    AGENT_SCORE_THRESHOLD: int = 60
    AVITO_API_KEY: str = ""
    FIRST_REGION: str = "kazan"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: Пишем backend/app/core/db.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 5: Пишем базовый backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hata", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Устанавливаем зависимости и проверяем запуск**

```bash
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: project structure, config, db connection, health endpoint"
```

### Task 2: Модели базы данных и миграции

**Files:**
- Create: `backend/app/models/__init__.py`, `backend/app/models/base.py`, `backend/app/models/region.py`, `backend/app/models/phone_def.py`, `backend/app/models/listing.py`, `backend/app/models/phone_stat.py`, `backend/app/models/blacklist.py`, `backend/app/models/parse_task.py`
- Create: `backend/alembic.ini`, `backend/alembic/` (alembic init)

- [ ] **Step 1: Базовая модель с общими полями**

```python
# backend/app/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Модель регионов**

```python
# backend/app/models/region.py
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Region(Base, TimestampMixin):
    __tablename__ = "regions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    avito_location_id: Mapped[int | None] = mapped_column(Integer)
    cian_region_id: Mapped[int | None] = mapped_column(Integer)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"))
    parent: Mapped["Region | None"] = relationship(remote_side=[id])
```

- [ ] **Step 3: Модель DEF-кодов телефонов**

```python
# backend/app/models/phone_def.py
from sqlalchemy import String, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class PhoneDef(Base):
    __tablename__ = "phone_defs"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[int] = mapped_column(Integer, index=True)
    range_start: Mapped[int] = mapped_column(BigInteger)
    range_end: Mapped[int] = mapped_column(BigInteger)
    operator: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(200), index=True)
```

- [ ] **Step 4: Модель объявлений**

```python
# backend/app/models/listing.py
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from app.models.base import Base, TimestampMixin

class ListingSource(str, enum.Enum):
    AVITO = "avito"
    CIAN = "cian"

class Listing(Base, TimestampMixin):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[ListingSource] = mapped_column(Enum(ListingSource), index=True)
    external_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[int | None] = mapped_column(Integer)
    address: Mapped[str | None] = mapped_column(String(500))
    metro: Mapped[str | None] = mapped_column(String(100))
    rooms: Mapped[int | None] = mapped_column(Integer)
    area: Mapped[float | None] = mapped_column(Float)
    floor: Mapped[int | None] = mapped_column(Integer)
    total_floors: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    phone_raw: Mapped[str | None] = mapped_column(String(100))
    phone_formatted: Mapped[str | None] = mapped_column(String(20), index=True)
    phone_region: Mapped[str | None] = mapped_column(String(100))
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"), index=True)
    is_agent: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    agent_score: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
```

- [ ] **Step 5: Модели phone_stats, blacklist, parse_task**

```python
# backend/app/models/phone_stat.py
from sqlalchemy import String, Integer, ARRAY, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base

class PhoneStat(Base):
    __tablename__ = "phone_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    count_listings: Mapped[int] = mapped_column(Integer, default=1)
    count_sources: Mapped[int] = mapped_column(Integer, default=1)
    regions: Mapped[list | None] = mapped_column(ARRAY(String))
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_agent_manual: Mapped[bool] = mapped_column(Boolean, default=False)

# backend/app/models/blacklist.py
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base

class Blacklist(Base):
    __tablename__ = "blacklist"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    comment: Mapped[str | None] = mapped_column(String(500))
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

# backend/app/models/parse_task.py
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base

class ParseTask(Base):
    __tablename__ = "parse_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"))
    source: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, done, error
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    listings_found: Mapped[int] = mapped_column(Integer, default=0)
    listings_new: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str | None] = mapped_column(Text)
```

- [ ] **Step 6: Инициализируем Alembic и создаём миграцию**

```bash
cd backend && alembic init alembic
# Настроить alembic.ini на DATABASE_URL и alembic/env.py на Base.metadata
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/alembic/
git commit -m "feat: database models and migrations"
```

### Task 3: Справочники — регионы и DEF-коды

**Files:**
- Create: `backend/app/api/regions.py`
- Create: `backend/scripts/seed_data.py`
- Create: `backend/scripts/import_phone_defs.py`

- [ ] **Step 1: API регионов**

```python
# backend/app/api/regions.py
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
```

- [ ] **Step 2: Скрипт для заполнения регионов (Казань + остальные)**

```python
# backend/scripts/seed_data.py
import asyncio
from app.core.db import async_session, engine
from app.models.base import Base
from app.models.region import Region

REGIONS = [
    {"name": "Казань", "slug": "kazan", "avito_location_id": 648130, "cian_region_id": 4772},
    {"name": "Москва", "slug": "moscow", "avito_location_id": 637640, "cian_region_id": 1},
    {"name": "Санкт-Петербург", "slug": "spb", "avito_location_id": 653240, "cian_region_id": 2},
    # Добавить остальные регионы по мере необходимости
]

async def seed():
    async with async_session() as db:
        for r in REGIONS:
            region = Region(**r)
            db.add(region)
        await db.commit()
        print(f"Seeded {len(REGIONS)} regions")

if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 3: Импорт DEF-кодов из opss.db оригинала**

```python
# backend/scripts/import_phone_defs.py
import asyncio
from app.core.db import async_session
from app.models.phone_def import PhoneDef

async def import_defs(filepath: str):
    """Parse opss.db format: prefix;rangeStart;rangeEnd;operator;region"""
    async with async_session() as db:
        count = 0
        with open(filepath, "r", encoding="cp1251") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) == 5:
                    prefix, start, end, operator, region = parts
                    db.add(PhoneDef(
                        prefix=int(prefix), range_start=int(start),
                        range_end=int(end), operator=operator, region=region
                    ))
                    count += 1
                    if count % 1000 == 0:
                        await db.flush()
        await db.commit()
        print(f"Imported {count} phone DEF records")

if __name__ == "__main__":
    asyncio.run(import_defs("C:/work/Hata/_extracted/Bin/opss.db"))
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/regions.py backend/scripts/
git commit -m "feat: regions API, seed data, phone DEF import"
```

---

## Фаза 2: Парсеры

### Task 4: Базовый класс парсера и инфраструктура

**Files:**
- Create: `backend/app/parsers/__init__.py`, `backend/app/parsers/base.py`
- Create: `backend/app/tasks/__init__.py`, `backend/app/tasks/parse.py`
- Create: `backend/app/tasks/celery_app.py`

- [ ] **Step 1: Конфигурация Celery**

```python
# backend/app/tasks/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery("hata", broker=settings.CELERY_BROKER_URL)
celery_app.conf.update(
    task_serializer="json", accept_content=["json"],
    result_serializer="json", timezone="Europe/Moscow",
    enable_utc=True, beat_schedule={}
)
```

- [ ] **Step 2: Базовый класс парсера**

```python
# backend/app/parsers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ParsedListing:
    external_id: str
    url: str
    title: str
    price: int | None
    address: str | None
    metro: str | None
    rooms: int | None
    area: float | None
    floor: int | None
    total_floors: int | None
    description: str | None
    phone_raw: str | None
    phone_formatted: str | None
    source: str

class BaseParser(ABC):
    source: str = ""

    @abstractmethod
    async def parse_region(self, region_id: int, avito_location_id: int | None,
                           cian_region_id: int | None) -> list[ParsedListing]:
        """Parse listings for a specific region. Returns list of parsed listings."""
        ...

    def format_phone(self, raw: str) -> str | None:
        """Normalize phone to +7XXXXXXXXXX format."""
        import re
        digits = re.sub(r'\D', '', raw)
        if len(digits) == 11 and digits[0] == '8':
            digits = '7' + digits[1:]
        elif len(digits) == 10:
            digits = '7' + digits
        elif len(digits) == 11 and digits[0] == '7':
            pass
        else:
            return None
        return '+' + digits

    def extract_phone_def(self, phone_formatted: str) -> tuple[int, int]:
        """Extract DEF code (first 3 digits after +7)."""
        if phone_formatted and len(phone_formatted) >= 5:
            return int(phone_formatted[2:5]), int(phone_formatted[2:])
        return 0, 0
```

- [ ] **Step 3: Celery задача парсинга**

```python
# backend/app/tasks/parse.py
from app.tasks.celery_app import celery_app
from app.parsers.avito import AvitoParser
from app.parsers.cian import CianParser
from app.filters.detector import RealtorDetector
from app.models.region import Region
from app.models.listing import Listing, ListingSource
from app.models.parse_task import ParseTask
from app.core.db import async_session
from sqlalchemy import select
from datetime import datetime

@celery_app.task
def parse_region_task(region_id: int, source: str):
    """Parse listings for a region from a specific source."""
    return asyncio.run(_parse_region(region_id, source))

async def _parse_region(region_id: int, source: str):
    async with async_session() as db:
        # Get region
        region = (await db.execute(select(Region).where(Region.id == region_id))).scalar_one()
        task = ParseTask(region_id=region_id, source=source, status="running", started_at=datetime.utcnow())
        db.add(task)
        await db.commit()

        try:
            # Run parser
            if source == "avito":
                parser = AvitoParser()
                listings = await parser.parse_region(region_id, region.avito_location_id, None)
            elif source == "cian":
                parser = CianParser()
                listings = await parser.parse_region(region_id, None, region.cian_region_id)
            else:
                raise ValueError(f"Unknown source: {source}")

            # Run realtor detection
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

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(300.0, parse_region_task.s(1, "avito"), name="parse-kazan-avito")
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/parsers/ backend/app/tasks/
git commit -m "feat: base parser class, celery tasks for parsing"
```

### Task 5: Avito парсер

**Files:**
- Create: `backend/app/parsers/avito.py`

- [ ] **Step 1: Avito парсер через API**

```python
# backend/app/parsers/avito.py
import httpx
from app.parsers.base import BaseParser, ParsedListing
from app.core.config import settings

class AvitoParser(BaseParser):
    source = "avito"
    API_URL = "https://m.avito.ru/api/11/items"
    API_KEY = "af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir"

    async def parse_region(self, region_id: int, avito_location_id: int | None,
                           cian_region_id: int | None) -> list[ParsedListing]:
        listings = []
        if not avito_location_id:
            return listings

        categories = [
            (24, 1060, 5256),  # Квартиры, сдам, на длительный срок
            (23, 1055, 6203),  # Комнаты, сдам, на длительный срок
        ]

        async with httpx.AsyncClient(timeout=30) as client:
            for category_id, param_201, param_504 in categories:
                for page in range(1, 11):  # 10 pages max
                    params = {
                        "key": self.API_KEY,
                        "sort": "date",
                        "locationId": avito_location_id,
                        "categoryId": category_id,
                        f"params[201]": param_201,
                        f"params[504]": param_504,
                        "privateOnly": 1,
                        "page": page,
                        "lastStamp": 0,
                        "display": "list",
                        "limit": 50,
                    }
                    try:
                        resp = await client.get(self.API_URL, params=params)
                        data = resp.json()
                        items = data.get("items", [])
                        if not items:
                            break
                        for item in items:
                            listing = self._parse_item(item, avito_location_id)
                            if listing:
                                listings.append(listing)
                    except Exception as e:
                        print(f"Avito API error page {page}: {e}")
                        break
        return listings

    def _parse_item(self, item: dict, location_id: int) -> ParsedListing | None:
        try:
            external_id = str(item.get("id", ""))
            title = item.get("title", "")
            price_str = item.get("price", "0")
            price = int(''.join(filter(str.isdigit, str(price_str)))) if price_str else None
            address = item.get("address", "")
            metro_list = item.get("metro", [])
            metro = metro_list[0].get("name", "") if metro_list else None
            description = item.get("description", "")

            # Extract phone from description
            phone_raw = self._extract_phone(description)
            phone_formatted = self.format_phone(phone_raw) if phone_raw else None

            # Extract params from item
            params = {p.get("nameSlug", ""): p.get("text", "") for p in item.get("params", [])}

            rooms = int(params.get("number_of_rooms", "0") or "0") or None
            area = float(params.get("area", "0") or "0") or None
            floor_str = params.get("floor", "")
            floor_parts = floor_str.split(" из ") if floor_str else []
            floor = int(floor_parts[0]) if len(floor_parts) > 0 and floor_parts[0].isdigit() else None
            total_floors = int(floor_parts[1]) if len(floor_parts) > 1 and floor_parts[1].isdigit() else None

            return ParsedListing(
                external_id=external_id,
                url=f"https://www.avito.ru/items/{external_id}",
                title=title, price=price, address=address, metro=metro,
                rooms=rooms, area=area, floor=floor, total_floors=total_floors,
                description=description, phone_raw=phone_raw,
                phone_formatted=phone_formatted, source="avito"
            )
        except Exception as e:
            print(f"Error parsing Avito item: {e}")
            return None

    def _extract_phone(self, text: str) -> str | None:
        import re
        patterns = [
            r'(\+7[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
            r'(8[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
            r'(\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(1)
        return None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/parsers/avito.py
git commit -m "feat: Avito parser via mobile API"
```

### Task 6: Cian парсер

**Files:**
- Create: `backend/app/parsers/cian.py`

- [ ] **Step 1: Cian парсер через Playwright**

```python
# backend/app/parsers/cian.py
from playwright.async_api import async_playwright
from app.parsers.base import BaseParser, ParsedListing
import re
import json

class CianParser(BaseParser):
    source = "cian"
    BASE_URL = "https://kazan.cian.ru/cat.php"

    async def parse_region(self, region_id: int, avito_location_id: int | None,
                           cian_region_id: int | None) -> list[ParsedListing]:
        listings = []
        if not cian_region_id:
            return listings

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to search
            url = f"{self.BASE_URL}?deal_type=rent&engine_version=2&offer_type=flat&region={cian_region_id}&type=3"
            await page.goto(url, wait_until="networkidle")

            for page_num in range(1, 21):  # 20 pages max
                try:
                    # Wait for cards
                    await page.wait_for_selector("article[data-name='CardComponent']", timeout=10000)

                    # Extract data from page
                    cards = await page.query_selector_all("article[data-name='CardComponent']")
                    for card in cards:
                        listing = await self._parse_card(card, cian_region_id)
                        if listing:
                            listings.append(listing)

                    # Next page
                    next_btn = await page.query_selector("a[data-name='Pagination']:last-child")
                    if next_btn:
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                    else:
                        break
                except Exception as e:
                    print(f"Cian error page {page_num}: {e}")
                    break

            await browser.close()
        return listings

    async def _parse_card(self, card, region_id: int) -> ParsedListing | None:
        try:
            # Get Cian ID from link
            link = await card.query_selector("a[data-name='LinkArea']")
            href = await link.get_attribute("href") if link else ""
            external_id = re.search(r'/flat/(\d+)', href or "")
            if not external_id:
                return None

            external_id = external_id.group(1)

            # Title
            title_el = await card.query_selector("[data-name='Title']")
            title = await title_el.inner_text() if title_el else ""

            # Price
            price_el = await card.query_selector("[data-name='Price'] span")
            price_text = await price_el.inner_text() if price_el else "0"
            price = int(re.sub(r'\D', '', price_text)) if price_text else None

            # Address
            addr_el = await card.query_selector("[data-name='Address']")
            address = await addr_el.inner_text() if addr_el else None

            # Metro
            metro_el = await card.query_selector("[data-name='Metro']")
            metro = await metro_el.inner_text() if metro_el else None

            # Description
            desc_el = await card.query_selector("[data-name='Description']")
            description = await desc_el.inner_text() if desc_el else None

            # Phone extraction
            phone_raw = self._extract_phone(description) if description else None
            phone_formatted = self.format_phone(phone_raw) if phone_raw else None

            return ParsedListing(
                external_id=external_id,
                url=f"https://kazan.cian.ru/rent/flat/{external_id}",
                title=title, price=price, address=address, metro=metro,
                rooms=None, area=None, floor=None, total_floors=None,
                description=description, phone_raw=phone_raw,
                phone_formatted=phone_formatted, source="cian"
            )
        except Exception as e:
            print(f"Error parsing Cian card: {e}")
            return None

    def _extract_phone(self, text: str) -> str | None:
        patterns = [
            r'(\+7[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
            r'(8[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(1)
        return None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/parsers/cian.py
git commit -m "feat: Cian parser via Playwright"
```

---

## Фаза 3: Детектор риэлторов

### Task 7: 5-слойный детектор риэлторов

**Files:**
- Create: `backend/app/filters/__init__.py`, `backend/app/filters/detector.py`

- [ ] **Step 1: Все 5 слоёв детектора**

```python
# backend/app/filters/detector.py
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.phone_stat import PhoneStat
from app.models.phone_def import PhoneDef
from app.models.blacklist import Blacklist
from app.models.listing import Listing, ListingSource
from app.parsers.base import ParsedListing
from app.core.config import settings

class RealtorDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_listing(self, pl: ParsedListing, region_id: int) -> bool:
        """Process a parsed listing through all 5 layers.
        Returns True if new listing was created, False if skipped/updated."""
        return await self._save_listing(pl, region_id)

    async def _save_listing(self, pl: ParsedListing, region_id: int) -> bool:
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

        # New listing — calculate agent score
        agent_score = 0
        phone_hash_val = None

        if pl.phone_formatted:
            phone_hash_val = hashlib.sha256(pl.phone_formatted.encode()).hexdigest()

            # Layer 2: Frequency check
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
                # count == 1 → 0 (private person)

                # Layer 4: Cross-platform
                if phone_stat.count_sources >= 2:
                    agent_score += 25

                # Update phone stats
                phone_stat.count_listings += 1
                if pl.source not in (phone_stat.regions or []):
                    phone_stat.count_sources += 1
                phone_stat.last_seen = func.now()
            else:
                # First sighting — create new phone stat
                phone_stat = PhoneStat(
                    phone_hash=phone_hash_val,
                    count_listings=1,
                    count_sources=1,
                    regions=[pl.source],
                )
                self.db.add(phone_stat)

            # Layer 3: Regional mismatch
            if phone_stat and phone_stat.count_listings == 1:
                def_code, _ = pl.phone_def if hasattr(pl, 'phone_def') else (0, 0)
                if not def_code:
                    def_code = int(pl.phone_formatted[2:5]) if len(pl.phone_formatted) >= 5 else 0

                # Look up DEF code region
                result = await self.db.execute(
                    select(PhoneDef).where(
                        PhoneDef.prefix == def_code,
                        PhoneDef.range_start <= int(pl.phone_formatted[2:]),
                        PhoneDef.range_end >= int(pl.phone_formatted[2:])
                    ).limit(1)
                )
                phone_def = result.scalar_one_or_none()

                if phone_def:
                    # Compare DEF region with listing region
                    from app.models.region import Region
                    region_result = await self.db.execute(
                        select(Region).where(Region.id == region_id)
                    )
                    region = region_result.scalar_one_or_none()

                    if region and phone_def.region.lower() != region.name.lower():
                        agent_score += 30
                    else:
                        agent_score -= 10  # Same region — likely private

            # Layer 5: Blacklist check
            result = await self.db.execute(
                select(Blacklist).where(Blacklist.phone_hash == phone_hash_val)
            )
            if result.scalar_one_or_none():
                agent_score = 100

        # Save listing
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
            agent_score=agent_score,
        )
        self.db.add(listing)
        await self.db.commit()
        return True
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/filters/
git commit -m "feat: 5-layer realtor detection algorithm"
```

---

## Фаза 4: API

### Task 8: Listings API и поиск

**Files:**
- Create: `backend/app/api/listings.py`
- Create: `backend/app/api/parser.py` (parser control endpoints)
- Create: `backend/app/api/stats.py`

- [ ] **Step 1: Listings API с фильтрацией**

```python
# backend/app/api/listings.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
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

    query = select(Listing).where(and_(*conditions)).order_by(Listing.last_seen.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    listings = result.scalars().all()

    # Count total
    count_query = select(func.count(Listing.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {"items": listings, "total": total, "page": page, "per_page": per_page}

@router.get("/{listing_id}")
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    return result.scalar_one_or_none()
```

- [ ] **Step 2: Parser control API**

```python
# backend/app/api/parser.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.tasks.parse import parse_region_task
from app.models.parse_task import ParseTask

router = APIRouter(prefix="/api/parse", tags=["parser"])

@router.post("/start")
async def start_parse(region_id: int, source: str = "avito", db: AsyncSession = Depends(get_db)):
    task = parse_region_task.delay(region_id, source)
    return {"task_id": task.id}

@router.get("/status/{task_id}")
async def parse_status(task_id: str, db: AsyncSession = Depends(get_db)):
    result = parse_region_task.AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status, "result": result.result}

@router.get("/history")
async def parse_history(region_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(ParseTask).order_by(ParseTask.started_at.desc()).limit(50)
    if region_id:
        query = query.where(ParseTask.region_id == region_id)
    result = await db.execute(query)
    return result.scalars().all()
```

- [ ] **Step 3: Stats API**

```python
# backend/app/api/stats.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.models.listing import Listing

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
async def get_stats(region_id: int | None = None, db: AsyncSession = Depends(get_db)):
    conditions = [Listing.is_active == True]
    if region_id:
        conditions.append(Listing.region_id == region_id)

    # Total listings
    total_q = select(func.count(Listing.id)).where(*conditions)
    total = (await db.execute(total_q)).scalar()

    # Agent count
    agent_q = select(func.count(Listing.id)).where(Listing.is_agent == True, *conditions)
    agent_count = (await db.execute(agent_q)).scalar()

    # Private count
    private_q = select(func.count(Listing.id)).where(Listing.is_agent == False, *conditions)
    private_count = (await db.execute(private_q)).scalar()

    # New today
    from datetime import date
    today_q = select(func.count(Listing.id)).where(
        Listing.first_seen >= date.today(), *conditions
    )
    new_today = (await db.execute(today_q)).scalar()

    return {
        "total": total, "agent_count": agent_count,
        "private_count": private_count, "new_today": new_today
    }
```

- [ ] **Step 4: Register all routers in main.py and commit**

```bash
git add backend/app/api/
git commit -m "feat: listings API, parser control, stats endpoints"
```

---

## Фаза 5: Фронтенд

### Task 9: React фронтенд — каркас и страница объявлений

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.js`, `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx`
- Create: `frontend/src/pages/Listings.tsx`
- Create: `frontend/src/components/ListingCard.tsx`, `frontend/src/components/FilterBar.tsx`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Инициализация React проекта с Vite**

```bash
cd frontend && npm create vite@latest . -- --template react-ts
npm install tailwindcss @tailwindcss/vite axios
```

- [ ] **Step 2: API клиент**

```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000' });

export interface Listing {
  id: number; source: 'avito' | 'cian'; title: string;
  price: number | null; address: string | null; metro: string | null;
  rooms: number | null; area: number | null; floor: number | null;
  phone_formatted: string | null; is_agent: boolean; agent_score: number;
  first_seen: string; url: string; description: string | null;
}

export interface Region {
  id: number; name: string; slug: string;
}

export const fetchListings = (params: Record<string, any>) =>
  api.get<{items: Listing[], total: number}>('/api/listings', { params });

export const fetchRegions = () =>
  api.get<Region[]>('/api/regions');

export const fetchStats = (regionId?: number) =>
  api.get('/api/stats', { params: { region_id: regionId } });

export const startParse = (regionId: number, source: string) =>
  api.post('/api/parse/start', null, { params: { region_id: regionId, source } });
```

- [ ] **Step 3: Карточка объявления**

```tsx
// frontend/src/components/ListingCard.tsx
import { Listing } from '../api/client';

export function ListingCard({ listing }: { listing: Listing }) {
  return (
    <div className={`border rounded-lg p-4 mb-3 hover:shadow-md transition ${
      listing.is_agent ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'
    }`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold px-2 py-1 rounded ${
              listing.is_agent ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
            }`}>
              {listing.is_agent ? 'РИЭЛТОР' : 'ЧАСТНИК'} ({listing.agent_score}%)
            </span>
            <span className="text-xs bg-gray-200 px-2 py-1 rounded">
              {listing.source.toUpperCase()}
            </span>
          </div>
          <h3 className="font-semibold text-lg">
            <a href={listing.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
              {listing.title}
            </a>
          </h3>
          <div className="text-2xl font-bold text-blue-600 my-2">
            {listing.price?.toLocaleString()} ₽/мес
          </div>
          <div className="text-gray-600 text-sm space-y-1">
            {listing.address && <div>📍 {listing.address}</div>}
            {listing.metro && <div>🚇 {listing.metro}</div>}
            {listing.rooms && <span className="mr-3">🛏 {listing.rooms}-комн.</span>}
            {listing.area && <span className="mr-3">📐 {listing.area} м²</span>}
            {listing.floor && <span>🏗 {listing.floor} этаж</span>}
          </div>
          {listing.description && (
            <p className="text-gray-500 text-sm mt-2 line-clamp-2">{listing.description}</p>
          )}
        </div>
        <div className="text-right text-xs text-gray-400">
          {new Date(listing.first_seen).toLocaleDateString('ru-RU')}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Страница объявлений с фильтрами**

```tsx
// frontend/src/pages/Listings.tsx
import { useEffect, useState } from 'react';
import { fetchListings, fetchRegions, fetchStats, startParse, Listing, Region } from '../api/client';
import { ListingCard } from '../components/ListingCard';

export function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<number | null>(null);
  const [filterAgent, setFilterAgent] = useState<'all' | 'private' | 'agent'>('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchRegions().then(r => setRegions(r.data)); }, []);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, any> = {};
    if (selectedRegion) params.region_id = selectedRegion;
    if (filterAgent === 'private') params.is_agent = false;
    if (filterAgent === 'agent') params.is_agent = true;
    fetchListings(params).then(r => { setListings(r.data.items); setLoading(false); });
  }, [selectedRegion, filterAgent]);

  const handleParse = (source: string) => {
    if (selectedRegion) { startParse(selectedRegion, source); alert(`Парсинг ${source} запущен`); }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">🏠 Hata — Аренда квартир</h1>
        <div className="flex gap-4 mt-4 flex-wrap">
          <select className="border rounded px-3 py-2" value={selectedRegion || ''}
            onChange={e => setSelectedRegion(Number(e.target.value) || null)}>
            <option value="">Все регионы</option>
            {regions.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
          <select className="border rounded px-3 py-2" value={filterAgent}
            onChange={e => setFilterAgent(e.target.value as any)}>
            <option value="all">Все объявления</option>
            <option value="private">Только частные</option>
            <option value="agent">Только риэлторы</option>
          </select>
          <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={() => handleParse('avito')}>
            🔄 Парсить Avito
          </button>
          <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={() => handleParse('cian')}>
            🔄 Парсить Cian
          </button>
        </div>
      </header>

      {loading ? <div className="text-center py-8">Загрузка...</div> :
        listings.length === 0 ? <div className="text-center py-8 text-gray-500">Нет объявлений. Запустите парсинг.</div> :
        listings.map(l => <ListingCard key={l.id} listing={l} />)
      }
    </div>
  );
}
```

- [ ] **Step 5: App.tsx и main.tsx**

```tsx
// frontend/src/App.tsx
import { ListingsPage } from './pages/Listings';

export default function App() {
  return <ListingsPage />;
}
```

```tsx
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
);
```

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: React frontend with listings, filters, parser controls"
```

---

## Фаза 6: Docker и финализация

### Task 10: Docker Compose и запуск всего проекта

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`

- [ ] **Step 1: docker-compose.yml**

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: hata
      POSTGRES_PASSWORD: hata
      POSTGRES_DB: hata
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://hata:hata@db:5432/hata
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
    volumes: [./backend:/app]
    depends_on: [db, redis]

  celery:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://hata:hata@db:5432/hata
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
    volumes: [./backend:/app]
    depends_on: [db, redis]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes: [./frontend:/app]
    command: npm run dev -- --host

volumes:
  pgdata:
```

- [ ] **Step 2: Бэкенд Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - || true
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
COPY . .
```

- [ ] **Step 3: Фронтенд Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
```

- [ ] **Step 4: Commit and run**

```bash
git add docker-compose.yml backend/Dockerfile frontend/Dockerfile
git commit -m "feat: Docker Compose setup for full project"
docker compose up -d
```

---

## План запуска после реализации

1. `docker compose up -d db redis` — запустить базу и кэш
2. `python backend/scripts/seed_data.py` — заполнить регионы
3. `python backend/scripts/import_phone_defs.py` — импортировать DEF-коды
4. `docker compose up -d` — запустить всё
5. Открыть `http://localhost:5173`
