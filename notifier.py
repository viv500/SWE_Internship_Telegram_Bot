import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_notification(listing: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[INFO] Telegram credentials not set - skipping notification.")
        return

    age_line = f"\n⏰ {listing['age']}" if listing.get("age") else ""
    salary_line = f"\n💰 {listing['salary']}" if listing.get("salary") else ""
    text = (
        f"🏢 <b>{listing['company'].upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💼 {listing['role']}\n"
        f"📍 {listing['location']}"
        f"{salary_line}"
        f"{age_line}\n\n"
        f"<a href=\"{listing['url']}\">➡️ Apply Now</a>\n\n"
        f"<i>{listing.get('tag', listing['source'])} · {listing['category']}</i>"
    )

    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)
    try:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to send Telegram notification: {e}")
