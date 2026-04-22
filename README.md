# SWE Internship Telegram Bot

A lightweight Python script that monitors GitHub-hosted SWE internship tracking repositories, detects new postings, and sends Telegram notifications. Designed to run as a scheduled hourly job.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Getting your credentials:**
- Bot Token: Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token
- Chat ID: Start a conversation with your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and find `"chat": {"id": ...}`

### 3. Run

```bash
python3 main.py
```

On the **first run**, all current listings are marked as seen and no notifications are sent (to avoid a flood). On subsequent runs, only **new** postings trigger a notification.

## Project Structure

```
├── main.py          # Entry point — orchestrates the full flow
├── config.py        # URLs, selectors, credentials (loaded from .env)
├── scraper.py       # Fetches and parses internship rows via GitHub API
├── state.py         # Reads/writes seen listing IDs to state.json
├── notifier.py      # Sends Telegram messages
├── state.json       # Auto-created on first run, gitignored
├── .env             # Your credentials — never commit this
└── requirements.txt
```

## Adding More Sources

Edit `SOURCES` in `config.py`. Each source needs:

```python
{
    "name": "Display name",
    "url": "https://github.com/owner/repo/blob/branch/README.md",
    "row_selector": "table tbody tr",
    "columns": {
        "company": 0,  # column index (0-based)
        "role": 1,
        "location": 2,
        "link_column": 3,  # column containing the Apply link
    },
}
```

## Scheduled Runs (PythonAnywhere)

1. Upload all files to a directory (e.g. `/home/you/internship-bot/`)
2. Install dependencies: `pip install -r requirements.txt`
3. Set env vars in the PythonAnywhere **Web** tab, or prefix the command:
   ```bash
   TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python3 main.py
   ```
4. Go to **Tasks** tab → add a scheduled task running hourly

## Test Mode

In `main.py`, `TEST_MODE = True` prints the first 10 listings on every run so you can verify scraping is working. Set it to `False` in production.
