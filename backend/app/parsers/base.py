from abc import ABC, abstractmethod
from dataclasses import dataclass


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

    @staticmethod
    def format_phone(raw: str) -> str | None:
        """Normalize phone to +7XXXXXXXXXX format."""
        import re
        if not raw:
            return None
        digits = re.sub(r'\D', '', raw)
        if len(digits) == 11 and digits[0] == '8':
            digits = '7' + digits[1:]
        elif len(digits) == 10:
            digits = '7' + digits
        elif len(digits) == 11 and digits[0] == '7':
            pass
        elif len(digits) < 10:
            return None
        return '+' + digits
