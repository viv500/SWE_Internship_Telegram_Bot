# SWE Internship Telegram Bot

A Python bot that monitors 6 GitHub-hosted SWE internship tracking repositories, detects new postings, and sends Telegram notifications. Runs automatically every 15 minutes via GitHub Actions.

**Tracked sources:**
- 🟢 SimplifyJobs · Summer 2026
- 🟡 SimplifyJobs · Off-Season 2026
- 🍁 Canadian Tech · 2026
- 🚀 SpeedyApply · FAANG+ 2026
- ⭐ Vansh+Ouckah · Summer 2026
- 🌀 Vansh+Ouckah · Spring/Fall 2026

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

Create a `.env` file in the project root:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Getting your credentials:**
- **Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token
- **Chat ID**: Start a conversation with your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and find `"chat": {"id": ...}`

### 3. Run locally

```bash
python3 main.py
```

On the **first run**, all current listings are seeded as seen — no notifications are sent (avoids a flood). On subsequent runs, only **new** postings trigger a notification.

## GitHub Actions (automated)

The workflow in `.github/workflows/check_internships.yml` runs every 15 minutes automatically.

**Required repo secrets** (Settings → Secrets and variables → Actions):
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

`state.json` is persisted across runs using `actions/cache` so the bot remembers what it has already seen.

> **Note:** GitHub may delay scheduled workflows by up to ~10 minutes under high load. This is normal.

## Project Structure

```
├── main.py          # Entry point — orchestrates the full flow
├── config.py        # Source definitions and credentials (loaded from .env)
├── scraper.py       # Fetches and parses listings via GitHub Contents API
├── state.py         # Reads/writes seen listing IDs to state.json
├── notifier.py      # Sends Telegram messages
├── state.json       # Auto-created on first run, gitignored
├── .env             # Your credentials — never commit this
├── requirements.txt
└── .github/
    └── workflows/
        └── check_internships.yml
```

## Adding More Sources

Edit `SOURCES` in `config.py`. Each source needs:

```python
{
    "name": "owner/repo",
    "tag": "emoji Label",
    "url": "https://github.com/owner/repo/blob/branch/README.md",
    "top_n": 20,  # how many rows per section to track
    "skip_category_keywords": ["Legend", "Want notifications"],  # headings to skip
    "columns": {
        "company": 0,
        "role": 1,
        "location": 2,
        "link_column": 3,
        "age": 4,
    },
}
```

The scraper uses the GitHub Contents API (`Accept: application/vnd.github.html+json`) to get rendered HTML, then walks `<table>` elements and matches them to the nearest preceding heading.

## Test Mode

In `main.py`, `TEST_MODE = True` prints the first 3 listings per section on every run so you can verify scraping is working without sending notifications. Set it to `False` in production.

