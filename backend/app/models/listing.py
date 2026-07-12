from __future__ import annotations

from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Enum, func
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
    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
