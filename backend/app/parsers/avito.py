import httpx
from app.parsers.base import BaseParser, ParsedListing


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
                for page in range(1, 6):  # 5 pages per category
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
                        "limit": 30,
                    }
                    try:
                        resp = await client.get(self.API_URL, params=params)
                        data = resp.json()
                        items = data.get("result", {}).get("items", [])
                        if not items:
                            break
                        for item in items:
                            listing = self._parse_item(item)
                            if listing:
                                listings.append(listing)
                    except Exception as e:
                        print(f"Avito API error category={category_id} page={page}: {e}")
                        break
        return listings

    def _parse_item(self, item: dict) -> ParsedListing | None:
        try:
            item_id = str(item.get("id", item.get("itemId", "")))
            if not item_id:
                return None

            title = item.get("title", "")

            # Parse price from value string like "18 000 ₽ за месяц"
            price_raw = item.get("price", {}).get("value", "0") if isinstance(item.get("price"), dict) else str(item.get("price", "0"))
            price = int(''.join(filter(str.isdigit, price_raw))) if price_raw else None

            address = item.get("address", "")
            metro_list = item.get("metro", [])
            metro = metro_list[0].get("name", "") if metro_list else None

            description = item.get("description", "")

            # Extract phone from description
            phone_raw = self._extract_phone(description)
            phone_formatted = self.format_phone(phone_raw) if phone_raw else None

            # Extract structured params
            params_list = item.get("params", [])
            params = {}
            for p in params_list:
                if isinstance(p, dict):
                    name = p.get("nameSlug", p.get("name", ""))
                    text = p.get("text", "")
                    params[name] = text

            rooms = self._parse_int(params.get("number_of_rooms", params.get("rooms", "")))
            area = self._parse_float(params.get("area", ""))
            floor_info = params.get("floor", "")
            floor, total_floors = self._parse_floor(floor_info)

            return ParsedListing(
                external_id=item_id,
                url=f"https://www.avito.ru/items/{item_id}",
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
        if not text:
            return None
        patterns = [
            r'(\+7[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
            r'(8[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})',
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _parse_int(text: str) -> int | None:
        if not text:
            return None
        digits = ''.join(filter(str.isdigit, str(text)))
        return int(digits) if digits else None

    @staticmethod
    def _parse_float(text: str) -> float | None:
        if not text:
            return None
        import re
        match = re.search(r'[\d]+[.,]?[\d]*', str(text))
        return float(match.group().replace(',', '.')) if match else None

    @staticmethod
    def _parse_floor(floor_info: str) -> tuple[int | None, int | None]:
        if not floor_info:
            return None, None
        import re
        nums = re.findall(r'\d+', str(floor_info))
        if not nums:
            return None, None
        floor = int(nums[0])
        total = int(nums[1]) if len(nums) >= 2 else None
        return floor, total
