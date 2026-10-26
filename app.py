"""VicePlug Hub — GTA VI research and content operations dashboard.

Designed for Streamlit Community Cloud. Connects to Google Sheets and Groq
when credentials are supplied in Streamlit Secrets.
"""

import json
import os
import html
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# -----------------------------------------------------------------------------
# Page configuration and visual system
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VicePlug Hub | GTA VI Intelligence",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {
  --bg:#060913; --surface:#0b1221; --card:#0e1729; --border:#202c43;
  --pink:#ff2e93; --purple:#a855f7; --cyan:#38d9f5; --green:#10b981;
  --amber:#f59e0b; --text:#f8fafc; --muted:#93a4bd; --dim:#64748b;
}
html, body, [class*="css"] { font-family:'Plus Jakarta Sans',sans-serif; }
.stApp { background:radial-gradient(ellipse at 70% -10%, rgba(93,25,105,.22), transparent 42%), var(--bg); color:var(--text); }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:rgba(6,9,19,.85); }
.block-container { max-width:1600px; padding:1.2rem 1.5rem 2.5rem; }
/* Widget styling */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
  background:#0c1424 !important; border-color:#26344c !important; border-radius:10px !important;
}
.stButton > button, .stDownloadButton > button {
  border-radius:10px; border:1px solid #2a3851; background:#101a2d; color:#e8eef8;
  font-weight:650; transition:all .18s ease; min-height:2.45rem;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color:var(--purple); color:white; background:#17152c; }
button[kind="primary"] { background:linear-gradient(110deg,#e51d83,#8b36d7) !important; border:0 !important; color:#fff !important; }
.stAlert { border-radius:10px; }
.vp-brand { font-family:'Space Grotesk',sans-serif; font-size:1.22rem; font-weight:800; letter-spacing:-.04em; margin:.2rem 0 1.25rem; color:#fff; }
.vp-brand span { color:var(--pink); }
.vp-eyebrow { font-size:.68rem; font-weight:800; letter-spacing:.16em; color:#b7a2d7; text-transform:uppercase; }
.vp-hero { border:1px solid #3b2450; border-radius:18px; padding:27px 30px; margin-bottom:20px;
  background:radial-gradient(ellipse at 85% 20%,rgba(255,46,147,.17),transparent 42%),linear-gradient(125deg,#10172b,#25102f 62%,#3d1031); }
.vp-hero h1 { font-family:'Space Grotesk',sans-serif; font-size:clamp(1.8rem,3vw,2.55rem); line-height:1.08; letter-spacing:-.045em; margin:.55rem 0 .65rem; }
.vp-hero h1 span { color:var(--pink); }
.vp-hero p { color:#a9b7cd; max-width:760px; font-size:.92rem; margin-bottom:0; }
.vp-page-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; border-bottom:1px solid #1d2940; padding:0 0 1rem; margin:0 0 1.15rem; }
.vp-page-head h1 { font-family:'Space Grotesk',sans-serif; font-size:1.75rem; margin:0; letter-spacing:-.04em; }
.vp-page-head p { color:var(--muted); margin:.3rem 0 0; font-size:.88rem; }
.vp-card { background:linear-gradient(145deg,#10192b,#0b1220); border:1px solid var(--border); border-radius:14px; padding:16px; min-height:108px; }
.vp-metric-label { color:var(--muted); font-size:.76rem; font-weight:600; }
.vp-metric-value { font-family:'Space Grotesk',sans-serif; font-size:1.85rem; font-weight:700; margin:.35rem 0 .1rem; color:#fff; }
.vp-metric-note { color:var(--dim); font-size:.72rem; }
.vp-panel { background:#0a1120; border:1px solid var(--border); border-radius:14px; padding:16px; margin-bottom:12px; }
.vp-panel-title { font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:700; margin:0 0 .25rem; }
.vp-muted { color:var(--muted); font-size:.84rem; }
.vp-pill { display:inline-block; border:1px solid #3b2a56; color:#e4c5ff; background:#21132e; border-radius:99px; padding:3px 9px; font-size:.7rem; font-weight:700; }
.vp-empty { text-align:center; padding:28px 16px; border:1px dashed #2a3851; border-radius:14px; color:var(--muted); background:rgba(14,23,41,.35); }
[data-testid="stDataFrame"] { border:1px solid #1e293b; border-radius:10px; overflow:hidden; }
@media (max-width: 850px) { .block-container { padding:.7rem .75rem 2rem; } .vp-hero { padding:21px; } .vp-page-head h1 { font-size:1.45rem; } }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Configuration / integrations
# -----------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Research Feed", "📰"),
    ("Viral Opportunities", "🎯"),
    ("Video Discovery", "🎥"),
    ("AI Studio", "🧠"),
    ("Script Generator", "📝"),
    ("Content Pipeline", "⚡"),
    ("Review Queue", "☑️"),
    ("Trends & Analytics", "📈"),
    ("Google Sheets Sync", "📊"),
    ("Settings", "⚙️"),
]

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if "generated_script" not in st.session_state:
    st.session_state.generated_script = None


def get_secret(name: str, default: Any = None) -> Any:
    """Read a value from Streamlit Secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, default)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def get_service_account_info() -> Optional[Dict[str, Any]]:
    """Support the usual Streamlit [gcp_service_account] block or JSON secret."""
    try:
        info = st.secrets.get("gcp_service_account")
        if info and hasattr(info, "items"):
            return dict(info)
    except Exception:
        pass
    raw = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        try:
            return json.loads(raw) if isinstance(raw, str) else dict(raw)
        except Exception:
            return None
    return None


def open_spreadsheet():
    if not HAS_GSPREAD:
        raise RuntimeError("Google Sheets packages are missing. Add gspread and google-auth to requirements.txt.")
    account_info = get_service_account_info()
    local_key_file = get_secret("GOOGLE_SERVICE_ACCOUNT_FILE")
    if account_info:
        credentials = Credentials.from_service_account_info(account_info, scopes=SCOPES)
        client = gspread.authorize(credentials)
    elif local_key_file and os.path.exists(str(local_key_file)):
        client = gspread.service_account(filename=str(local_key_file), scopes=SCOPES)
    else:
        raise RuntimeError("Google credentials are not configured in Streamlit Secrets.")

    sheet_id = get_secret("GOOGLE_SHEET_ID") or get_secret("SPREADSHEET_ID")
    sheet_name = get_secret("GOOGLE_SHEET_NAME") or get_secret("SPREADSHEET_NAME")
    if sheet_id:
        return client.open_by_key(str(sheet_id))
    if sheet_name:
        return client.open(str(sheet_name))
    raise RuntimeError("Set GOOGLE_SHEET_ID or GOOGLE_SHEET_NAME in Streamlit Secrets.")


def load_sheet_records() -> Tuple[pd.DataFrame, Any, str, str]:
    """Load a research worksheet. Returns dataframe, worksheet, message, status."""
    try:
        book = open_spreadsheet()
        preferred = str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))
        candidates = [preferred, "Research Feed", "AI Analysis", "Clip Queue", "Sheet1"]
        worksheet = None
        last_error = None
        for name in dict.fromkeys(candidates):
            try:
                worksheet = book.worksheet(name)
                break
            except Exception as exc:
                last_error = exc
        if worksheet is None:
            names = [ws.title for ws in book.worksheets()]
            if not names:
                return pd.DataFrame(), None, "The spreadsheet has no worksheets.", "empty"
            return pd.DataFrame(), None, "Could not find a research worksheet. Available tabs: " + ", ".join(names), "missing_tab"
        values = worksheet.get_all_values()
        if not values:
            return pd.DataFrame(), worksheet, f"Connected to {book.title} / {worksheet.title}, but the tab is empty.", "empty"
        headers = [str(h).strip() for h in values[0]]
        if not any(headers):
            return pd.DataFrame(), worksheet, f"The first row of {worksheet.title} must contain column headers.", "empty"
        # Prevent duplicate/blank column headings from breaking pandas operations.
        seen: Dict[str, int] = {}
        clean_headers = []
        for i, name in enumerate(headers):
            base = name or f"Column {i + 1}"
            seen[base] = seen.get(base, 0) + 1
            clean_headers.append(base if seen[base] == 1 else f"{base} ({seen[base]})")
        rows = values[1:]
        width = len(clean_headers)
        rows = [(row + [""] * max(0, width - len(row)))[:width] for row in rows]
        df = pd.DataFrame(rows, columns=clean_headers)
        df.insert(0, "_sheet_row", range(2, len(df) + 2))
        # Drop fully empty records but keep the original row number for safe updates.
        if len(df):
            visible_cols = [c for c in df.columns if c != "_sheet_row"]
            nonempty = df[visible_cols].astype(str).apply(lambda r: any(v.strip() for v in r), axis=1)
            df = df.loc[nonempty].reset_index(drop=True)
        return df, worksheet, f"Connected: {book.title} → {worksheet.title} · {len(df)} records", "connected"
    except Exception as exc:
        return pd.DataFrame(), None, str(exc), "error"


def first_matching_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    # Loose fallback only after exact variants fail.
    # Prefer the most specific phrase first (e.g. "Review Status" before "Status").
    for candidate in sorted(candidates, key=len, reverse=True):
        candidate = candidate.lower()
        for column in df.columns:
            normalized = str(column).strip().lower()
            if candidate in normalized:
                return column
    return None


def title_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["Title", "Video Title", "Topic", "Video", "Story Title", "Name"])


def url_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["Video URL", "Source URL", "YouTube URL", "URL", "Link", "Source Link"])


def score_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["AI Priority Score", "Priority Score", "Viral Score", "Priority", "Score"])


def status_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["Review Status", "Pipeline Status", "Content Status", "Status"])


def fact_column(df: pd.DataFrame) -> Optional[str]:
    return first_matching_column(df, ["AI Fact Status", "Fact Status", "Verification Status"])


def number_value(value: Any) -> Optional[float]:
    try:
        text = str(value).strip().replace("%", "").replace(",", "")
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def sorted_by_score(df: pd.DataFrame) -> pd.DataFrame:
    col = score_column(df)
    if not col:
        return df.copy()
    output = df.copy()
    output["_numeric_score"] = output[col].apply(number_value)
    return output.sort_values("_numeric_score", ascending=False, na_position="last")


def clean_display_df(df: pd.DataFrame, max_cols: int = 9) -> pd.DataFrame:
    output = df.drop(columns=[c for c in ["_sheet_row"] if c in df.columns], errors="ignore").copy()
    return output.iloc[:, :max_cols]


def safe_text(value: Any, limit: int = 160) -> str:
    result = html.escape(str(value or "").strip())
    return result if len(result) <= limit else result[:limit - 1] + "…"


def call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 1600) -> Dict[str, Any]:
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in Streamlit Secrets.")
    if not HAS_GROQ:
        raise RuntimeError("The groq package is missing. Add groq to requirements.txt.")
    model = str(get_secret("GROQ_MODEL", "openai/gpt-oss-20b"))
    client = Groq(api_key=str(api_key))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=max_tokens,
        temperature=0.4,
    )
    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # A visible error is better than silently treating malformed output as valid.
        raise RuntimeError("Groq returned text that was not valid JSON. Try again or use a shorter source note.")


def render_page_header(title: str, subtitle: str, eyebrow: str = "VICEPLUG HUB") -> None:
    st.markdown(
        f'<div class="vp-page-head"><div><div class="vp-eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>'
        f'<span class="vp-pill">GTA VI · CREATOR WORKSPACE</span></div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str, emoji: str, accent: str) -> None:
    st.markdown(
        f'<div class="vp-card"><div style="display:flex;align-items:center;gap:9px">'
        f'<span style="width:30px;height:30px;display:grid;place-items:center;border-radius:50%;background:{accent}22">{emoji}</span>'
        f'<span class="vp-metric-label">{html.escape(label)}</span></div>'
        f'<div class="vp-metric-value">{html.escape(value)}</div>'
        f'<div class="vp-metric-note">{html.escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def show_missing_data(message: str = "Connect Google Sheets to show your real research records here.") -> None:
    st.markdown(f'<div class="vp-empty"><div style="font-size:1.5rem">🗂️</div><b>No research data loaded</b><br><span>{html.escape(message)}</span></div>', unsafe_allow_html=True)


def save_ai_brief_to_worksheet(worksheet_name: str, sheet_row: int, result: Dict[str, Any]) -> str:
    """Persist an AI brief into clearly named columns on the matching research row."""
    book = open_spreadsheet()
    ws = book.worksheet(worksheet_name)
    headers = [str(h).strip() for h in ws.row_values(1)]
    if not headers:
        raise RuntimeError(f"Worksheet '{worksheet_name}' has no header row.")

    fields = {
        "AI Relevance": "relevance",
        "AI Priority Score": "priority_score",
        "AI Fact Status": "fact_status",
        "AI Summary": "summary",
        "AI Why It Matters": "why_it_matters",
        "AI Hook": "hook",
        "AI Commentary Draft": "commentary_draft",
        "AI On-Screen Text": "on_screen_text",
        "AI Title": "title",
        "AI Caption": "caption",
        "AI Hashtags": "hashtags",
        "AI Verification Needed": "verification_needed",
        "AI Rights Note": "rights_note",
        "AI Recommended Action": "recommended_action",
        "AI Last Analyzed (UTC)": "_timestamp",
    }
    for heading in fields:
        if heading.lower() not in [h.lower() for h in headers]:
            ws.update_cell(1, len(headers) + 1, heading)
            headers.append(heading)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    for heading, key in fields.items():
        idx = next(i for i, h in enumerate(headers) if h.lower() == heading.lower())
        value = now if key == "_timestamp" else result.get(key, "")
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        ws.update_cell(int(sheet_row), idx + 1, str(value) if value is not None else "")

    # Mark as needing human review only when a status column exists and is blank.
    normalized = [h.lower() for h in headers]
    status_idx = next((i for i, h in enumerate(normalized) if h in ["review status", "pipeline status", "content status", "status"]), None)
    if status_idx is not None:
        existing_status = ws.cell(int(sheet_row), status_idx + 1).value
        if not str(existing_status or "").strip():
            ws.update_cell(int(sheet_row), status_idx + 1, "Needs Review")
    return f"Saved AI brief to {book.title} → {worksheet_name}, row {sheet_row}."


# -----------------------------------------------------------------------------
# Live news discovery (GDELT DOC API) and a dedicated Research Feed worksheet
# -----------------------------------------------------------------------------
NEWS_WORKSHEET_NAME = str(get_secret("NEWS_RESEARCH_WORKSHEET", "Research Feed"))
NEWS_DEFAULT_QUERY = '("Grand Theft Auto VI" OR "GTA VI" OR "GTA 6")'
NEWS_BASE_HEADERS = [
    "Title", "Source", "Source URL", "Indexed At", "Discovery Query",
    "Research Type", "Fact Status", "Review Status", "Notes",
]


def _article_type_hint(title: str, domain: str) -> str:
    """Heuristic triage only; never treats the outlet/title as proof."""
    d = (domain or "").lower().strip()
    t = (title or "").lower()
    if d == "rockstargames.com" or d.endswith(".rockstargames.com") or d == "take2games.com" or d.endswith(".take2games.com"):
        return "Potential official source — verify"
    if any(term in t for term in ("leak", "rumor", "rumour", "theory", "speculation", "alleged", "reportedly", "unconfirmed")):
        return "Claim/speculation terms detected — verify"
    return "News/reporting candidate — verify"


def _format_gdelt_date(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            continue
    return value


@st.cache_data(ttl=300, show_spinner=False)
def fetch_gdelt_news(query: str, timespan: str, max_records: int) -> List[Dict[str, str]]:
    """Fetch public news metadata. GDELT returns article links/headlines, not verification."""
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": int(max_records),
        "timespan": timespan,
        "sort": "datedesc",
    }
    endpoint = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
    request = Request(endpoint, headers={"User-Agent": "VicePlugHub/1.0 (GTA VI research dashboard)"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        raise RuntimeError(f"News discovery could not reach GDELT: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("GDELT returned an unexpected response format.")
    articles = payload.get("articles", []) or []
    results: List[Dict[str, str]] = []
    seen = set()
    for item in articles:
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or item.get("url_mobile") or "").strip()
        domain = str(item.get("domain") or "").strip()
        if not title or not url or not url.startswith(("https://", "http://")):
            continue
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "Title": title,
            "Source": domain or str(item.get("source") or "Unknown publisher"),
            "Source URL": url,
            "Indexed At": _format_gdelt_date(item.get("seendate") or item.get("date")),
            "Research Type": _article_type_hint(title, domain),
            "Fact Status": "Unverified — headline/metadata only",
            "Review Status": "Needs Review",
            "Notes": "Discovered via GDELT. Open the original source and verify the claim before scripting. Do not treat the headline alone as evidence.",
        })
    return results


def _load_named_worksheet_records(worksheet_name: str) -> Tuple[pd.DataFrame, Any, str, str]:
    """Load a named worksheet without changing the existing Video Discovery source."""
    try:
        book = open_spreadsheet()
        try:
            ws = book.worksheet(worksheet_name)
        except Exception:
            return pd.DataFrame(), None, f"The '{worksheet_name}' worksheet has not been created yet. Save selected discoveries to create it.", "missing_tab"
        values = ws.get_all_values()
        if not values:
            return pd.DataFrame(), ws, f"Connected to {book.title} / {worksheet_name}, but the worksheet is empty.", "empty"
        headers = [str(h).strip() for h in values[0]]
        if not any(headers):
            return pd.DataFrame(), ws, f"The first row of {worksheet_name} must contain column headers.", "empty"
        seen: Dict[str, int] = {}
        clean_headers = []
        for i, name in enumerate(headers):
            base = name or f"Column {i + 1}"
            seen[base] = seen.get(base, 0) + 1
            clean_headers.append(base if seen[base] == 1 else f"{base} ({seen[base]})")
        width = len(clean_headers)
        rows = [(row + [""] * max(0, width - len(row)))[:width] for row in values[1:]]
        out = pd.DataFrame(rows, columns=clean_headers)
        out.insert(0, "_sheet_row", range(2, len(out) + 2))
        if len(out):
            visible = [c for c in out.columns if c != "_sheet_row"]
            nonempty = out[visible].astype(str).apply(lambda r: any(v.strip() for v in r), axis=1)
            out = out.loc[nonempty].reset_index(drop=True)
        return out, ws, f"Connected: {book.title} → {worksheet_name} · {len(out)} saved research items", "connected"
    except Exception as exc:
        return pd.DataFrame(), None, str(exc), "error"


def save_news_to_research_sheet(articles: List[Dict[str, str]], discovery_query: str) -> Tuple[int, int, str]:
    """Explicitly create/use the Research Feed worksheet and append only non-duplicates."""
    if not articles:
        return 0, 0, "No articles were selected."
    if not HAS_GSPREAD:
        raise RuntimeError("Google Sheets integration is unavailable. Add gspread and google-auth to requirements.txt.")
    book = open_spreadsheet()
    try:
        ws = book.worksheet(NEWS_WORKSHEET_NAME)
    except Exception:
        ws = book.add_worksheet(title=NEWS_WORKSHEET_NAME, rows=max(1000, len(articles) + 10), cols=len(NEWS_BASE_HEADERS) + 2)
        ws.update("A1", [NEWS_BASE_HEADERS])

    existing_values = ws.get_all_values()
    headers = [str(h).strip() for h in (existing_values[0] if existing_values else [])]
    if not any(headers):
        headers = NEWS_BASE_HEADERS.copy()
        ws.update("A1", [headers])
        existing_values = [headers]

    def col_for(names: List[str]) -> Optional[int]:
        normalized = [h.strip().lower() for h in headers]
        for name in names:
            if name.lower() in normalized:
                return normalized.index(name.lower())
        for name in sorted(names, key=len, reverse=True):
            for idx, header in enumerate(normalized):
                if name.lower() in header:
                    return idx
        return None

    # Add missing fields after the user's existing columns; never rename or replace their fields.
    required = [
        ("Title", ["title", "story title", "headline", "article title", "video title"]),
        ("Source", ["source", "publisher", "domain", "site"]),
        ("Source URL", ["source url", "article url", "source link", "url", "link"]),
        ("Indexed At", ["indexed at", "seen at", "published at", "published date", "publication date", "date published", "published", "date"]),
        ("Discovery Query", ["discovery query", "search query", "query"]),
        ("Research Type", ["research type", "source type"]),
        ("Fact Status", ["fact status", "verification status"]),
        ("Review Status", ["review status", "pipeline status", "content status", "status"]),
        ("Notes", ["notes", "research notes", "editor notes"]),
    ]
    for canonical, aliases in required:
        if col_for(aliases) is None:
            next_col = len(headers) + 1
            ws.update_cell(1, next_col, canonical)
            headers.append(canonical)

    # Refresh all current values after adding headers; dedupe by URL and title.
    existing_values = ws.get_all_values()
    url_idx = col_for(["source url", "article url", "source link", "url", "link"])
    title_idx = col_for(["title", "story title", "headline", "article title", "video title"])
    existing_urls, existing_titles = set(), set()
    for row in existing_values[1:]:
        if url_idx is not None and len(row) > url_idx and row[url_idx].strip():
            existing_urls.add(row[url_idx].strip().rstrip("/").lower())
        if title_idx is not None and len(row) > title_idx and row[title_idx].strip():
            existing_titles.add(row[title_idx].strip().lower())

    out_rows: List[List[str]] = []
    skipped = 0
    for article in articles:
        url = article.get("Source URL", "").strip()
        title = article.get("Title", "").strip()
        if (url and url.rstrip("/").lower() in existing_urls) or (title and title.lower() in existing_titles):
            skipped += 1
            continue
        row = [""] * len(headers)
        values_by_canonical = {
            "Title": title, "Source": article.get("Source", ""), "Source URL": url,
            "Indexed At": article.get("Indexed At", ""), "Discovery Query": discovery_query,
            "Research Type": article.get("Research Type", ""), "Fact Status": "Unverified — headline/metadata only",
            "Review Status": "Needs Review", "Notes": article.get("Notes", ""),
        }
        for canonical, aliases in required:
            idx = col_for(aliases)
            if idx is not None and idx < len(row):
                row[idx] = values_by_canonical.get(canonical, "")
        out_rows.append(row)
        if url: existing_urls.add(url.rstrip("/").lower())
        if title: existing_titles.add(title.lower())

    if out_rows:
        ws.append_rows(out_rows, value_input_option="USER_ENTERED")
    return len(out_rows), skipped, f"Saved to {book.title} → {NEWS_WORKSHEET_NAME}."

# -----------------------------------------------------------------------------
# Load records and build the shared application shell
# -----------------------------------------------------------------------------
df, worksheet, sheet_message, sheet_status = load_sheet_records()

# Hero only appears on Dashboard, not at the top of every workspace.
if st.session_state.active_tab == "Dashboard":
    st.markdown("""
    <section class="vp-hero">
      <div class="vp-eyebrow">VICE CITY LIVES ONLINE</div>
      <h1>GTA VI RESEARCH.<br><span>AI INTELLIGENCE.</span><br>VIRAL CONTENT.</h1>
      <p>Track GTA VI research, prioritize content ideas, draft Shorts scripts, and move approved concepts through one creator workspace. AI outputs are drafts until you verify the source.</p>
    </section>
    """, unsafe_allow_html=True)

col_nav, col_main = st.columns([1.15, 5.2], gap="large")
with col_nav:
    st.markdown('<div class="vp-brand">👑 VICE<span>PLUG</span> HUB</div>', unsafe_allow_html=True)
    st.caption("YOUR CONTENT COMMAND CENTER")
    for label, icon in NAV_ITEMS:
        is_active = st.session_state.active_tab == label
        button_label = f"{icon}  {label}"
        if st.button(button_label, key=f"nav_{label}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.active_tab = label
            st.rerun()
    st.markdown('<div style="margin-top:24px;color:#64748b;font-size:.68rem;letter-spacing:.08em;font-weight:700;line-height:1.7">GOOD CONTENT<br>BUILDS BIGGER WORLDS.</div>', unsafe_allow_html=True)

with col_main:
    # =====================================================================
    # DASHBOARD
    # =====================================================================
    if st.session_state.active_tab == "Dashboard":
        greet_left, greet_right = st.columns([1.4, 1])
        with greet_left:
            st.markdown('<div class="vp-page-head" style="border:0;margin-bottom:.5rem;padding-bottom:0"><div><h1 style="font-size:1.55rem">Welcome back, Creator.</h1><p>Your GTA VI research and content overview.</p></div></div>', unsafe_allow_html=True)
        with greet_right:
            st.markdown(f'<div style="text-align:right;color:#91a3bd;font-size:.76rem;padding-top:8px">{datetime.now().strftime("%A, %B %d, %Y")}<br><span style="color:{"#10b981" if sheet_status == "connected" else "#f59e0b"};font-weight:700">● {"Google Sheets connected" if sheet_status == "connected" else "Google Sheets not connected"}</span></div>', unsafe_allow_html=True)

        title_col = title_column(df) if not df.empty else None
        score_col = score_column(df) if not df.empty else None
        status_col = status_column(df) if not df.empty else None
        scores = df[score_col].apply(number_value).dropna() if score_col else pd.Series(dtype=float)
        statuses = df[status_col].fillna("").astype(str).str.lower() if status_col else pd.Series(dtype=str)
        pending_count = int(statuses.str.contains("review|pending|needs approval|needs review", regex=True).sum()) if len(statuses) else 0
        approved_count = int(statuses.str.contains("approved|published", regex=True).sum()) if len(statuses) else 0
        stories_count = int(len(df))
        avg_score = f"{scores.mean():.0f}/100" if len(scores) else "—"
        metrics = st.columns(5, gap="small")
        with metrics[0]: metric_card("Research Records", str(stories_count), "Rows loaded from your sheet" if sheet_status == "connected" else "Connect Sheets for live counts", "📰", "#ff2e93")
        with metrics[1]: metric_card("Scored Ideas", str(int(len(scores))), "Records with a numeric score", "🎯", "#38d9f5")
        with metrics[2]: metric_card("Average Score", avg_score, "Based on available score fields", "⭐", "#a855f7")
        with metrics[3]: metric_card("Needs Review", str(pending_count) if status_col else "—", "Based on your status column", "🧾", "#f43f5e")
        with metrics[4]: metric_card("Approved / Published", str(approved_count) if status_col else "—", "Based on your status column", "✅", "#10b981")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        main_col, side_col = st.columns([1.45, 1], gap="medium")
        with main_col:
            st.markdown('<div class="vp-panel"><div class="vp-panel-title">🔥 Top Research Opportunities</div><div class="vp-muted">Ranked using the score already stored in your sheet. A score is a prioritization estimate, not a promise of virality.</div></div>', unsafe_allow_html=True)
            if df.empty or not title_col:
                show_missing_data(sheet_message if sheet_status != "connected" else "Add a title column and research records to your worksheet.")
            else:
                best = sorted_by_score(df).head(5)
                for i, (_, row) in enumerate(best.iterrows(), start=1):
                    title = safe_text(row.get(title_col, "Untitled record"), 110)
                    score = number_value(row.get(score_col)) if score_col else None
                    fact_col = fact_column(df)
                    fact = safe_text(row.get(fact_col, "Fact status not recorded"), 60) if fact_col else "Fact status not recorded"
                    st.markdown(f'<div class="vp-panel" style="display:flex;gap:12px;align-items:center;margin-bottom:8px;padding:12px"><div style="color:#73839d;font-family:Space Grotesk;font-weight:700">{i:02d}</div><div style="flex:1;min-width:0"><div style="font-weight:700;font-size:.88rem;color:#f8fafc">{title}</div><div class="vp-muted">{fact}</div></div><div style="white-space:nowrap;color:#ff63b0;font-family:Space Grotesk;font-weight:700">{f"{score:.0f}/100" if score is not None else "Unscored"}</div></div>', unsafe_allow_html=True)
        with side_col:
            st.markdown('<div class="vp-panel"><div class="vp-panel-title">⚡ Content Pipeline</div><div class="vp-muted">Progress inferred from your sheet status column.</div></div>', unsafe_allow_html=True)
            if not status_col:
                st.info("Your worksheet does not appear to have a Review Status or Status column, so pipeline counts are unavailable.")
            else:
                pipeline_stages = [
                    ("Research", len(df), "#38d9f5"),
                    ("Needs Review", int(statuses.str.contains("review|pending|needs", regex=True).sum()), "#f59e0b"),
                    ("Approved", int(statuses.str.contains("approved", regex=True).sum()), "#10b981"),
                    ("Published", int(statuses.str.contains("published", regex=True).sum()), "#a855f7"),
                ]
                for stage, count, color in pipeline_stages:
                    st.markdown(f'<div style="display:flex;justify-content:space-between;gap:10px;padding:12px 2px;border-bottom:1px solid #1a263b"><span style="color:#cbd5e1">● &nbsp;{stage}</span><b style="color:{color}">{count}</b></div>', unsafe_allow_html=True)
            st.markdown('<div class="vp-panel" style="margin-top:12px"><div class="vp-panel-title">🧠 Quick Actions</div></div>', unsafe_allow_html=True)
            quick1, quick2 = st.columns(2)
            with quick1:
                if st.button("Open AI Studio", use_container_width=True):
                    st.session_state.active_tab = "AI Studio"; st.rerun()
            with quick2:
                if st.button("Review Queue", use_container_width=True):
                    st.session_state.active_tab = "Review Queue"; st.rerun()
        st.markdown('<div class="vp-panel" style="margin-top:10px"><span class="vp-pill">DATA NOTE</span><div class="vp-muted" style="margin-top:8px">The dashboard no longer invents trend counts, view totals, confidence percentages, or breaking-news headlines. Figures appear only when the connected worksheet contains the relevant data.</div></div>', unsafe_allow_html=True)

    # =====================================================================
    # RESEARCH FEED / VIDEO DISCOVERY
    # =====================================================================
    elif st.session_state.active_tab == "Research Feed":
        render_page_header("Research Feed", "Discover recent GTA VI coverage from public news metadata, then choose what to save for human review.")
        st.markdown('<div class="vp-panel"><div class="vp-panel-title">🌐 Live News Discovery</div><div class="vp-muted">Searches GDELT’s news index for headline, publisher, index timestamp and source URL metadata. Results are discovery leads, not fact-checked stories; open the source before scripting. GDELT can miss relevant coverage, and its query endpoint may change.</div></div>', unsafe_allow_html=True)
        search_left, search_right = st.columns([2.2, 1])
        with search_left:
            discovery_query = st.text_input("Search query", value=st.session_state.get("news_query", NEWS_DEFAULT_QUERY), key="news_query_input", help='Try a phrase, e.g. \"GTA VI\" OR Rockstar OR \"Grand Theft Auto 6\"')
        with search_right:
            timespan_label = st.selectbox("Coverage window", ["Past 24 hours", "Past 3 days", "Past 7 days", "Past 30 days"], index=2, key="news_timespan_label")
        timespan = {"Past 24 hours": "1d", "Past 3 days": "3d", "Past 7 days": "7d", "Past 30 days": "30d"}[timespan_label]
        result_limit = st.select_slider("Maximum results", options=[10, 20, 30, 50], value=20, key="news_result_limit")
        if st.button("🔎 Search fresh coverage", type="primary", use_container_width=True):
            if not discovery_query.strip():
                st.warning("Enter a search query.")
            else:
                try:
                    with st.spinner("Searching recent news metadata…"):
                        found = fetch_gdelt_news(discovery_query.strip(), timespan, result_limit)
                    st.session_state.pop("news_discovery_editor", None)
                    st.session_state.news_discovery_results = found
                    st.session_state.news_discovery_query = discovery_query.strip()
                    st.session_state.news_discovery_error = ""
                    st.success(f"Found {len(found)} candidate articles. Review the original sources before using any claim.")
                except Exception as exc:
                    st.session_state.news_discovery_error = str(exc)
                    st.session_state.news_discovery_results = []
        if st.session_state.get("news_discovery_error"):
            st.error(st.session_state.news_discovery_error)
        found = st.session_state.get("news_discovery_results", [])
        if found:
            st.markdown("### Discovery results")
            st.caption("Select the stories to save. Duplicate links and titles already in the Research Feed will be skipped.")
            edit_df = pd.DataFrame([{
                "_Discovery ID": i, "Save": False, "Title": item["Title"], "Publisher / domain": item["Source"],
                "Indexed At (GDELT)": item["Indexed At"], "Triage hint (not verification)": item["Research Type"],
                "Source URL": item["Source URL"],
            } for i, item in enumerate(found)])
            edited = st.data_editor(
                edit_df, use_container_width=True, hide_index=True, num_rows="fixed", height=min(520, 44 + 36 * len(edit_df)),
                column_config={
                    "_Discovery ID": None,
                    "Save": st.column_config.CheckboxColumn("Save", help="Select this item for the Research Feed."),
                    "Source URL": st.column_config.LinkColumn("Source URL", display_text="Open source ↗"),
                },
                disabled=["_Discovery ID", "Title", "Publisher / domain", "Indexed At (GDELT)", "Triage hint (not verification)", "Source URL"],
                key="news_discovery_editor",
            )
            selected_positions = [int(row["_Discovery ID"]) for _, row in edited.iterrows() if bool(row["Save"])]
            save_col, clear_col = st.columns([2, 1])
            with save_col:
                if st.button(f"💾 Save {len(selected_positions)} selected to Google Sheets", type="primary", use_container_width=True, disabled=not selected_positions):
                    try:
                        selected_articles = [found[i] for i in selected_positions]
                        with st.spinner("Saving selected discovery records…"):
                            saved_count, skipped_count, message = save_news_to_research_sheet(selected_articles, st.session_state.get("news_discovery_query", discovery_query.strip()))
                        st.success(f"{message} Added {saved_count}; skipped {skipped_count} duplicate(s).")
                        st.session_state.news_discovery_results = []
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save discoveries: {exc}")
            with clear_col:
                if st.button("Clear results", use_container_width=True):
                    st.session_state.news_discovery_results = []
                    st.rerun()
        else:
            st.markdown('<div class="vp-empty"><b>No discovery results yet</b><br><span>Run a search to find recently indexed GTA VI headlines and publisher links.</span></div>', unsafe_allow_html=True)

        st.markdown("### Saved Research Feed")
        news_df, news_ws, news_message, news_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
        if news_status == "connected" and not news_df.empty:
            st.success(news_message)
            saved_title_col = title_column(news_df)
            saved_query = st.text_input("Filter saved research", placeholder="Filter headlines or publishers…", key="saved_news_filter")
            saved_view = news_df.copy()
            if saved_query.strip():
                saved_view = saved_view[saved_view.astype(str).apply(lambda col: col.str.contains(saved_query.strip(), case=False, na=False)).any(axis=1)]
            st.dataframe(clean_display_df(saved_view, 12), use_container_width=True, hide_index=True, height=320)
            saved_url_col = url_column(saved_view)
            if saved_url_col and len(saved_view):
                open_idx = st.selectbox("Open saved article", saved_view.index.tolist(), format_func=lambda idx: str(saved_view.loc[idx, saved_title_col] if saved_title_col else f"Sheet row {idx + 1}")[:120], key="saved_news_open_idx")
                target_url = str(saved_view.loc[open_idx, saved_url_col]).strip()
                if target_url.startswith(("https://", "http://")):
                    st.link_button("Open original source ↗", target_url)
        else:
            st.info(news_message or f"No saved Research Feed worksheet yet. Select results above and save them to create '{NEWS_WORKSHEET_NAME}'.")
        st.caption("Data source: GDELT Project. ‘Indexed At’ is when GDELT indexed/observed the article, not necessarily the publisher’s original publication time. Its article index is a discovery aid; the publisher remains the authority for the original story. See gdeltproject.org/about.html for GDELT’s data-use information.")

    # =====================================================================
    # VIDEO DISCOVERY — existing Google Sheets video workflow
    # =====================================================================
    elif st.session_state.active_tab == "Video Discovery":
        page_title = "Video Discovery"
        render_page_header(page_title, "Search and inspect video records already collected in your Google Sheet.")
        if df.empty:
            show_missing_data(sheet_message)
        else:
            query = st.text_input("Search video records", placeholder="Search titles, source links, summaries…", key="search_video_discovery")
            view = df.copy()
            if query.strip():
                mask = view.astype(str).apply(lambda c: c.str.contains(query.strip(), case=False, na=False)).any(axis=1)
                view = view[mask]
            with st.container(border=True):
                st.markdown(f"**{len(view)} records** · Google Sheets video research data")
                if title_column(view):
                    st.dataframe(clean_display_df(view, 12), use_container_width=True, hide_index=True, height=470)
                else:
                    st.warning("No title-like column was detected. Showing the available sheet columns so you can check the headers.")
                    st.dataframe(clean_display_df(view, 12), use_container_width=True, hide_index=True, height=400)
                link_col = url_column(view)
                if link_col and len(view):
                    chosen_index = st.selectbox("Open a source record", view.index.tolist(), format_func=lambda idx: str(view.loc[idx, title_column(view)] if title_column(view) else f"Row {idx + 1}")[:100], key="video_open_source")
                    url = str(view.loc[chosen_index, link_col]).strip()
                    if url.startswith("https://") or url.startswith("http://"):
                        st.link_button("Open selected source ↗", url)
                    else:
                        st.caption("No valid source URL is saved for this record.")

    # =====================================================================
    # VIRAL OPPORTUNITIES
    # =====================================================================
    elif st.session_state.active_tab == "Viral Opportunities":
        render_page_header("Viral Opportunities", "Prioritize ideas using the score and fact-status fields already saved in your data.")
        if df.empty:
            show_missing_data(sheet_message)
        elif not score_column(df):
            st.info("No score column was detected. Run AI analysis or add a column such as AI Priority Score / Viral Score to rank ideas.")
            st.dataframe(clean_display_df(df), use_container_width=True, hide_index=True)
        else:
            min_score = st.slider("Minimum priority score", 0, 100, 60)
            ranked = sorted_by_score(df)
            ranked = ranked[ranked["_numeric_score"].fillna(-1) >= min_score]
            st.caption(f"Showing {len(ranked)} records with a score of {min_score}+.")
            st.dataframe(clean_display_df(ranked.drop(columns=["_numeric_score"], errors="ignore"), 12), use_container_width=True, hide_index=True, height=470)
            st.caption("Priority scores help organize review; they do not predict actual views or guarantee virality.")

    # =====================================================================
    # AI STUDIO — analyze existing record
    # =====================================================================
    elif st.session_state.active_tab == "AI Studio":
        render_page_header("AI Studio", "Turn a saved video or news research record into an evidence-aware content brief.")
        ai_source = st.radio("Analyze records from", ["Video Discovery", "Research Feed"], horizontal=True, key="ai_studio_source")
        if ai_source == "Research Feed":
            analysis_df, analysis_ws, analysis_message, analysis_status = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
            analysis_sheet_name = NEWS_WORKSHEET_NAME
        else:
            analysis_df, analysis_ws, analysis_message, analysis_status = df, worksheet, sheet_message, sheet_status
            analysis_sheet_name = analysis_ws.title if analysis_ws is not None else str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))

        if analysis_df.empty or not title_column(analysis_df):
            show_missing_data(analysis_message if analysis_status != "connected" else "Add records with a Title column to analyze them here.")
        else:
            tcol = title_column(analysis_df)
            selected_idx = st.selectbox("Choose a research record", analysis_df.index.tolist(), format_func=lambda idx: str(analysis_df.loc[idx, tcol])[:130], key=f"ai_record_{ai_source}")
            selected_record = analysis_df.loc[selected_idx]
            sheet_row = int(selected_record.get("_sheet_row", selected_idx + 2))
            record = selected_record.drop(labels=["_sheet_row"], errors="ignore").to_dict()
            with st.expander("Source fields sent to the AI", expanded=False):
                st.json({k: str(v)[:1200] for k, v in record.items()})
            st.warning("Groq analyzes the saved title and fields only. It does not watch videos or independently verify article claims. Review the original source before using any factual statement.")
            if st.button("✨ Analyze selected record with Groq", type="primary", use_container_width=True, key="analyze_selected_ai_record"):
                system_prompt = """You are VicePlug Hub's GTA VI research editor. Use only information in the supplied record. Never invent gameplay, trailer frames, patents, leaks, release dates, view counts, or quotes. If the record lacks evidence, state that clearly. Distinguish official information, reputable reporting, creator commentary, speculation, and unverified claims. Return one JSON object with keys: relevance (High/Medium/Low), priority_score (1-100), fact_status, summary, why_it_matters, hook, commentary_draft (20-35 seconds), on_screen_text, title, caption, hashtags (array), verification_needed (array), rights_note, recommended_action. A score is only a prioritization estimate, not a prediction of virality."""
                user_prompt = "Analyze this saved research record. Treat all fields as unverified unless the source field itself clearly establishes provenance. Do not infer that a claim is true simply because it appears in a headline.\n\n" + json.dumps(record, ensure_ascii=False, default=str)
                try:
                    with st.spinner("Preparing the content brief…"):
                        result = call_groq(system_prompt, user_prompt, max_tokens=1900)
                    st.session_state.generated_ai_brief = result
                    st.session_state.generated_ai_source = ai_source
                    st.session_state.generated_ai_row = sheet_row
                    st.session_state.generated_ai_sheet = analysis_sheet_name
                    st.success("Draft generated. Verify every factual claim and source before using it.")
                except Exception as exc:
                    st.error(f"AI analysis failed: {exc}")

            brief = st.session_state.get("generated_ai_brief")
            same_record = (st.session_state.get("generated_ai_source") == ai_source and
                           st.session_state.get("generated_ai_row") == sheet_row and
                           st.session_state.get("generated_ai_sheet") == analysis_sheet_name)
            if brief and same_record:
                st.markdown("### Generated content brief")
                st.json(brief)
                st.download_button("Download brief as JSON", data=json.dumps(brief, ensure_ascii=False, indent=2), file_name="viceplug_ai_brief.json", mime="application/json", use_container_width=True, key="download_ai_brief")
                if st.button("💾 Save AI brief to this Google Sheets record", type="primary", use_container_width=True, key="save_ai_brief_to_sheet"):
                    try:
                        with st.spinner("Saving AI fields to the selected research row…"):
                            saved_message = save_ai_brief_to_worksheet(analysis_sheet_name, sheet_row, brief)
                        st.success(saved_message)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save the AI brief: {exc}")

    # =====================================================================
    # SCRIPT GENERATOR
    # =====================================================================
    elif st.session_state.active_tab == "Script Generator":
        render_page_header("Script Generator", "Draft a short-form script from a topic and evidence you provide.")
        st.markdown('<div class="vp-panel"><div class="vp-panel-title">Create a Short concept</div><div class="vp-muted">The generator should not make up details to make a story sound more exciting. Add source facts and a URL when available.</div></div>', unsafe_allow_html=True)
        topic = st.text_input("Video opportunity topic", placeholder="e.g. A confirmed detail from an official GTA VI trailer", key="script_topic")
        source_url = st.text_input("Source URL (optional)", placeholder="https://…", key="script_source_url")
        evidence = st.text_area("Verified facts / source notes", placeholder="Paste the facts that the script is allowed to state. Separate confirmed details from speculation.", height=130, key="script_evidence")
        angle = st.selectbox("Content angle", ["Explain a confirmed detail", "Compare GTA V and GTA VI", "Summarize reputable reporting", "Explore a clearly labelled theory", "React to creator commentary"])
        length = st.select_slider("Target length", options=[15, 20, 30, 40, 50, 60], value=30, format_func=lambda v: f"{v} seconds")
        if st.button("✨ Generate script with Groq", type="primary", use_container_width=True):
            if not topic.strip():
                st.warning("Enter a topic first.")
            elif not evidence.strip():
                st.warning("Add source facts or notes first. Without evidence, the script may only discuss the topic as an unverified idea.")
            else:
                system_prompt = """You write engaging short-form gaming scripts for VicePlug Hub. Use only supplied evidence. Do not invent events, trailer details, quotes, patents, leaks, release timing, numbers, or claims about what Rockstar confirmed. Label speculation. If evidence is insufficient, say so in verification_needed and avoid stating the claim as fact. Return JSON only with keys: title, spoken_hook, voiceover_script, timestamped_beats (array of objects with start, end, narration, visual_direction), on_screen_text (array), caption, hashtags (array), verification_needed (array), rights_note, why_this_angle. Make it punchy but accurate. Do not claim to have watched a source."""
                user_prompt = json.dumps({"topic": topic, "source_url": source_url, "evidence": evidence, "angle": angle, "target_seconds": length, "platforms": ["YouTube Shorts", "TikTok"]}, ensure_ascii=False)
                try:
                    with st.spinner("Drafting the script and on-screen beats…"):
                        result = call_groq(system_prompt, user_prompt, max_tokens=2200)
                    st.session_state.generated_script = result
                    st.success("Script draft generated. Review sources, edit it, and approve before publishing.")
                except Exception as exc:
                    st.error(f"Script generation failed: {exc}")
        if st.session_state.generated_script:
            st.markdown("### Your generated draft")
            result = st.session_state.generated_script
            st.json(result)
            st.download_button("Download script brief", data=json.dumps(result, ensure_ascii=False, indent=2), file_name="viceplug_script_draft.json", mime="application/json", use_container_width=True)

    # =====================================================================
    # CONTENT PIPELINE / REVIEW QUEUE
    # =====================================================================
    elif st.session_state.active_tab in ["Content Pipeline", "Review Queue"]:
        if st.session_state.active_tab == "Content Pipeline":
            render_page_header("Content Pipeline", "Track research records from discovery through review and publication.")
        else:
            render_page_header("Review Queue", "Focus on records that still need human review or approval.")

        pipeline_source = st.radio("Review records from", ["Video Discovery", "Research Feed"], horizontal=True, key=f"pipeline_source_{st.session_state.active_tab}")
        if pipeline_source == "Research Feed":
            pipeline_df, pipeline_ws, pipeline_message, pipeline_connection = _load_named_worksheet_records(NEWS_WORKSHEET_NAME)
            pipeline_sheet_name = NEWS_WORKSHEET_NAME
        else:
            pipeline_df, pipeline_ws, pipeline_message, pipeline_connection = df, worksheet, sheet_message, sheet_status
            pipeline_sheet_name = pipeline_ws.title if pipeline_ws is not None else str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery"))

        if pipeline_df.empty:
            show_missing_data(pipeline_message)
        else:
            s_col = status_column(pipeline_df)
            if not s_col:
                st.warning(f"No Review Status / Status column was detected in {pipeline_sheet_name}. Add a status column to enable stage tracking.")
                st.dataframe(clean_display_df(pipeline_df), use_container_width=True, hide_index=True)
            else:
                statuses = pipeline_df[s_col].fillna("").astype(str).str.strip()
                if st.session_state.active_tab == "Review Queue":
                    mask = statuses.str.lower().str.contains("review|pending|needs|draft|unreviewed", regex=True)
                    shown = pipeline_df[mask]
                else:
                    shown = pipeline_df.copy()
                stages = st.columns(4)
                labels = ["Needs Review", "Script Draft", "Approved", "Published"]
                patterns = ["review|pending|needs|unreviewed", "script|draft", "approved", "published"]
                for slot, label, pattern in zip(stages, labels, patterns):
                    count = int(statuses.str.lower().str.contains(pattern, regex=True).sum())
                    with slot:
                        st.markdown(f'<div class="vp-card"><div class="vp-metric-label">{label}</div><div class="vp-metric-value">{count}</div><div class="vp-metric-note">Matching status values</div></div>', unsafe_allow_html=True)
                st.markdown(" ")
                st.dataframe(clean_display_df(shown, 12), use_container_width=True, hide_index=True, height=350)
                shown_title_col = title_column(shown)
                if len(shown):
                    record_index = st.selectbox("Select a record to update", shown.index.tolist(), format_func=lambda idx: str(shown.loc[idx, shown_title_col])[:120] if shown_title_col else f"Sheet row {shown.loc[idx, '_sheet_row']}", key=f"pipeline_record_{st.session_state.active_tab}_{pipeline_source}")
                    current_status = str(pipeline_df.loc[record_index, s_col]) or "Unspecified"
                    st.caption(f"Current status: {current_status}")
                    statuses_options = ["Needs Review", "Script Draft", "In Review", "Approved", "Ready to Edit", "Ready to Publish", "Published", "Rejected"]
                    default_status_idx = statuses_options.index(current_status) if current_status in statuses_options else 0
                    new_status = st.selectbox("New status", statuses_options, index=default_status_idx, key=f"new_pipeline_status_{pipeline_source}_{st.session_state.active_tab}")
                    if st.button("Save status to Google Sheets", type="primary", key=f"save_pipeline_status_{pipeline_source}_{st.session_state.active_tab}"):
                        if pipeline_ws is None or pipeline_connection != "connected":
                            st.error("Google Sheets is not connected, so the status was not saved.")
                        else:
                            actual_headers = [str(h).strip() for h in pipeline_ws.row_values(1)]
                            normalized = [h.lower() for h in actual_headers]
                            try:
                                status_index = next(i for i, h in enumerate(normalized) if h in ["review status", "pipeline status", "content status", "status"])
                                sheet_row = int(pipeline_df.loc[record_index, "_sheet_row"])
                                pipeline_ws.update_cell(sheet_row, status_index + 1, new_status)
                                st.success(f"Updated {pipeline_sheet_name}, row {sheet_row} to '{new_status}'.")
                                st.rerun()
                            except StopIteration:
                                st.error("Could not find a supported status header in row 1; nothing was changed.")
                            except Exception as exc:
                                st.error(f"Could not save status: {exc}")

    # =====================================================================
    # TRENDS & ANALYTICS — no invented analytics
    # =====================================================================
    elif st.session_state.active_tab == "Trends & Analytics":
        render_page_header("Trends & Analytics", "See only the trends supported by records and metrics you have actually collected.")
        if df.empty:
            show_missing_data(sheet_message)
        else:
            topic_col = first_matching_column(df, ["Topic", "Category", "Keyword", "Trend", "Content Pillar"])
            date_col = first_matching_column(df, ["Published At", "Date Published", "Date", "Created At", "Collected At", "Timestamp", "End Timestamp"])
            views_col = first_matching_column(df, ["Views", "View Count", "Views Count", "Video Views"])
            score_col = score_column(df)
            left, right = st.columns(2)
            with left:
                st.markdown('<div class="vp-panel"><div class="vp-panel-title">Score distribution</div><div class="vp-muted">Only numeric scores stored in the worksheet are included.</div></div>', unsafe_allow_html=True)
                if score_col:
                    chart_df = pd.DataFrame({"Priority score": df[score_col].apply(number_value).dropna()})
                    if len(chart_df):
                        st.bar_chart(chart_df["Priority score"].value_counts(bins=10, sort=False).sort_index())
                    else:
                        st.info("Score column exists, but contains no numeric scores yet.")
                else:
                    st.info("Add an AI Priority Score or Viral Score column to chart scores.")
            with right:
                st.markdown('<div class="vp-panel"><div class="vp-panel-title">Recorded views</div><div class="vp-muted">Not a prediction. This chart needs real view counts from your sheet.</div></div>', unsafe_allow_html=True)
                if views_col:
                    views = df[views_col].apply(number_value).dropna()
                    if len(views):
                        st.bar_chart(views.reset_index(drop=True).rename("Views"))
                    else:
                        st.info("View-count column exists, but there are no numeric values.")
                else:
                    st.info("No views column detected. Connect platform analytics before making performance claims.")
            if topic_col:
                st.markdown("### Most frequent recorded topics")
                counts = df[topic_col].fillna("").astype(str).str.strip()
                counts = counts[counts != ""].value_counts().head(10)
                if len(counts):
                    st.bar_chart(counts)
                else:
                    st.info("The topic/category column is empty.")
            else:
                st.info("Add a Topic, Category, Keyword, Trend, or Content Pillar column to analyze recurring subjects.")
            if date_col:
                st.caption(f"Date-like field detected: {date_col}. Date-based growth comparisons can be added once the values are consistently formatted.")

    # =====================================================================
    # GOOGLE SHEETS SYNC
    # =====================================================================
    elif st.session_state.active_tab == "Google Sheets Sync":
        render_page_header("Google Sheets Sync", "Inspect your connected research worksheet and check connection setup.")
        if sheet_status == "connected":
            st.success(sheet_message)
            st.caption("This screen currently reads the configured research worksheet. Status edits in Content Pipeline / Review Queue are written back when a supported status column exists.")
            st.dataframe(clean_display_df(df, 14), use_container_width=True, hide_index=True, height=470)
            if st.button("Refresh from Google Sheets", type="primary"):
                st.rerun()
        else:
            st.error("Google Sheets is not connected.")
            st.code("GOOGLE_SHEET_ID = \"your-spreadsheet-id\"\nGROQ_API_KEY = \"your-groq-key\"\n\n[gcp_service_account]\ntype = \"service_account\"\n... = \"your service account fields\"", language="toml")
            st.markdown("In Streamlit Community Cloud, add secrets under **App → Settings → Secrets**. Share the spreadsheet with the service-account email as an Editor. Do not paste API keys into this Python file or a public repository.")
            if sheet_message:
                with st.expander("Connection detail"):
                    st.code(sheet_message)

    # =====================================================================
    # SETTINGS
    # =====================================================================
    elif st.session_state.active_tab == "Settings":
        render_page_header("Settings & Integrations", "Review configuration without exposing your API keys.")
        groq_configured = bool(get_secret("GROQ_API_KEY"))
        account_configured = bool(get_service_account_info() or (get_secret("GOOGLE_SERVICE_ACCOUNT_FILE") and os.path.exists(str(get_secret("GOOGLE_SERVICE_ACCOUNT_FILE")))))
        settings = [
            ("Groq API", "Connected / key present" if groq_configured and HAS_GROQ else "Not configured" if not groq_configured else "Package missing", "#10b981" if groq_configured and HAS_GROQ else "#f59e0b"),
            ("Google Sheets", "Connected" if sheet_status == "connected" else "Not connected", "#10b981" if sheet_status == "connected" else "#f59e0b"),
            ("Spreadsheet credentials", "Configured" if account_configured else "Missing", "#10b981" if account_configured else "#f59e0b"),
            ("Groq model", str(get_secret("GROQ_MODEL", "openai/gpt-oss-20b")), "#38d9f5"),
            ("Research worksheet", str(get_secret("VIDEO_DISCOVERY_WORKSHEET", "Video Discovery")), "#a855f7"),
            ("News research worksheet", NEWS_WORKSHEET_NAME, "#ff2e93"),
        ]
        for label, value, color in settings:
            st.markdown(f'<div class="vp-panel" style="display:flex;align-items:center;justify-content:space-between;gap:14px"><div style="font-weight:700">{html.escape(label)}</div><div style="color:{color};font-weight:700;text-align:right">{html.escape(value)}</div></div>', unsafe_allow_html=True)
        st.markdown("### Required Streamlit Secrets")
        st.code('GROQ_API_KEY = "your-groq-api-key"\nGROQ_MODEL = "openai/gpt-oss-20b"\nGOOGLE_SHEET_ID = "your-google-sheet-id"\nVIDEO_DISCOVERY_WORKSHEET = "Video Discovery"\nNEWS_RESEARCH_WORKSHEET = "Research Feed"\n\n[gcp_service_account]\ntype = "service_account"\nproject_id = "..."\nprivate_key_id = "..."\nprivate_key = "..."\nclient_email = "..."\nclient_id = "..."\nauth_uri = "https://accounts.google.com/o/oauth2/auth"\ntoken_uri = "https://oauth2.googleapis.com/token"\nauth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"\nclient_x509_cert_url = "..."', language="toml")
        st.caption("Use your actual service-account values in Streamlit Secrets; the example above is a template, not a working credential.")

# Footer in normal flow, inside the selected workspace only.
st.markdown('<div style="margin-top:24px;padding:12px 14px;border:1px solid #34204a;border-radius:12px;background:#090e1b;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;color:#8696af;font-size:.73rem"><span><b style="color:#ff477f">VICEPLUG HUB</b> · RESEARCH → VERIFY → CREATE → REVIEW → PUBLISH</span><span>AI-generated drafts require human fact-checking and rights review.</span></div>', unsafe_allow_html=True)
