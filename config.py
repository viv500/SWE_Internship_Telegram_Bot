import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# How many most-recent rows to check per category per source
TOP_N = 20

SOURCES = [
    # -------------------------------------------------------
    # 1. SimplifyJobs — Summer 2026 main list
    #    Sections: SWE, PM, Data/AI/ML, Quant, Hardware
    #    Columns: Company(0), Role(1), Location(2), Apply(3), Age(4)
    # -------------------------------------------------------
    {
        "name": "SimplifyJobs/Summer2026-Internships",
        "tag": "🟢 SimplifyJobs · Summer 2026",
        "url": "https://github.com/SimplifyJobs/Summer2026-Internships/blob/dev/README.md",
        "top_n": 20,
        "skip_category_keywords": ["See Full List"],
        "columns": {
            "company": 0,
            "role": 1,
            "location": 2,
            "link_column": 3,
            "age": 4,
        },
    },
    # -------------------------------------------------------
    # 2. SimplifyJobs — Off-Season (Spring/Fall 2026)
    #    Same repo, separate README.  Extra 'Terms' col shifts
    #    Apply to col 4 and Age to col 5.
    #    Columns: Company(0), Role(1), Location(2), Terms(3), Apply(4), Age(5)
    # -------------------------------------------------------
    {
        "name": "SimplifyJobs/Summer2026-Internships (Off-Season)",
        "tag": "🟡 SimplifyJobs · Off-Season 2026",
        "url": "https://github.com/SimplifyJobs/Summer2026-Internships/blob/dev/README-Off-Season.md",
        "top_n": 20,
        "skip_category_keywords": ["See Full List"],
        "columns": {
            "company": 0,
            "role": 1,
            "location": 2,
            "link_column": 4,
            "age": 5,
        },
    },
    # -------------------------------------------------------
    # 3. negarprh — Canadian Tech Internships 2026
    #    Single table, no sub-categories.
    #    Columns: Company(0), Role(1), Location(2), Apply(3), Date(4)
    # -------------------------------------------------------
    {
        "name": "negarprh/Canadian-Tech-Internships-2026",
        "tag": "🍁 Canadian Tech · 2026",
        "url": "https://github.com/negarprh/Canadian-Tech-Internships-2026",
        "top_n": 20,
        "columns": {
            "company": 0,
            "role": 1,
            "location": 2,
            "link_column": 3,
            "age": 4,
        },
    },
    # -------------------------------------------------------
    # 4. speedyapply — 2026 SWE College Jobs (FAANG+ only)
    #    Only the 'FAANG+' h3 section is monitored.
    #    Extra Salary column; Apply is col 4, Age is col 5.
    #    Columns: Company(0), Position(1), Location(2), Salary(3), Apply(4), Age(5)
    # -------------------------------------------------------
    {
        "name": "speedyapply/2026-SWE-College-Jobs",
        "tag": "🚀 SpeedyApply · FAANG+ 2026",
        "url": "https://github.com/speedyapply/2026-SWE-College-Jobs",
        "top_n": 20,
        "include_sections": ["FAANG+"],
        "columns": {
            "company": 0,
            "role": 1,
            "location": 2,
            "salary": 3,
            "link_column": 4,
            "age": 5,
        },
    },
    # -------------------------------------------------------
    # 5. vanshb03 — Summer 2026 Tech Internships (main)
    #    The job table's closest previous heading is h3 "Legend"
    #    (not the h2 "The List 🚴🏔" further up). Skip promo headings.
    #    Columns: Company(0), Role(1), Location(2), Apply(3), Date(4)
    # -------------------------------------------------------
    {
        "name": "vanshb03/Summer2027-Internships",
        "tag": "⭐ Vansh+Ouckah · Summer 2026",
        "url": "https://github.com/vanshb03/Summer2027-Internships",
        "top_n": 20,
        "skip_category_keywords": ["Want notifications", "Summer 2026 Tech Internships"],
        "columns": {
            "company": 0,
            "role": 1,
            "location": 2,
            "link_column": 3,
            "age": 4,
        },
    },
    # -------------------------------------------------------
    # 6. vanshb03 — Spring & Fall 2026 Off-Season
    #    Same structure as source 5 (Legend h3 before table).
    #    Separate history — different source name key.
    #    Columns: Company(0), Role(1), Location(2), Apply(3), Date(4)
    # -------------------------------------------------------
    {
        "name": "vanshb03/Summer2027-Internships (Off-Season)",
        "tag": "🌀 Vansh+Ouckah · Spring/Fall 2026",
        "url": "https://github.com/vanshb03/Summer2027-Internships/blob/dev/OFFSEASON_README.md",
        "top_n": 20,
        "skip_category_keywords": ["Want notifications", "Spring & Fall 2026 Tech Internships"],
        "columns": {
            "company": 0,
            "role": 1,
            "location": 2,
            "link_column": 3,
            "age": 4,
        },
    },
]

STATE_FILE = "state.json"
MAX_TRACKED_PER_SOURCE = 20  # matches TOP_N — only ever need to remember the last N per category
