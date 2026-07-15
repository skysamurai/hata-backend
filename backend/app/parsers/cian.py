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
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--no-sandbox',
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ru-RU',
                timezone_id='Europe/Moscow',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                bypass_csp=True,
            )
            page = await context.new_page()
            await page.add_init_script('''
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU','ru','en-US','en']});
            ''')

            # Warm up: visit a neutral site first
            try:
                await page.goto("https://www.google.com", wait_until="load", timeout=15000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            url = (
                f"https://www.cian.ru/cat.php?"
                f"deal_type=rent&engine_version=2&offer_type=flat&"
                f"region={cian_region_id}&type=3"
            )
            await page.goto(url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(5000)

            for page_num in range(1, 6):
                try:
                    # Scroll to trigger lazy loading
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)

                    cards = await page.query_selector_all("div[data-testid='offer-card']")
                    if not cards:
                        # Fallback selectors
                        cards = await page.query_selector_all(
                            "article[data-name='CardComponent'], div[data-name='OfferCard']"
                        )

                    for card in cards:
                        listing = await self._parse_card(card)
                        if listing:
                            listings.append(listing)

                    if not cards:
                        break

                    # Try next page
                    next_btn = await page.query_selector("a[data-name='Pagination']:last-child, ul[data-name='Pagination'] + a")
                    if next_btn:
                        is_disabled = await next_btn.get_attribute("aria-disabled")
                        if is_disabled:
                            break
                        await next_btn.click()
                        await page.wait_for_timeout(3000)
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

            if href.startswith("/"):
                href = f"https://www.cian.ru{href}"

            # Title
            title_el = await card.query_selector(
                "[data-name='Title'], span[data-mark='OfferTitle'], [class*='title']"
            )
            title = await title_el.inner_text() if title_el else "Без названия"

            # Price — grab first number only (₽/month)
            price_el = await card.query_selector(
                "span[data-mark='MainPrice'], [class*='price']"
            )
            price_text = await price_el.inner_text() if price_el else "0"
            # Extract first number sequence (the monthly rent)
            price_match = re.search(r'(\d[\d\s]*)', price_text)
            price = int(re.sub(r'\s', '', price_match.group(1))) if price_match else None

            # Address
            addr_el = await card.query_selector(
                "[data-name='Address'], span[data-mark='Address'], [class*='address']"
            )
            if addr_el:
                address = await addr_el.inner_text()
            else:
                # Try to extract address from card text
                full_text = await card.inner_text()
                lines = full_text.split('\n')
                # Address is usually one of the first few lines with a street name
                address = lines[1] if len(lines) > 1 and len(lines[1]) > 5 else None

            # Metro
            metro_el = await card.query_selector("[data-name='Metro'], span[data-mark='Metro']")
            metro = await metro_el.inner_text() if metro_el else None

            # Description
            desc_el = await card.query_selector(
                "[data-name='Description'], div[data-mark='Description']"
            )
            description = await desc_el.inner_text() if desc_el else None

            # Phone extraction from card text
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
