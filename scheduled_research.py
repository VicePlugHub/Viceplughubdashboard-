"""Scheduled VicePlug Hub research collector.

Collects GTA VI-related headline metadata from direct gaming-publisher RSS feeds
and Rockstar's official Newswire page, assigns an explainable priority score,
and appends de-duplicated records to a Google Sheets Research Feed worksheet.

This collector does not verify article claims or generate scripts.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Dict, List, Tuple, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
HEADERS = [
    "Title", "Source", "Source URL", "Indexed At", "Discovery Query",
    "Research Type", "Fact Status", "Review Status", "Notes",
    "Discovery Priority Score", "Discovery Priority Reasons", "Collected At (UTC)", "Collection Method",
]

# These are direct publisher feeds, rather than the Google News RSS search endpoint
# that returned HTTP 503 in the user's scheduled GitHub Actions run.
PUBLISHER_FEEDS = [
    ("IGN", "https://www.ign.com/rss/v2/articles/feed"),
    ("PC Gamer", "https://www.pcgamer.com/feeds.xml"),
    ("GameSpot", "https://www.gamespot.com/feeds/news/"),
    ("Eurogamer", "https://www.eurogamer.net/feed/news"),
    ("GamesRadar+", "https://www.gamesradar.com/feeds.xml"),
    ("VG247", "https://www.vg247.com/feed/articles"),
    ("Rock Paper Shotgun", "https://www.rockpapershotgun.com/feed"),
]
ROCKSTAR_NEWSWIRE_URL = "https://www.rockstargames.com/newswire/"
USER_AGENT = "Mozilla/5.0 (compatible; VicePlugHubResearchBot/2.0)"
GTA_TERMS = (
    "gta vi", "gta 6", "grand theft auto vi", "grand theft auto 6", "grand theft auto six"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def parse_date(raw: str) -> Optional[datetime]:
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
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%dT%H%M%SZ", "%Y-%m-%d %H:%M UTC", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def plain_text(raw: str) -> str:
    """Strip markup from RSS descriptions without requiring another dependency."""
    class _TextParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts: List[str] = []
        def handle_data(self, data: str) -> None:
            self.parts.append(data)
    parser = _TextParser()
    try:
        parser.feed(html.unescape(raw or ""))
        return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    except Exception:
        return re.sub(r"\s+", " ", html.unescape(raw or "")).strip()


def is_gta_vi_relevant(title: str, description: str = "") -> bool:
    text = f"{title} {description}".lower()
    return any(term in text for term in GTA_TERMS) or bool(re.search(r"\bgta\s*(?:vi|6)\b", text))


def priority_score(title: str, domain: str, date_text: str) -> Tuple[int, str]:
    """Explainable headline/metadata ranking, not a model or virality prediction."""
    title_l = (title or "").lower()
    domain_l = (domain or "").lower().strip().removeprefix("www.")
    score = 35
    reasons: List[str] = []
    if "grand theft auto vi" in title_l or "grand theft auto 6" in title_l:
        score += 24; reasons.append("Strong Grand Theft Auto title match")
    elif "gta vi" in title_l:
        score += 22; reasons.append("Explicit GTA VI title match")
    elif "gta 6" in title_l:
        score += 18; reasons.append("GTA 6 title match")
    else:
        reasons.append("GTA VI reference appears in article metadata")

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

    signal_terms = (
        "official", "trailer", "gameplay", "release date", "release window", "confirmed",
        "launch", "pre-order", "preorder", "price", "map", "delay", "update", "take-two"
    )
    signal_hits = [term for term in signal_terms if term in title_l]
    if signal_hits:
        score += min(10, 3 + len(signal_hits))
        reasons.append("Specific news terms: " + ", ".join(signal_hits[:3]))

    official = ("rockstargames.com", "take2games.com")
    outlets = (
        "ign.com", "pcgamer.com", "gamespot.com", "eurogamer.net", "gamesradar.com",
        "vg247.com", "rockpapershotgun.com", "videogameschronicle.com", "polygon.com",
        "kotaku.com", "theverge.com", "axios.com", "gamesindustry.biz"
    )
    if any(domain_l == d or domain_l.endswith("." + d) for d in official):
        score += 12; reasons.append("Official-domain candidate; verify the page")
    elif any(domain_l == d or domain_l.endswith("." + d) for d in outlets):
        score += 6; reasons.append("Recognized gaming/news publisher domain")

    cautious_terms = ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed", "fake", "hoax")
    caution_hits = [term for term in cautious_terms if term in title_l]
    if caution_hits:
        score -= 16; reasons.append("Caution terms: " + ", ".join(caution_hits[:3]))
    return max(10, min(95, score)), "; ".join(reasons)


def article_type_hint(title: str, domain: str) -> str:
    t = (title or "").lower()
    d = (domain or "").lower().strip().removeprefix("www.")
    if d == "rockstargames.com" or d.endswith(".rockstargames.com") or d == "take2games.com" or d.endswith(".take2games.com"):
        return "Potential official source — verify"
    if any(x in t for x in ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed")):
        return "Claim/speculation terms detected — verify"
    return "News/reporting candidate — verify"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, names: Tuple[str, ...]) -> str:
    for child in list(element):
        if _local_name(child.tag) in names:
            if _local_name(child.tag) == "link":
                href = child.attrib.get("href", "").strip()
                if href:
                    return href
            if child.text:
                return child.text.strip()
    return ""


def _fetch_bytes(url: str, timeout: int = 18, attempts: int = 2) -> bytes:
    last_error: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html, */*",
            })
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
                if not body:
                    raise RuntimeError("empty response")
                return body
        except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"request failed for {url}: {last_error}")


def make_record(title: str, url: str, published: str, source_name: str, publisher_domain: str, method: str, query: str, description: str = "") -> Dict[str, str]:
    domain = urlparse(url).netloc.lower().removeprefix("www.") or publisher_domain
    score, reasons = priority_score(title, domain, published)
    pub_date = parse_date(published)
    published_display = pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else (published or "")
    summary = plain_text(description)[:700]
    extra = (f" Feed description: {summary}" if summary else "")
    return {
        "Title": title.strip(),
        "Source": source_name or domain or "Unknown publisher",
        "Source URL": url.strip(),
        "Indexed At": published_display,
        "Discovery Query": query,
        "Research Type": article_type_hint(title, domain),
        "Fact Status": "Unverified — headline/metadata only",
        "Review Status": "Needs Review",
        "Notes": (
            f"Collected automatically from {method}. Headline/feed metadata are not proof of the claim. "
            "Open the original publisher page and corroborate important claims before scripting." + extra
        ),
        "Discovery Priority Score": str(score),
        "Discovery Priority Reasons": reasons,
        "Collected At (UTC)": utc_now(),
        "Collection Method": method,
    }


def fetch_publisher_feed(name: str, feed_url: str, max_results: int) -> Tuple[List[Dict[str, str]], int]:
    """Fetch one publisher feed; return matching records and number of parsed entries."""
    body = _fetch_bytes(feed_url)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise RuntimeError(f"feed was not valid XML: {feed_url}") from exc

    entries: List[ET.Element] = []
    for element in root.iter():
        if _local_name(element.tag) in ("item", "entry"):
            entries.append(element)

    found: List[Dict[str, str]] = []
    feed_domain = urlparse(feed_url).netloc.lower().removeprefix("www.")
    for entry in entries:
        title = plain_text(_child_text(entry, ("title",)))
        link = _child_text(entry, ("link", "guid"))
        if link and not link.startswith(("http://", "https://")):
            # Relative URLs are unusual in RSS, but can occur in Atom feeds.
            from urllib.parse import urljoin
            link = urljoin(feed_url, link)
        date_text = _child_text(entry, ("pubdate", "published", "updated", "date"))
        description = _child_text(entry, ("description", "summary", "content", "encoded"))
        if not title or not link.startswith(("https://", "http://")):
            continue
        if not is_gta_vi_relevant(title, plain_text(description)):
            continue
        found.append(make_record(
            title=title, url=link, published=date_text, source_name=name,
            publisher_domain=feed_domain, method=f"Scheduled publisher RSS ({name})",
            query=f"GTA VI keyword scan via {name} RSS", description=description,
        ))
        if len(found) >= max_results:
            break
    return found, len(entries)


class _AnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results: List[Tuple[str, str]] = []
        self._href: Optional[str] = None
        self._parts: List[str] = []
        self._depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            if self._depth == 0:
                self._href = dict(attrs).get("href", "")
                self._parts = []
            self._depth += 1

    def handle_data(self, data: str) -> None:
        if self._depth > 0:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._depth > 0:
            self._depth -= 1
            if self._depth == 0:
                text = re.sub(r"\s+", " ", " ".join(self._parts)).strip()
                if self._href and text:
                    self.results.append((text, self._href))
                self._href = None
                self._parts = []


def fetch_rockstar_newswire(max_results: int) -> Tuple[List[Dict[str, str]], int]:
    """Lightly parse visible article links from Rockstar's public Newswire page."""
    from urllib.parse import urljoin
    body = _fetch_bytes(ROCKSTAR_NEWSWIRE_URL)
    text = body.decode("utf-8", errors="replace")
    parser = _AnchorCollector()
    parser.feed(text)
    host = urlparse(ROCKSTAR_NEWSWIRE_URL).netloc
    found: List[Dict[str, str]] = []
    seen_urls = set()
    for title_raw, href in parser.results:
        title = plain_text(title_raw)
        url = urljoin(ROCKSTAR_NEWSWIRE_URL, href)
        parsed = urlparse(url)
        if parsed.netloc.lower() != host or not parsed.path.startswith("/newswire/"):
            continue
        if not title or not is_gta_vi_relevant(title):
            continue
        key = url.split("#", 1)[0].rstrip("/").lower()
        if key in seen_urls:
            continue
        seen_urls.add(key)
        found.append(make_record(
            title=title, url=url, published="", source_name="Rockstar Games Newswire",
            publisher_domain="rockstargames.com", method="Scheduled official Newswire page",
            query="GTA VI keyword scan via Rockstar Newswire",
        ))
        if len(found) >= max_results:
            break
    return found, len(parser.results)


def fetch_gdelt(max_results: int) -> Tuple[List[Dict[str, str]], int]:
    """Query GDELT once as an additional provider, respecting its cooldown on 429."""
    query = '"GTA VI" OR "GTA 6" OR "Grand Theft Auto VI" OR "Grand Theft Auto 6"'
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode({
        "query": query,
        "mode": "artlist",
        "format": "json",
        "timespan": "7d",
        "maxrecords": str(min(250, max_results * 5)),
        "sort": "datedesc",
    })
    last_error: Optional[Exception] = None
    body = b""
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(request, timeout=25) as response:
                body = response.read()
            break
        except HTTPError as exc:
            last_error = exc
            # GDELT asks callers to space requests; cool down instead of hammering it.
            if exc.code == 429 and attempt < 2:
                wait_seconds = 6 if attempt == 0 else 10
                print(f"GDELT rate-limited this run; waiting {wait_seconds}s before retry.")
                time.sleep(wait_seconds)
            elif exc.code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
            else:
                break
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
    else:
        pass
    if not body:
        raise RuntimeError(f"GDELT request failed: {last_error}")
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("GDELT returned a non-JSON response") from exc
    articles = payload.get("articles", []) if isinstance(payload, dict) else []
    if not isinstance(articles, list):
        raise RuntimeError("GDELT response did not contain an articles list")

    found: List[Dict[str, str]] = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = plain_text(str(article.get("title", "")))
        link = str(article.get("url", "")).strip()
        domain = str(article.get("domain", "")).strip().lower().removeprefix("www.")
        date_text = str(article.get("seendate", "")).strip()
        if not title or not link.startswith(("https://", "http://")):
            continue
        if not is_gta_vi_relevant(title):
            continue
        found.append(make_record(
            title=title, url=link, published=date_text, source_name=domain or "GDELT indexed publisher",
            publisher_domain=domain, method="Scheduled GDELT News Index",
            query="GDELT: GTA VI terms over the last 7 days",
        ))
        if len(found) >= max_results:
            break
    return found, len(articles)


def credentials_from_env():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("Missing GitHub Actions secret GOOGLE_SERVICE_ACCOUNT_JSON.")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON must contain the full service-account JSON object.") from exc
    if not isinstance(info, dict) or not info.get("client_email") or not info.get("private_key"):
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is missing client_email or private_key.")
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(credentials)


def ensure_capacity(ws, rows: int, cols: int) -> None:
    target_rows = max(int(ws.row_count), int(rows))
    target_cols = max(int(ws.col_count), int(cols))
    if target_rows != ws.row_count or target_cols != ws.col_count:
        ws.resize(rows=target_rows, cols=target_cols)


def gather_candidates(max_per_source: int) -> Tuple[List[Dict[str, str]], List[str], int]:
    all_items: List[Dict[str, str]] = []
    errors: List[str] = []
    successful_sources = 0

    # Direct publisher feeds are attempted independently so one outage doesn't stop discovery.
    for name, feed_url in PUBLISHER_FEEDS:
        try:
            items, parsed_entries = fetch_publisher_feed(name, feed_url, max_per_source)
            successful_sources += 1
            print(f"Source {name}: feed reachable, parsed {parsed_entries} entries, {len(items)} GTA VI candidates")
            all_items.extend(items)
        except Exception as exc:
            message = f"{name} RSS: {exc}"
            errors.append(message)
            print(f"WARNING: {message}")
        time.sleep(0.4)

    # Always include a separate attempt at Rockstar's official Newswire page.
    try:
        items, link_count = fetch_rockstar_newswire(max_per_source)
        successful_sources += 1
        print(f"Rockstar Newswire: page reachable, inspected {link_count} links, {len(items)} GTA VI candidates")
        all_items.extend(items)
    except Exception as exc:
        message = f"Rockstar Newswire: {exc}"
        errors.append(message)
        print(f"WARNING: {message}")

    # Additional broad index fallback. It is one request per run (not one per query),
    # and its 429 handling uses a cooldown before retrying.
    try:
        items, article_count = fetch_gdelt(max_per_source * 3)
        successful_sources += 1
        print(f"GDELT: index returned {article_count} articles, {len(items)} GTA VI candidates")
        all_items.extend(items)
    except Exception as exc:
        message = f"GDELT: {exc}"
        errors.append(message)
        print(f"WARNING: {message}")

    return all_items, errors, successful_sources


def main() -> int:
    sheet_id = (os.environ.get("GOOGLE_SHEET_ID") or os.environ.get("SPREADSHEET_ID") or "").strip()
    if not sheet_id:
        raise RuntimeError("Missing GitHub Actions secret GOOGLE_SHEET_ID (or SPREADSHEET_ID).")
    worksheet_name = os.environ.get("NEWS_RESEARCH_WORKSHEET", "Research Feed").strip() or "Research Feed"
    max_per_source = max(1, min(40, int(os.environ.get("NEWS_MAX_PER_SOURCE", os.environ.get("NEWS_MAX_PER_QUERY", "15")))))

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
    for heading in HEADERS:
        if heading.lower() not in [h.lower() for h in headers]:
            ensure_capacity(ws, rows=max(ws.row_count, 1000), cols=len(headers) + 1)
            ws.update_cell(1, len(headers) + 1, heading)
            headers.append(heading)

    values = ws.get_all_values()
    headers = [str(h).strip() for h in values[0]]
    indexes = {h.lower(): i for i, h in enumerate(headers)}
    if "source url" not in indexes or "title" not in indexes:
        raise RuntimeError("Research Feed must contain Title and Source URL headers.")

    existing_urls, existing_titles = set(), set()
    url_i, title_i = indexes["source url"], indexes["title"]
    for row in values[1:]:
        if len(row) > url_i and row[url_i].strip():
            existing_urls.add(row[url_i].strip().rstrip("/").lower())
        if len(row) > title_i and row[title_i].strip():
            existing_titles.add(re.sub(r"\s+", " ", row[title_i].strip().lower()))

    all_items, errors, successful_sources = gather_candidates(max_per_source)
    # Deduplicate this run by normalized URL and title, preferring earliest source in the list.
    unique_items: List[Dict[str, str]] = []
    run_urls, run_titles = set(), set()
    for item in all_items:
        url_key = item["Source URL"].rstrip("/").lower()
        title_key = re.sub(r"\s+", " ", item["Title"].strip().lower())
        if url_key in run_urls or title_key in run_titles:
            continue
        run_urls.add(url_key)
        run_titles.add(title_key)
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
        existing_urls.add(url_key)
        existing_titles.add(title_key)

    if rows_to_add:
        ensure_capacity(ws, rows=len(values) + len(rows_to_add), cols=len(headers))
        ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")

    print(
        f"Finished: {len(rows_to_add)} new records added, {skipped} duplicates skipped, "
        f"{len(unique_items)} unique candidates. Sources reachable: {successful_sources}/{len(PUBLISHER_FEEDS) + 2}. "
        f"Worksheet: {worksheet_name}."
    )
    if successful_sources == 0:
        joined = " | ".join(errors) if errors else "No source responded successfully."
        raise RuntimeError("All scheduled discovery sources failed: " + joined)
    if errors:
        print(f"NOTE: {len(errors)} source(s) were unavailable; successful sources were still processed.")
    if not unique_items:
        print("No GTA VI-related candidates found in the publisher feeds checked. Existing rows were not changed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
