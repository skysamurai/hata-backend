from __future__ import annotations

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
    parent: Mapped[Region | None] = relationship(remote_side=[id])
