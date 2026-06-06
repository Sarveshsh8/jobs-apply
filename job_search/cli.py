from pathlib import Path

import click

from .browser import BrowserSession
from .config import load_config
from .extractor import extract_listings
from .filters import SeenJobsCache, filter_listings
from .navigator import iter_search_pages
from .reporter import print_results


@click.command()
@click.option("--config", "config_path", default="config.yaml", type=click.Path(exists=True), help="Path to config YAML")
def main(config_path: str):
    cfg = load_config(Path(config_path))
    cache = SeenJobsCache(Path("seen_jobs.json"))
    session = BrowserSession(cfg.browser)

    try:
        page = session.launch()
        session.ensure_logged_in(page)

        all_listings = []
        for results_page in iter_search_pages(page, cfg.search):
            all_listings.extend(extract_listings(results_page))

        print(f"\nExtracted {len(all_listings)} total listings")
        results = filter_listings(all_listings, cfg.filters, cache)
        print_results(results)
        cache.save()
    finally:
        session.close()


if __name__ == "__main__":
    main()
