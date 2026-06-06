from __future__ import annotations

from .extractor import JobListing


def print_results(results: list[tuple[JobListing, str, str]]) -> None:
    if not results:
        print("\nNo new matching jobs found.")
        return

    print(f"\n{'='*60}")
    print(f" Found {len(results)} new matching job(s)")
    print(f"{'='*60}\n")

    for i, (job, verdict, reason) in enumerate(results, 1):
        print(f"  {i}. {job.title}")
        print(f"     Company:  {job.company}")
        print(f"     Location: {verdict} ({reason})")
        print(f"     Posted:   {job.posted_date or 'unknown'}")
        print(f"     Link:     {job.link}")
        print()
