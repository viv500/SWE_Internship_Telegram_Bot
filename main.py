import os
import datetime
from collections import defaultdict
from config import SOURCES, STATE_FILE
from scraper import fetch_listings
from state import load_state, save_state, get_seen_ids, mark_seen
from notifier import send_notification

TEST_MODE = True   # Set False in production to suppress preview output
TEST_PREVIEW_COUNT = 3


def log(level: str, msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def print_preview(listings: list[dict]):
    by_category = defaultdict(list)
    for l in listings:
        by_category[l["category"]].append(l)

    print(f"  {'─'*56}")
    print(f"  PREVIEW (first {TEST_PREVIEW_COUNT} per category)")
    print(f"  {'─'*56}")
    for category, items in by_category.items():
        print(f"  [{category}]")
        for listing in items[:TEST_PREVIEW_COUNT]:
            salary = f"  salary={listing['salary']}" if listing.get("salary") else ""
            apply = listing["url"] if listing["url"] else "N/A"
            print(f"    • {listing['company']} | {listing['role']}{salary}")
            print(f"      Apply: {apply}")
    print()


def main():
    run_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*64}")
    print(f"  Internship Bot Run — {run_start}")
    print(f"  Sources configured: {len(SOURCES)}")
    print(f"{'='*64}\n")

    is_first_run = not os.path.exists(STATE_FILE)
    state = load_state()

    if is_first_run:
        log("INFO", "First run — seeding all buckets. No notifications sent.")

    total_new = 0

    for source in SOURCES:
        print(f"\n{'─'*64}")
        log("INFO", f"Source : {source['name']}")
        log("INFO", f"Tag    : {source.get('tag', '—')}")
        log("INFO", f"URL    : {source['url']}")

        try:
            listings = fetch_listings(source)
        except Exception as e:
            log("ERROR", f"Failed to fetch — {e}")
            continue

        by_category = defaultdict(list)
        for l in listings:
            by_category[l["category"]].append(l)

        log("INFO", f"Fetched {len(listings)} listings across {len(by_category)} section(s):")
        for cat, items in by_category.items():
            log("INFO", f"  • {cat}: {len(items)} rows")

        if TEST_MODE:
            print_preview(listings)

        source_new = 0
        for category, cat_listings in by_category.items():
            state_key = f"{source['name']}::{category}"

            if is_first_run:
                state = mark_seen(state, state_key, [l["id"] for l in cat_listings])
                continue

            if state_key not in state:
                state = mark_seen(state, state_key, [l["id"] for l in cat_listings])
                log("INFO", f"  Seeded new bucket '{category}' ({len(cat_listings)} listings)")
                continue

            seen_ids = get_seen_ids(state, state_key)
            new_listings = [l for l in cat_listings if l["id"] not in seen_ids]

            if new_listings:
                for listing in new_listings:
                    send_notification(listing)
                    log("NOTIFY", f"  [{category}] {listing['company']} — {listing['role']}")
                    source_new += 1
            else:
                log("OK", f"  [{category}] No new listings (scanned {len(cat_listings)})")

            state = mark_seen(state, state_key, [l["id"] for l in new_listings])

        if is_first_run:
            log("INFO", f"  Seeded {len(listings)} listings across {len(by_category)} sections")
        else:
            status = f"{source_new} NEW" if source_new else "nothing new"
            log("INFO", f"  Result: {status}")
            total_new += source_new

    print(f"\n{'='*64}")
    if not is_first_run:
        log("INFO", f"Run complete — {total_new} new listing(s) found across all sources")
    else:
        log("INFO", "Seeding complete — bot is ready. Run again to start monitoring.")
    log("INFO", "State saved.")
    print(f"{'='*64}\n")

    save_state(state)


if __name__ == "__main__":
    main()
