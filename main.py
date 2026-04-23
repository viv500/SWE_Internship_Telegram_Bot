import os
import datetime
import re
from collections import defaultdict
from config import SOURCES, STATE_FILE
from scraper import fetch_listings
from state import load_state, save_state, get_seen_ids, mark_seen
from notifier import send_notification

TEST_MODE = True   # Set False in production to suppress preview output
TEST_PREVIEW_COUNT = 3


def should_send_test_ping() -> bool:
    return os.getenv("TELEGRAM_TEST_PING", "").strip().lower() in {"1", "true", "yes", "on"}


def send_test_ping():
    test_listing = {
        "category": "Workflow Test",
        "company": "GitHub Actions",
        "role": "Telegram Pipeline Check",
        "location": "N/A",
        "salary": "N/A",
        "age": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "url": "https://github.com",
        "source": "manual workflow_dispatch",
        "tag": "🧪 Test Ping",
    }
    send_notification(test_listing)
    log("INFO", "Sent Telegram test ping (TELEGRAM_TEST_PING enabled)")


def _age_to_days(age_text: str):
    if not age_text:
        return None

    s = age_text.strip().lower()
    m = re.search(r"(\d+)", s)
    if not m:
        return None

    value = int(m.group(1))
    if "mo" in s or "month" in s:
        return value * 30
    if "w" in s or "week" in s:
        return value * 7
    if "d" in s or "day" in s:
        return value
    if "h" in s or "hour" in s:
        return 0
    return None


def _within_age_limit(listing: dict, max_age_days: int | None) -> bool:
    if max_age_days is None:
        return True

    age_days = _age_to_days(listing.get("age", ""))
    # If age cannot be parsed, keep the notification path unchanged.
    if age_days is None:
        return True
    return age_days <= max_age_days


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

    if should_send_test_ping():
        send_test_ping()

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
        source_skipped_old = 0
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
            unseen_listings = [l for l in cat_listings if l["id"] not in seen_ids]

            max_age_days = source.get("notify_max_age_days")
            notify_listings = [l for l in unseen_listings if _within_age_limit(l, max_age_days)]
            skipped_old = len(unseen_listings) - len(notify_listings)
            source_skipped_old += skipped_old

            if notify_listings:
                for listing in notify_listings:
                    send_notification(listing)
                    log("NOTIFY", f"  [{category}] {listing['company']} — {listing['role']}")
                    source_new += 1
            else:
                log("OK", f"  [{category}] No new listings (scanned {len(cat_listings)})")

            if skipped_old:
                log("INFO", f"  [{category}] Skipped {skipped_old} older listing(s) by age filter")

            state = mark_seen(state, state_key, [l["id"] for l in unseen_listings])

        if is_first_run:
            log("INFO", f"  Seeded {len(listings)} listings across {len(by_category)} sections")
        else:
            status = f"{source_new} NEW" if source_new else "nothing new"
            if source_skipped_old:
                status += f", {source_skipped_old} old skipped"
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
