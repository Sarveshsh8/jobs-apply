from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SearchConfig:
    keywords: list[str] = field(default_factory=lambda: ["software engineer"])
    remote_filter: bool = True
    date_posted: str = "past_week"
    max_pages: int = 5
    page_delay_seconds: int = 3
    locations: list[dict[str, str]] = field(default_factory=list)


@dataclass
class FilterConfig:
    recency_days: int = 7
    include_titles: list[str] = field(default_factory=list)
    include_skills: list[str] = field(default_factory=list)
    exclude_companies: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    location_red_flags: list[str] = field(default_factory=list)
    location_green_flags: list[str] = field(default_factory=list)


@dataclass
class BrowserConfig:
    user_data_dir: str = "./user_data"
    headless: bool = False


@dataclass
class AppConfig:
    search: SearchConfig = field(default_factory=SearchConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)


def load_config(path: Path) -> AppConfig:
    raw = yaml.safe_load(path.read_text())
    return AppConfig(
        search=SearchConfig(**raw.get("search", {})),
        filters=FilterConfig(**raw.get("filters", {})),
        browser=BrowserConfig(**raw.get("browser", {})),
    )
