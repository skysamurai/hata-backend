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
