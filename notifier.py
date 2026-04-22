import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_notification(listing: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[INFO] Telegram credentials not set - skipping notification.")
        return

    age_line = f"\n⏰ <b>Posted:</b>  {listing['age']}" if listing.get("age") else ""
    salary_line = f"\n💰 <b>Salary:</b>   {listing['salary']}" if listing.get("salary") else ""
    text = (
        f"🆕 <b>New Internship Posted!</b>\n"
        f"<i>{listing.get('tag', listing['source'])}</i>\n\n"
        f"📂 <b>Category:</b> {listing['category']}\n"
        f"🏢 <b>Company:</b>  {listing['company']}\n"
        f"💼 <b>Role:</b>     {listing['role']}\n"
        f"📍 <b>Location:</b> {listing['location']}"
        f"{salary_line}"
        f"{age_line}\n"
        f"🔗 <b>Apply:</b>    {listing['url']}\n\n"
        f"<code>{listing['source']}</code>"
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
