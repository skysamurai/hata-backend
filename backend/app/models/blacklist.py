from __future__ import annotations

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
