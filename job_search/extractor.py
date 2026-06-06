from __future__ import annotations

import logging
from dataclasses import dataclass

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    posted_date: str
    description: str
    link: str
    job_id: str


def extract_listings(page: Page) -> list[JobListing]:
    listings: list[JobListing] = []

    cards = page.query_selector_all(".job-card-container")
    if not cards:
        cards = page.query_selector_all("[data-job-id]")

    for card in cards:
        try:
            job_id = card.get_attribute("data-job-id") or ""
            title_el = card.query_selector(".job-card-list__title--link, .job-card-container__link")
            title = (title_el.inner_text().strip() if title_el else "").split("\n")[0]
            link = title_el.get_attribute("href") if title_el else ""
            if link and not link.startswith("http"):
                link = "https://www.linkedin.com" + link

            company_el = card.query_selector(".artdeco-entity-lockup__subtitle, .job-card-container__primary-description")
            company = company_el.inner_text().strip() if company_el else ""

            location_el = card.query_selector(".artdeco-entity-lockup__caption, .job-card-container__metadata-wrapper")
            location = location_el.inner_text().strip() if location_el else ""

            date_el = card.query_selector("time")
            posted = date_el.get_attribute("datetime") if date_el else ""

            description = _get_description(page, title_el) or ""

            listings.append(JobListing(
                title=title, company=company, location=location,
                posted_date=posted, description=description,
                link=link, job_id=job_id.strip(),
            ))
        except Exception:
            logger.warning("Failed to extract a listing, skipping", exc_info=True)

    return listings


def _get_description(page: Page, title_el) -> str:
    if title_el:
        try:
            title_el.click()
            page.wait_for_selector(".jobs-description__content, .jobs-box__html-content", timeout=5000)
            desc_el = page.query_selector(".jobs-description__content, .jobs-box__html-content")
            if desc_el:
                return desc_el.inner_text().strip()
        except Exception:
            logger.debug("Could not load description", exc_info=True)
    return ""
