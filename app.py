"""VicePlug Hub — GTA VI research and content operations dashboard.

Designed for Streamlit Community Cloud. Connects to Google Sheets and Groq
when credentials are supplied in Streamlit Secrets.
"""

import json
import os
import html
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
    elif st.session_state.active_tab in ["Research Feed", "Video Discovery"]:
        page_title = st.session_state.active_tab
        render_page_header(page_title, "Search and inspect records already collected in your Google Sheet.")
        if df.empty:
            show_missing_data(sheet_message)
        else:
            query = st.text_input("Search records", placeholder="Search titles, source links, summaries…", key=f"search_{page_title}")
            view = df.copy()
            if query.strip():
                mask = view.astype(str).apply(lambda c: c.str.contains(query.strip(), case=False, na=False)).any(axis=1)
                view = view[mask]
            with st.container(border=True):
                st.markdown(f"**{len(view)} records** · Worksheet data, not a live web search")
                if title_column(view):
                    st.dataframe(clean_display_df(view, 12), use_container_width=True, hide_index=True, height=470)
                else:
                    st.warning("No title-like column was detected. Showing the available sheet columns so you can check the headers.")
                    st.dataframe(clean_display_df(view, 12), use_container_width=True, hide_index=True, height=400)
                link_col = url_column(view)
                if link_col and len(view):
                    chosen_index = st.selectbox("Open a source record", view.index.tolist(), format_func=lambda idx: str(view.loc[idx, title_column(view)] if title_column(view) else f"Row {idx + 1}")[:100])
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
        render_page_header("AI Studio", "Turn a saved research record into a reviewable content brief.")
        if df.empty or not title_column(df):
            show_missing_data(sheet_message if sheet_status != "connected" else "Add records with a Title column to analyze them here.")
        else:
            tcol = title_column(df)
            selected_idx = st.selectbox("Choose a research record", df.index.tolist(), format_func=lambda idx: str(df.loc[idx, tcol])[:130])
            record = df.loc[selected_idx].drop(labels=["_sheet_row"], errors="ignore").to_dict()
            with st.expander("Source fields sent to the AI", expanded=False):
                st.json({k: str(v)[:1200] for k, v in record.items()})
            st.warning("Groq analyzes the text fields you provide. This code does not watch the video, fetch fresh news, or independently verify claims.")
            if st.button("✨ Analyze selected record with Groq", type="primary", use_container_width=True):
                system_prompt = """You are VicePlug Hub's GTA VI research editor. Use only information in the supplied record. Never invent gameplay, trailer frames, patents, leaks, release dates, view counts, or quotes. If the record lacks evidence, state that clearly. Distinguish official information, reputable reporting, creator commentary, speculation, and unverified claims. Return one JSON object with keys: relevance (High/Medium/Low), priority_score (1-100), fact_status, summary, why_it_matters, hook, commentary_draft (20-35 seconds), on_screen_text, title, caption, hashtags (array), verification_needed (array), rights_note, recommended_action. A score is only a prioritization estimate, not a prediction of virality."""
                user_prompt = "Analyze this saved sheet record. Treat all fields as unverified unless the source field itself clearly establishes provenance.\n\n" + json.dumps(record, ensure_ascii=False, default=str)
                try:
                    with st.spinner("Preparing the content brief…"):
                        result = call_groq(system_prompt, user_prompt, max_tokens=1900)
                    st.session_state.generated_script = result
                    st.success("Draft generated. Verify every factual claim and source before using it.")
                except Exception as exc:
                    st.error(f"AI analysis failed: {exc}")
            if st.session_state.generated_script:
                st.markdown("### Generated content brief")
                st.json(st.session_state.generated_script)
                st.download_button("Download brief as JSON", data=json.dumps(st.session_state.generated_script, ensure_ascii=False, indent=2), file_name="viceplug_ai_brief.json", mime="application/json", use_container_width=True)

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
        if df.empty:
            show_missing_data(sheet_message)
        else:
            s_col = status_column(df)
            if not s_col:
                st.warning("No Review Status / Status column was detected. Add a status column to your Video Discovery worksheet to enable stage tracking.")
                st.dataframe(clean_display_df(df), use_container_width=True, hide_index=True)
            else:
                statuses = df[s_col].fillna("").astype(str).str.strip()
                if st.session_state.active_tab == "Review Queue":
                    mask = statuses.str.lower().str.contains("review|pending|needs|draft|unreviewed", regex=True)
                    shown = df[mask]
                else:
                    shown = df.copy()
                stages = st.columns(4)
                labels = ["Needs Review", "Script Draft", "Approved", "Published"]
                patterns = ["review|pending|needs|unreviewed", "script|draft", "approved", "published"]
                for slot, label, pattern in zip(stages, labels, patterns):
                    count = int(statuses.str.lower().str.contains(pattern, regex=True).sum())
                    with slot:
                        st.markdown(f'<div class="vp-card"><div class="vp-metric-label">{label}</div><div class="vp-metric-value">{count}</div><div class="vp-metric-note">Matching status values</div></div>', unsafe_allow_html=True)
                st.markdown(" ")
                st.dataframe(clean_display_df(shown, 12), use_container_width=True, hide_index=True, height=350)
                title_col = title_column(shown)
                if len(shown):
                    record_index = st.selectbox("Select a record to update", shown.index.tolist(), format_func=lambda idx: str(shown.loc[idx, title_col])[:120] if title_col else f"Sheet row {shown.loc[idx, '_sheet_row']}")
                    current_status = str(df.loc[record_index, s_col]) or "Unspecified"
                    st.caption(f"Current status: {current_status}")
                    new_status = st.selectbox("New status", ["Needs Review", "Script Draft", "In Review", "Approved", "Ready to Edit", "Ready to Publish", "Published", "Rejected"], index=0, key="new_pipeline_status")
                    if st.button("Save status to Google Sheets", type="primary"):
                        if worksheet is None or sheet_status != "connected":
                            st.error("Google Sheets is not connected, so the status was not saved.")
                        else:
                            actual_headers = [str(h).strip() for h in worksheet.row_values(1)]
                            normalized = [h.lower() for h in actual_headers]
                            try:
                                status_index = next(i for i, h in enumerate(normalized) if h in ["review status", "pipeline status", "content status", "status"])
                                sheet_row = int(df.loc[record_index, "_sheet_row"])
                                worksheet.update_cell(sheet_row, status_index + 1, new_status)
                                st.success(f"Updated row {sheet_row} to '{new_status}'.")
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
        ]
        for label, value, color in settings:
            st.markdown(f'<div class="vp-panel" style="display:flex;align-items:center;justify-content:space-between;gap:14px"><div style="font-weight:700">{html.escape(label)}</div><div style="color:{color};font-weight:700;text-align:right">{html.escape(value)}</div></div>', unsafe_allow_html=True)
        st.markdown("### Required Streamlit Secrets")
        st.code('GROQ_API_KEY = "your-groq-api-key"\nGROQ_MODEL = "openai/gpt-oss-20b"\nGOOGLE_SHEET_ID = "your-google-sheet-id"\nVIDEO_DISCOVERY_WORKSHEET = "Video Discovery"\n\n[gcp_service_account]\ntype = "service_account"\nproject_id = "..."\nprivate_key_id = "..."\nprivate_key = "..."\nclient_email = "..."\nclient_id = "..."\nauth_uri = "https://accounts.google.com/o/oauth2/auth"\ntoken_uri = "https://oauth2.googleapis.com/token"\nauth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"\nclient_x509_cert_url = "..."', language="toml")
        st.caption("Use your actual service-account values in Streamlit Secrets; the example above is a template, not a working credential.")

# Footer in normal flow, inside the selected workspace only.
st.markdown('<div style="margin-top:24px;padding:12px 14px;border:1px solid #34204a;border-radius:12px;background:#090e1b;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;color:#8696af;font-size:.73rem"><span><b style="color:#ff477f">VICEPLUG HUB</b> · RESEARCH → VERIFY → CREATE → REVIEW → PUBLISH</span><span>AI-generated drafts require human fact-checking and rights review.</span></div>', unsafe_allow_html=True)
