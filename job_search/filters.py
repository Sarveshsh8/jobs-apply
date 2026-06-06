from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from .config import FilterConfig
from .extractor import JobListing


class LocationVerdict:
    OPEN = "open"
    RESTRICTED = "restricted"
    UNCLEAR = "unclear"


def check_location(listing: JobListing, config: FilterConfig) -> tuple[str, str]:
    text = f"{listing.location} {listing.description}".lower()

    for flag in config.location_red_flags:
        if flag.lower() in text:
            return LocationVerdict.RESTRICTED, f"red flag: '{flag}'"

    for flag in config.location_green_flags:
        if flag.lower() in text:
            return LocationVerdict.OPEN, f"green flag: '{flag}'"

    return LocationVerdict.UNCLEAR, "no location signals found"


def matches_titles(listing: JobListing, config: FilterConfig) -> bool:
    if not config.include_titles:
        return True
    title_lower = listing.title.lower()
    return any(t.lower() in title_lower for t in config.include_titles)


def matches_skills(listing: JobListing, config: FilterConfig) -> bool:
    if not config.include_skills:
        return True
    desc_lower = listing.description.lower()
    return any(s.lower() in desc_lower for s in config.include_skills)


def is_recent(listing: JobListing, config: FilterConfig) -> bool:
    if not listing.posted_date:
        return True
    try:
        posted = datetime.fromisoformat(listing.posted_date)
        cutoff = datetime.now() - timedelta(days=config.recency_days)
        return posted >= cutoff
    except ValueError:
        return True


def is_excluded(listing: JobListing, config: FilterConfig) -> bool:
    company_lower = listing.company.lower()
    if any(c.lower() in company_lower for c in config.exclude_companies):
        return True
    text = f"{listing.title} {listing.description}".lower()
    if any(k.lower() in text for k in config.exclude_keywords):
        return True
    return False


class SeenJobsCache:
    def __init__(self, path: Path):
        self._path = path
        self._seen: set[str] = set()
        if path.exists():
            self._seen = set(json.loads(path.read_text()))

    def is_seen(self, job_id: str) -> bool:
        return job_id in self._seen

    def add(self, job_id: str) -> None:
        self._seen.add(job_id)

    def save(self) -> None:
        self._path.write_text(json.dumps(sorted(self._seen)))


def filter_listings(
    listings: list[JobListing],
    config: FilterConfig,
    cache: SeenJobsCache,
) -> list[tuple[JobListing, str, str]]:
    results = []
    for listing in listings:
        if not listing.job_id or cache.is_seen(listing.job_id):
            continue
        if is_excluded(listing, config):
            continue
        if not matches_titles(listing, config):
            continue
        if not matches_skills(listing, config):
            continue
        if not is_recent(listing, config):
            continue
        verdict, reason = check_location(listing, config)
        if verdict != LocationVerdict.OPEN:
            continue
        results.append((listing, verdict, reason))
        cache.add(listing.job_id)
    return results
