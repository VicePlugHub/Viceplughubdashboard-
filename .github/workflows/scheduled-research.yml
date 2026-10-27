"""Scheduled VicePlug Hub research collector.

Reads Google News RSS metadata, assigns a transparent heuristic priority score,
and appends de-duplicated records to a Google Sheets Research Feed worksheet.
It does not verify article claims or generate scripts.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
HEADERS = [
    "Title", "Source", "Source URL", "Indexed At", "Discovery Query",
    "Research Type", "Fact Status", "Review Status", "Notes",
    "Discovery Priority Score", "Discovery Priority Reasons", "Collected At (UTC)", "Collection Method",
]
DEFAULT_QUERIES = [
    '"GTA VI" OR "Grand Theft Auto VI"',
    '"GTA 6" Rockstar',
    'Rockstar Games GTA VI trailer gameplay map',
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def parse_date(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        value = parsedate_to_datetime(raw)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def priority_score(title: str, domain: str, date_text: str) -> Tuple[int, str]:
    """Explainable metadata-based ranking, not a model or virality prediction."""
    title_l = (title or "").lower()
    domain_l = (domain or "").lower().strip().removeprefix("www.")
    score = 35
    reasons: List[str] = []
    if "grand theft auto vi" in title_l or "grand theft auto 6" in title_l:
        score += 24; reasons.append("Strong GTA VI title match")
    elif "gta vi" in title_l:
        score += 22; reasons.append("Explicit GTA VI title match")
    elif "gta 6" in title_l:
        score += 18; reasons.append("GTA 6 title match")
    elif "rockstar" in title_l:
        score += 8; reasons.append("Rockstar-related headline")

    published = parse_date(date_text)
    if published:
        age_hours = max(0.0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
        if age_hours <= 24:
            score += 22; reasons.append("Date appears within 24 hours")
        elif age_hours <= 72:
            score += 15; reasons.append("Date appears within 3 days")
        elif age_hours <= 168:
            score += 8; reasons.append("Date appears within 7 days")
        else:
            reasons.append("Older than 7 days by supplied date")
    else:
        score += 3; reasons.append("Date unavailable; freshness is uncertain")

    signal_terms = ("official", "trailer", "gameplay", "release date", "release window", "confirmed", "launch", "pre-order", "preorder", "price", "map", "delay", "update", "rockstar games", "take-two")
    signal_hits = [term for term in signal_terms if term in title_l]
    if signal_hits:
        score += min(10, 3 + len(signal_hits))
        reasons.append("Specific news terms: " + ", ".join(signal_hits[:3]))

    official = ("rockstargames.com", "take2games.com")
    outlets = ("reuters.com", "bbc.com", "ign.com", "gamespot.com", "eurogamer.net", "videogameschronicle.com", "polygon.com", "pcgamer.com", "kotaku.com", "theverge.com", "axios.com", "gamesindustry.biz")
    if any(domain_l == d or domain_l.endswith("." + d) for d in official):
        score += 12; reasons.append("Official-domain candidate; verify the page")
    elif any(domain_l == d or domain_l.endswith("." + d) for d in outlets):
        score += 6; reasons.append("Known games/news outlet domain")

    cautious_terms = ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed", "fake", "hoax")
    cautious_hits = [term for term in cautious_terms if term in title_l]
    if cautious_hits:
        score -= 16; reasons.append("Caution terms: " + ", ".join(cautious_hits[:3]))
    score = max(10, min(95, score))
    return score, "; ".join(reasons or ["General GTA VI relevance; manual review needed"])


def article_type_hint(title: str, domain: str) -> str:
    t = (title or "").lower()
    d = (domain or "").lower().strip().removeprefix("www.")
    if d == "rockstargames.com" or d.endswith(".rockstargames.com") or d == "take2games.com" or d.endswith(".take2games.com"):
        return "Potential official source — verify"
    if any(x in t for x in ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed")):
        return "Claim/speculation terms detected — verify"
    return "News/reporting candidate — verify"


def fetch_rss(query: str, max_results: int) -> List[Dict[str, str]]:
    query = query.strip()
    rss_query = f"{query} when:7d"
    url = "https://news.google.com/rss/search?" + urlencode({"q": rss_query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; VicePlugHubResearchBot/1.0; contact: owner)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=25) as response:
                body = response.read()
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"RSS request failed for query {query!r}: {last_error}")

    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise RuntimeError(f"Google News RSS was not valid XML for {query!r}") from exc

    results: List[Dict[str, str]] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        source_node = item.find("source")
        source_name = (source_node.text or "").strip() if source_node is not None else ""
        publisher_url = source_node.attrib.get("url", "") if source_node is not None else ""
        domain = urlparse(publisher_url).netloc.lower().removeprefix("www.") if publisher_url else ""
        if not domain and url:
            domain = urlparse(url).netloc.lower().removeprefix("www.")
        if not title or not url.startswith(("https://", "http://")):
            continue
        score, reasons = priority_score(title, domain, published)
        pub_date = parse_date(published)
        published_display = pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else published
        publisher_display = source_name or domain or "Unknown publisher"
        results.append({
            "Title": title,
            "Source": domain or publisher_display,
            "Source URL": url,
            "Indexed At": published_display,
            "Discovery Query": query,
            "Research Type": article_type_hint(title, domain),
            "Fact Status": "Unverified — headline/metadata only",
            "Review Status": "Needs Review",
            "Notes": (
                f"Collected automatically from Google News RSS ({publisher_display}). "
                "Headline and metadata are not proof of the claim. Verify the original publisher article and corroborate important claims before scripting."
            ),
            "Discovery Priority Score": str(score),
            "Discovery Priority Reasons": reasons,
            "Collected At (UTC)": utc_now(),
            "Collection Method": "Scheduled Google News RSS",
        })
        if len(results) >= max_results:
            break
    return results


def credentials_from_env():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("Missing GitHub Actions secret GOOGLE_SERVICE_ACCOUNT_JSON.")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON must contain the full service-account JSON object.") from exc
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(credentials)


def ensure_capacity(ws, rows: int, cols: int) -> None:
    target_rows = max(int(ws.row_count), int(rows))
    target_cols = max(int(ws.col_count), int(cols))
    if target_rows != ws.row_count or target_cols != ws.col_count:
        ws.resize(rows=target_rows, cols=target_cols)


def collect_queries() -> List[str]:
    configured = os.environ.get("NEWS_QUERIES", "").strip()
    if not configured:
        return DEFAULT_QUERIES
    return [q.strip() for q in configured.split("||") if q.strip()] or DEFAULT_QUERIES


def main() -> int:
    sheet_id = (os.environ.get("GOOGLE_SHEET_ID") or os.environ.get("SPREADSHEET_ID") or "").strip()
    if not sheet_id:
        raise RuntimeError("Missing GitHub Actions secret GOOGLE_SHEET_ID (or SPREADSHEET_ID).")
    worksheet_name = os.environ.get("NEWS_RESEARCH_WORKSHEET", "Research Feed").strip() or "Research Feed"
    max_per_query = max(1, min(30, int(os.environ.get("NEWS_MAX_PER_QUERY", "15"))))

    client = credentials_from_env()
    book = client.open_by_key(sheet_id)
    try:
        ws = book.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = book.add_worksheet(title=worksheet_name, rows=1000, cols=len(HEADERS))
        ws.update("A1", [HEADERS], value_input_option="RAW")

    values = ws.get_all_values()
    if not values or not any(str(x).strip() for x in values[0]):
        ensure_capacity(ws, rows=max(1000, len(values) + 10), cols=len(HEADERS))
        ws.update("A1", [HEADERS], value_input_option="RAW")
        values = ws.get_all_values()
    headers = [str(h).strip() for h in values[0]]
    # Do not delete or rename existing columns. Add only the missing fields required by this collector.
    for heading in HEADERS:
        if heading.lower() not in [h.lower() for h in headers]:
            ensure_capacity(ws, rows=max(ws.row_count, 1000), cols=len(headers) + 1)
            ws.update_cell(1, len(headers) + 1, heading)
            headers.append(heading)

    values = ws.get_all_values()
    headers = [str(h).strip() for h in values[0]]
    indexes = {h.lower(): i for i, h in enumerate(headers)}
    def index_for(name: str) -> int:
        return indexes[name.lower()]

    existing_urls, existing_titles = set(), set()
    url_i = index_for("Source URL")
    title_i = index_for("Title")
    for row in values[1:]:
        if len(row) > url_i and row[url_i].strip():
            existing_urls.add(row[url_i].strip().rstrip("/").lower())
        if len(row) > title_i and row[title_i].strip():
            existing_titles.add(re.sub(r"\s+", " ", row[title_i].strip().lower()))

    queries = collect_queries()
    all_items: List[Dict[str, str]] = []
    errors = []
    for query in queries:
        try:
            items = fetch_rss(query, max_per_query)
            print(f"Query {query!r}: {len(items)} candidate results")
            all_items.extend(items)
        except Exception as exc:
            errors.append(str(exc))
            print(f"WARNING: {exc}")
        time.sleep(1.0)

    # Deduplicate current run by title and URL, preferring first occurrence.
    unique_items = []
    run_urls, run_titles = set(), set()
    for item in all_items:
        url_key = item["Source URL"].rstrip("/").lower()
        title_key = re.sub(r"\s+", " ", item["Title"].strip().lower())
        if url_key in run_urls or title_key in run_titles:
            continue
        run_urls.add(url_key); run_titles.add(title_key)
        unique_items.append(item)

    rows_to_add = []
    skipped = 0
    for item in unique_items:
        url_key = item["Source URL"].rstrip("/").lower()
        title_key = re.sub(r"\s+", " ", item["Title"].strip().lower())
        if url_key in existing_urls or title_key in existing_titles:
            skipped += 1
            continue
        row = [""] * len(headers)
        for key, value in item.items():
            idx = indexes.get(key.lower())
            if idx is not None:
                row[idx] = str(value)
        rows_to_add.append(row)
        existing_urls.add(url_key); existing_titles.add(title_key)

    if rows_to_add:
        ensure_capacity(ws, rows=len(values) + len(rows_to_add), cols=len(headers))
        ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")
    print(f"Finished: {len(rows_to_add)} new records added, {skipped} duplicates skipped, {len(unique_items)} unique candidates. Worksheet: {worksheet_name}.")
    if errors and not rows_to_add:
        raise RuntimeError("All scheduled discovery queries failed: " + " | ".join(errors))
    if not unique_items and not errors:
        print("No items matched this run. No existing rows were changed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
