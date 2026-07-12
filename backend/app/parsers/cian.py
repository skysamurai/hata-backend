import re
from playwright.async_api import async_playwright
from app.parsers.base import BaseParser, ParsedListing


class CianParser(BaseParser):
    source = "cian"

    async def parse_region(self, region_id: int, avito_location_id: int | None,
                           cian_region_id: int | None) -> list[ParsedListing]:
        listings = []
        if not cian_region_id:
            return listings

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Build search URL for the region
            url = (
                f"https://www.cian.ru/cat.php?"
                f"deal_type=rent&engine_version=2&offer_type=flat&"
                f"region={cian_region_id}&type=3"
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            for page_num in range(1, 6):  # 5 pages max
                try:
                    # Wait for listing cards to appear
                    await page.wait_for_selector(
                        "article[data-name='CardComponent'], div[data-name='OfferCard']",
                        timeout=10000
                    )

                    # Scroll to load all content
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                    # Extract listing data from the page
                    cards = await page.query_selector_all(
                        "article[data-name='CardComponent'], div[data-testid='offer-card']"
                    )
                    for card in cards:
                        listing = await self._parse_card(card)
                        if listing:
                            listings.append(listing)

                    if not cards:
                        break

                    # Try to go to next page
                    next_btn = await page.query_selector(
                        "a[data-name='Pagination']:last-child, ul[data-name='Pagination'] + a"
                    )
                    if next_btn:
                        is_disabled = await next_btn.get_attribute("aria-disabled")
                        if is_disabled:
                            break
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                    else:
                        break
                except Exception as e:
                    print(f"Cian error page {page_num}: {e}")
                    break

            await browser.close()
        return listings

    async def _parse_card(self, card) -> ParsedListing | None:
        try:
            # Get Cian ID from link
            link = await card.query_selector("a")
            href = await link.get_attribute("href") if link else ""
            if not href or "/rent/" not in href:
                return None

            cian_id_match = re.search(r'/(?:flat|room|house)/(\d+)', href)
            if not cian_id_match:
                return None
            external_id = cian_id_match.group(1)

            # Get full URL
            if href.startswith("/"):
                href = f"https://www.cian.ru{href}"

            # Title
            title_el = await card.query_selector("[data-name='Title'], span[data-mark='OfferTitle']")
            title = await title_el.inner_text() if title_el else "Без названия"

            # Price
            price_el = await card.query_selector("span[data-mark='MainPrice'], span[data-mark='Price']")
            price_text = await price_el.inner_text() if price_el else "0"
            price = int(re.sub(r'\D', '', price_text)) if price_text else None

            # Address
            addr_el = await card.query_selector("[data-name='Address'], span[data-mark='Address']")
            address = await addr_el.inner_text() if addr_el else None

            # Metro
            metro_el = await card.query_selector("[data-name='Metro'], span[data-mark='Metro']")
            metro = await metro_el.inner_text() if metro_el else None

            # Description - try to get from card or we'll leave it minimal
            desc_el = await card.query_selector("[data-name='Description'], div[data-mark='Description']")
            description = await desc_el.inner_text() if desc_el else None

            # Try to get card inner text for phone extraction
            card_text = await card.inner_text() if card else ""

            phone_raw = self._extract_phone(card_text)
            phone_formatted = self.format_phone(phone_raw) if phone_raw else None

            return ParsedListing(
                external_id=external_id,
                url=href,
                title=title, price=price, address=address, metro=metro,
                rooms=None, area=None, floor=None, total_floors=None,
                description=description, phone_raw=phone_raw,
                phone_formatted=phone_formatted, source="cian"
            )
        except Exception as e:
            print(f"Error parsing Cian card: {e}")
            return None

    @staticmethod
    def _extract_phone(text: str) -> str | None:
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
