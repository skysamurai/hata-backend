from __future__ import annotations

from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
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
