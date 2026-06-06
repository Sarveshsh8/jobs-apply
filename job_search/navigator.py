import logging
import random
import time
from urllib.parse import quote_plus

from playwright.sync_api import Page

from .config import SearchConfig

logger = logging.getLogger(__name__)

DATE_POSTED_MAP = {
    "past_24h": "r86400",
    "past_week": "r604800",
    "past_month": "r2592000",
}


def build_search_url(keywords: str, date_posted: str, start: int = 0, location: str = "", geo_id: str = "") -> str:
    base = "https://www.linkedin.com/jobs/search/?"
    params = [
        f"keywords={quote_plus(keywords)}",
        "f_WT=2",  # remote filter
        f"f_TPR={DATE_POSTED_MAP.get(date_posted, 'r604800')}",
        "sortBy=DD",
    ]
    if location:
        params.append(f"location={quote_plus(location)}")
    if geo_id:
        params.append(f"geoId={geo_id}")
    if start:
        params.append(f"start={start}")
    return base + "&".join(params)


def _is_browser_dead(e: Exception) -> bool:
    msg = str(e).lower()
    return "browser has been closed" in msg or "target page" in msg


def iter_search_pages(page: Page, config: SearchConfig):
    consecutive_failures = 0
    locations = config.locations or [{"name": "", "geo_id": ""}]
    search_idx = 0

    for loc in locations:
        loc_name = loc.get("name", "")
        geo_id = loc.get("geo_id", "")
        for kw in config.keywords:
            if search_idx > 0:
                cooldown = random.uniform(15, 25)
                print(f"  Cooling down {cooldown:.0f}s before next search...")
                time.sleep(cooldown)
            search_idx += 1

            label = f"{kw!r} in {loc_name}" if loc_name else f"{kw!r}"
            for page_num in range(config.max_pages):
                if consecutive_failures >= 3:
                    print("  Too many failures — stopping to avoid rate limit. Run again later.")
                    return

                url = build_search_url(kw, config.date_posted, start=page_num * 25, location=loc_name, geo_id=geo_id)
                print(f"  Loading: {label} page {page_num + 1}/{config.max_pages}")

            success = False
            for attempt in range(2):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    success = True
                    consecutive_failures = 0
                    break
                except Exception as e:
                    if _is_browser_dead(e):
                        print("  Browser closed — stopping. Run again later.")
                        return
                    if attempt == 0:
                        wait = random.uniform(10, 20)
                        print(f"  Rate limited, waiting {wait:.0f}s...")
                        time.sleep(wait)
                    else:
                        consecutive_failures += 1
                        logger.warning(f"Skipping {kw!r} page {page_num + 1} after retry")

            if not success:
                continue

            delay = config.page_delay_seconds + random.uniform(2, 5)
            time.sleep(delay)
            yield page
