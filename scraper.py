import hashlib
import os
import re
import requests
from bs4 import BeautifulSoup
from config import TOP_N


def _build_headers() -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/vnd.github.html+json",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

SKIP_COMPANIES = {"---", "↳", "", "<!-- -->"}


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    cleaned = url.strip()
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


def _github_blob_to_api_url(url: str) -> str:
    # blob path: /owner/repo/blob/branch/path/to/file.md
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url
    )
    if match:
        owner, repo, branch, path = match.groups()
        return f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

    # branch root: /owner/repo/tree/branch
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/?", url
    )
    if match:
        owner, repo, branch = match.groups()
        return f"https://api.github.com/repos/{owner}/{repo}/contents/README.md?ref={branch}"

    # repo root: /owner/repo
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)/?", url
    )
    if match:
        owner, repo = match.groups()
        return f"https://api.github.com/repos/{owner}/{repo}/readme"

    return url


def _extract_apply_url(cell) -> str:
    for a in cell.find_all("a", href=True):
        if a.find("img", alt="Apply"):
            return a["href"]
    a = cell.find("a", href=True)
    return a["href"] if a else ""


def fetch_listings(source: dict) -> list[dict]:
    """
    Returns listings grouped by category. Each listing has a 'category' field.
    Only the top TOP_N rows per category are returned (list is newest-first).
    """
    api_url = _github_blob_to_api_url(source["url"])
    response = requests.get(api_url, headers=_build_headers(), timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    col = source["columns"]
    max_col_index = max(col["company"], col["role"], col["location"], col["link_column"])

    listings = []

    top_n = source.get("top_n", TOP_N)

    skip_keywords = source.get("skip_category_keywords", [])
    include_sections = source.get("include_sections", [])  # whitelist; empty = all

    # Walk each table and map it to its closest previous heading as category
    for table in soup.find_all("table"):
        heading = table.find_previous(
            ["h1", "h2", "h3", "h4", "h5", "h6"],
            class_="heading-element",
        )
        category = heading.get_text(strip=True) if heading else "General"
        if any(keyword in category for keyword in skip_keywords):
            continue
        if include_sections and not any(s in category for s in include_sections):
            continue

        rows = table.select("tbody tr")[:top_n]
        for row in rows:
            cells = row.find_all("td")
            if not cells or len(cells) <= max_col_index:
                continue

            company = cells[col["company"]].get_text(strip=True)
            role = cells[col["role"]].get_text(strip=True)
            location = cells[col["location"]].get_text(strip=True)

            if not company or company in SKIP_COMPANIES or company.startswith("↳"):
                continue

            url = _extract_apply_url(cells[col["link_column"]])

            age = ""
            if "age" in col and len(cells) > col["age"]:
                age = cells[col["age"]].get_text(strip=True)

            salary = ""
            if "salary" in col and len(cells) > col["salary"]:
                salary = cells[col["salary"]].get_text(strip=True)

            # Prefer apply URL for a stable ID because table text (role/location/age)
            # can be edited frequently without meaning a truly new posting.
            identity = _normalize_url(url) or f"{company}|{role}|{location}"
            listing_id = hashlib.md5(f"{source['name']}|{category}|{identity}".encode()).hexdigest()
            legacy_id = hashlib.md5(f"{company}|{role}|{location}".encode()).hexdigest()
            listings.append({
                "id": listing_id,
                "legacy_id": legacy_id,
                "company": company,
                "role": role,
                "location": location,
                "url": url,
                "age": age,
                "salary": salary,
                "category": category,
                "source": source["name"],
                "tag": source.get("tag", source["name"]),
            })

    return listings

