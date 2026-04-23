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


def get_recent_audit_days() -> int | None:
    raw = os.getenv("RECENT_AUDIT_DAYS", "").strip()
    if not raw:
        return None
    try:
        val = int(raw)
    except ValueError:
        return None
    return val if val >= 0 else None


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


def _parse_absolute_date_days(s: str):
    normalized = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s.strip(), flags=re.IGNORECASE)
    normalized = normalized.replace(",", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    today = datetime.date.today()
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d %Y",
        "%B %d %Y",
        "%b %d",
        "%B %d",
    ]

    for fmt in formats:
        try:
            parsed = datetime.datetime.strptime(normalized, fmt).date()
            if "%Y" not in fmt and "%y" not in fmt:
                parsed = parsed.replace(year=today.year)
                # Handle year rollover for dates like "Dec 31" when today is Jan.
                if parsed > today + datetime.timedelta(days=1):
                    parsed = parsed.replace(year=today.year - 1)
            delta = (today - parsed).days
            if delta < 0:
                return 0
            return delta
        except ValueError:
            continue

    return None


def _age_to_days(age_text: str, age_format: str = "auto"):
    if not age_text:
        return None

    mode = (age_format or "auto").strip().lower()
    s = age_text.strip().lower()
    if s in {"today", "new", "just now", "now"}:
        return 0
    if s == "yesterday":
        return 1

    if mode in {"auto", "absolute"}:
        absolute_days = _parse_absolute_date_days(age_text)
        if absolute_days is not None:
            return absolute_days

    if mode == "absolute":
        return None

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


def _within_age_limit(listing: dict, max_age_days: int | None, age_format: str = "auto") -> bool:
    if max_age_days is None:
        return True

    age_days = _age_to_days(listing.get("age", ""), age_format)
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


def print_recent_audit(source_name: str, listings: list[dict], max_days: int, age_format: str = "auto"):
    recent = []
    for listing in listings:
        age_days = _age_to_days(listing.get("age", ""), age_format)
        if age_days is not None and age_days <= max_days:
            recent.append((age_days, listing))

    recent.sort(key=lambda x: x[0])
    log("INFO", f"Recent age-audit (0-{max_days}d): {len(recent)} listing(s)")
    for age_days, listing in recent:
        log(
            "INFO",
            (
                f"  [{listing['category']}] {listing['company']} — {listing['role']} "
                f"| age='{listing.get('age', '')}' ({age_days}d)"
            ),
        )


def main():
    run_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*64}")
    print(f"  Internship Bot Run — {run_start}")
    print(f"  Sources configured: {len(SOURCES)}")
    print(f"{'='*64}\n")

    is_first_run = not os.path.exists(STATE_FILE)
    state = load_state()

    if is_first_run:
        log("INFO", "First run — seeding old listings only. Recent ones will notify on next run.")

    if should_send_test_ping():
        send_test_ping()

    recent_audit_days = get_recent_audit_days()

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

        if recent_audit_days is not None:
            print_recent_audit(
                source["name"],
                listings,
                recent_audit_days,
                source.get("age_format", "auto"),
            )

        source_new = 0
        source_skipped_old = 0
        for category, cat_listings in by_category.items():
            state_key = f"{source['name']}::{category}"

            max_age_days = source.get("notify_max_age_days")
            age_format = source.get("age_format", "auto")

            if is_first_run or state_key not in state:
                # Seed only listings that are OLDER than our notification window.
                # Recent listings are intentionally left unseeded so they notify on the next run.
                seed_ids = [
                    l["id"] for l in cat_listings
                    if not _within_age_limit(l, max_age_days, age_format)
                ]
                state = mark_seen(state, state_key, seed_ids)
                recent_count = len(cat_listings) - len(seed_ids)
                if is_first_run:
                    log("INFO", f"  [{category}] Seeded {len(seed_ids)} old, left {recent_count} recent to notify next run")
                else:
                    log("INFO", f"  Seeded new bucket '{category}' ({len(seed_ids)} old, {recent_count} recent pending)")
                continue

            seen_ids = get_seen_ids(state, state_key)
            unseen_listings = [
                l for l in cat_listings
                if l["id"] not in seen_ids and l.get("legacy_id") not in seen_ids
            ]

            max_age_days = source.get("notify_max_age_days")
            age_format = source.get("age_format", "auto")
            notify_listings = [
                l for l in unseen_listings
                if _within_age_limit(l, max_age_days, age_format)
            ]
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

        status = f"{source_new} NEW" if source_new else "nothing new"
        if source_skipped_old:
            status += f", {source_skipped_old} old skipped"
        log("INFO", f"  Result: {status}")
        total_new += source_new

    print(f"\n{'='*64}")
    if is_first_run:
        log("INFO", "Seeding complete — recent listings will notify on next run.")
    else:
        log("INFO", f"Run complete — {total_new} new listing(s) found across all sources")
    log("INFO", "State saved.")
    print(f"{'='*64}\n")

    save_state(state)


if __name__ == "__main__":
    main()
