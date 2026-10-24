import os
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

# --------------------------------------------------
# SYSTEM CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug OS | Research Automation System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# MODERN DESIGN SYSTEM & CONTROL DECK CSS
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@600;700&display=swap');

:root {
    --bg: #060911;
    --surface: #0B111E;
    --surface-card: #0F182A;
    --border: #1B2942;
    --border-subtle: #141F33;
    --purple: #7857FF;
    --cyan: #00E5FF;
    --pink: #F43F5E;
    --green: #10B981;
    --amber: #F59E0B;
    --text: #F8FAFC;
    --text-muted: #94A3B8;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg);
    color: var(--text);
}

.stApp {
    background: radial-gradient(circle at 15% 0%, rgba(120, 87, 255, 0.08) 0%, transparent 45%),
                radial-gradient(circle at 85% 0%, rgba(0, 229, 255, 0.05) 0%, transparent 45%),
                var(--bg);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #070C16 !important;
    border-right: 1px solid var(--border-subtle) !important;
}

.block-container {
    max-width: 1750px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3.5rem !important;
}

/* Hide Streamlit Branding */
#MainMenu, header, footer { visibility: hidden; }

/* Control Panels & Cards */
.os-panel {
    background: var(--surface-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s ease;
}

.os-panel:hover {
    border-color: #273D63;
}

/* Telemetry Mini-Stat */
.telemetry-card {
    background: linear-gradient(145deg, #0D1627 0%, #09101C 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.telemetry-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: #FFFFFF;
}

/* Priority & Fact Badges */
.badge-official {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}

.badge-leak {
    background: rgba(244, 63, 94, 0.15);
    color: #FB7185;
    border: 1px solid rgba(244, 63, 94, 0.35);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}

.badge-speculation {
    background: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}

.badge-priority {
    background: rgba(120, 87, 255, 0.2);
    color: #C4B5FD;
    border: 1px solid rgba(120, 87, 255, 0.4);
    padding: 2px 7px;
    border-radius: 5px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #090E1A;
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--border-subtle);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: var(--text-muted);
    font-weight: 600;
    padding: 8px 18px;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background-color: #141E33 !important;
    color: #FFF !important;
    border: 1px solid #233554 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    border: 1px solid #223554 !important;
    background: #111A2B !important;
    color: #E2E8F0 !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    border-color: var(--purple) !important;
    background: #162238 !important;
    box-shadow: 0 0 12px rgba(120, 87, 255, 0.25) !important;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# BACKEND INTEGRATIONS (SHEETS & GROQ)
# --------------------------------------------------
def get_secret(key, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


@st.cache_resource
def connect_google_sheets():
    raw = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    service_account = json.loads(raw) if isinstance(raw, str) else dict(raw)
    credentials = Credentials.from_service_account_info(
        service_account,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    return gspread.authorize(credentials).open_by_key(str(get_secret("GOOGLE_SHEET_ID")))


@st.cache_data(ttl=30)
def load_worksheet(sheet_name):
    try:
        values = connect_google_sheets().worksheet(sheet_name).get_all_values()
        if not values:
            return pd.DataFrame(), []
        headers = [h.strip() or f"Col_{i+1}" for i, h in enumerate(values[0])]
        rows = [(r + [""] * max(0, len(headers) - len(r)))[:len(headers)] for r in values[1:]]
        return pd.DataFrame(rows, columns=headers), headers
    except Exception:
        return pd.DataFrame(), []


def find_column(columns, candidates):
    lookup = {str(c).strip().lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    for c in columns:
        if any(cand.lower() in str(c).lower() for cand in candidates):
            return c
    return None


def update_sheet_status(worksheet_title, row_idx, new_status, status_col_name):
    try:
        ws = connect_google_sheets().worksheet(worksheet_title)
        headers = ws.row_values(1)
        if status_col_name in headers:
            col_idx = headers.index(status_col_name) + 1
            ws.update_cell(row_idx, col_idx, new_status)
            return True
    except Exception as e:
        st.error(f"Status sync failed: {e}")
    return False


def analyze_with_groq(record, custom_temperature=0.2, model_override=None):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=str(api_key))
    model = model_override or str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
You are VicePlug Hub's Senior GTA VI Content Research Engine.
Your goal is to parse raw community posts/videos into verified short-form video intelligence.

Classify evidence into:
- 'Official' (Rockstar, Take-Two, Sony, MSFT, verified SEC filings)
- 'Credible Press' (Bloomberg, Jason Schreier, IGN, etc.)
- 'Community Speculation' (Lore theories, map comparisons)
- 'Unverified Leak' (Anonymous Reddit/4chan/Twitter clips)

Return strictly JSON with:
{
  "relevance": "High" | "Medium" | "Low",
  "priority_score": int (1-100),
  "fact_status": "Official" | "Credible Press" | "Community Speculation" | "Unverified Leak",
  "summary": "1-2 sentence core factual event",
  "why_it_matters": "Audience retention angle",
  "hook": "High-CTR verbal script opening for a 30s Short",
  "commentary_draft": "Concise spoken narrative for voiceover",
  "verification_needed": ["Specific claim to verify before posting"],
  "tags": ["Tag1", "Tag2"]
}
"""
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({k: str(v)[:1500] for k, v in record.items() if str(v).strip()})},
        ],
        temperature=custom_temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content or "{}")


def save_ai_analysis(ws_title, headers, row_number, result):
    ws = connect_google_sheets().worksheet(ws_title)
    mapping = {
        "AI Priority Score": result.get("priority_score", 50),
        "AI Fact Status": result.get("fact_status", "Unverified Leak"),
        "AI Summary": result.get("summary", ""),
        "AI Hook": result.get("hook", ""),
        "AI Commentary Draft": result.get("commentary_draft", ""),
        "AI Verification Needed": "; ".join(result.get("verification_needed", [])),
        "Review Status": "Needs Review",
        "AI Analyzed UTC": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    new_headers = list(headers)
    for col in mapping:
        if col not in new_headers:
            new_headers.append(col)

    if new_headers != list(headers):
        ws.update("1:1", [new_headers])

    row_data = (ws.row_values(row_number) + [""] * len(new_headers))[:len(new_headers)]
    for col, val in mapping.items():
        idx = new_headers.index(col)
        row_data[idx] = str(val)

    ws.update(f"A{row_number}", [row_data], value_input_option="USER_ENTERED")


# --------------------------------------------------
# SYSTEM BOOT & DATA SYNC
# --------------------------------------------------
spreadsheet = connect_google_sheets()
all_worksheets = [ws.title for ws in spreadsheet.worksheets()]

def match_ws(names):
    return next((n for n in names if n in all_worksheets), None)

ws_disc_name = match_ws(["Video Discovery", "Discovery", "Sheet1"])
discovery_df, disc_headers = load_worksheet(ws_disc_name) if ws_disc_name else (pd.DataFrame(), [])

title_col = find_column(discovery_df.columns, ["video title", "title", "headline"]) if not discovery_df.empty else None
url_col = find_column(discovery_df.columns, ["video url", "url", "link"]) if not discovery_df.empty else None
status_col = find_column(discovery_df.columns, ["review status", "status", "approval"]) if not discovery_df.empty else "Review Status"
score_col = find_column(discovery_df.columns, ["ai priority score", "priority score", "score"]) if not discovery_df.empty else "AI Priority Score"
fact_col = find_column(discovery_df.columns, ["ai fact status", "fact status", "type"]) if not discovery_df.empty else "AI Fact Status"
summary_col = find_column(discovery_df.columns, ["ai summary", "summary"]) if not discovery_df.empty else None
hook_col = find_column(discovery_df.columns, ["ai hook", "hook"]) if not discovery_df.empty else None


# --------------------------------------------------
# SIDEBAR: SYSTEM TELEMETRY & CONTROLS
# --------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #7857FF, #00E5FF); width: 36px; height: 36px; border-radius: 10px; display:flex; align-items:center; justify-content:center; font-size:18px;">⚡</div>
            <div>
                <div style="font-weight:800; font-size: 1.1rem; letter-spacing: -0.02em;">VicePlug <span style="color:#00E5FF">OS</span></div>
                <div style="font-size: 0.65rem; color: #94A3B8; font-family:'JetBrains Mono'; letter-spacing: 0.05em;">RESEARCH AUTOMATION</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#64748B; letter-spacing:0.1em; text-transform:uppercase;'>GLOBAL TRIAGE FILTERS</p>", unsafe_allow_html=True)
    
    min_score = st.slider("Min AI Priority Score", min_value=0, max_value=100, value=30, step=5)
    
    fact_filter = st.multiselect(
        "Evidence Credibility",
        options=["Official", "Credible Press", "Community Speculation", "Unverified Leak"],
        default=["Official", "Credible Press", "Community Speculation", "Unverified Leak"],
    )

    status_filter = st.multiselect(
        "Workflow Status",
        options=["Needs Review", "Approved", "In Clip Queue", "Rejected"],
        default=["Needs Review", "Approved", "In Clip Queue"],
    )

    st.divider()

    st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#64748B; letter-spacing:0.1em; text-transform:uppercase;'>ENGINE TELEMETRY</p>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="font-size:0.78rem; color:#94A3B8; font-family:'JetBrains Mono'; display:flex; flex-direction:column; gap:6px;">
            <div>⚡ <b>Engine:</b> {get_secret('GROQ_MODEL', 'llama-3.3-70b-versatile')}</div>
            <div>📊 <b>Active Sheet:</b> {ws_disc_name}</div>
            <div>🟢 <b>Sync State:</b> Live (Cached 30s)</div>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("↻ Hard Sync Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# --------------------------------------------------
# HEADER COMMAND BAR
# --------------------------------------------------
head_col1, head_col2 = st.columns([2.5, 1.5])
with head_col1:
    st.markdown("""
        <div style="margin-bottom: 8px;">
            <h1 style="font-size: 1.8rem; font-weight: 800; letter-spacing: -0.03em; margin:0;">Research Intelligence Control Deck</h1>
            <p style="color: #94A3B8; font-size: 0.85rem; margin: 4px 0 0 0;">Automated signal intake, claim verification, and short-form narrative production.</p>
        </div>
    """, unsafe_allow_html=True)

with head_col2:
    search_query = st.text_input("Search Signals", placeholder="Filter by keyword, topic, or source...", label_visibility="collapsed")


# --------------------------------------------------
# FILTERED WORKING DATASET
# --------------------------------------------------
display_df = discovery_df.copy()

if not display_df.empty:
    # Ensure standard scoring columns exist safely for calculations
    if score_col in display_df.columns:
        display_df["_numeric_score"] = pd.to_numeric(display_df[score_col], errors="coerce").fillna(0)
    else:
        display_df["_numeric_score"] = 0

    if status_col not in display_df.columns:
        display_df[status_col] = "Needs Review"
    if fact_col not in display_df.columns:
        display_df[fact_col] = "Unverified Leak"

    # Apply global filters
    display_df = display_df[display_df["_numeric_score"] >= min_score]
    if fact_filter and fact_col in display_df.columns:
        display_df = display_df[display_df[fact_col].isin(fact_filter) | (display_df[fact_col] == "")]
    if status_filter and status_col in display_df.columns:
        display_df = display_df[display_df[status_col].isin(status_filter) | (display_df[status_col] == "")]
    if search_query:
        mask = display_df.astype(str).apply(lambda col: col.str.contains(search_query, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]


# --------------------------------------------------
# HIGH-DENSITY TELEMETRY STRIP (4 METRICS)
# --------------------------------------------------
t1, t2, t3, t4 = st.columns(4)
total_records = len(discovery_df)
high_priority = len(discovery_df[discovery_df["_numeric_score"] >= 70]) if "_numeric_score" in discovery_df else 0
needs_review = len(discovery_df[discovery_df[status_col].str.lower() == "needs review"]) if status_col in discovery_df else 0
approved_total = len(discovery_df[discovery_df[status_col].str.lower() == "approved"]) if status_col in discovery_df else 0

with t1:
    st.markdown(f"""
        <div class="telemetry-card">
            <span style="font-size:0.75rem; color:#94A3B8; font-weight:600;">ACTIVE INGESTION POOL</span>
            <div class="telemetry-val">{total_records}</div>
            <span style="font-size:0.72rem; color:#00E5FF;">Direct from Google Sheets</span>
        </div>
    """, unsafe_allow_html=True)

with t2:
    st.markdown(f"""
        <div class="telemetry-card">
            <span style="font-size:0.75rem; color:#94A3B8; font-weight:600;">HIGH-PRIORITY SIGNALS (≥70)</span>
            <div class="telemetry-val" style="color:#C4B5FD;">{high_priority}</div>
            <span style="font-size:0.72rem; color:#A78BFA;">Recommended for production</span>
        </div>
    """, unsafe_allow_html=True)

with t3:
    st.markdown(f"""
        <div class="telemetry-card">
            <span style="font-size:0.75rem; color:#94A3B8; font-weight:600;">AWAITING FACT-CHECK / TRIAGE</span>
            <div class="telemetry-val" style="color:#FBBF24;">{needs_review}</div>
            <span style="font-size:0.72rem; color:#F59E0B;">Requires human editor sign-off</span>
        </div>
    """, unsafe_allow_html=True)

with t4:
    st.markdown(f"""
        <div class="telemetry-card">
            <span style="font-size:0.75rem; color:#94A3B8; font-weight:600;">VERIFIED / IN PRODUCTION</span>
            <div class="telemetry-val" style="color:#34D399;">{approved_total}</div>
            <span style="font-size:0.72rem; color:#10B981;">Ready for video editor</span>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# --------------------------------------------------
# SYSTEM WORKSPACES (TABS)
# --------------------------------------------------
tab_triage, tab_telemetry, tab_automation, tab_master = st.tabs([
    "🎯 Research Triage & Hopper",
    "📊 Signal Telemetry & Charts",
    "⚡ Batch Automation Engine",
    "🗄️ Knowledge Base & Raw Data",
])


# ==================================================
# TAB 1: RESEARCH TRIAGE & HOPPER (ACTIONABLE)
# ==================================================
with tab_triage:
    if display_df.empty:
        st.info("No research items meet the current sidebar filter criteria.")
    else:
        st.markdown(f"<p style='font-size:0.8rem; color:#94A3B8;'>Displaying <b>{len(display_df)}</b> filtered research items.</p>", unsafe_allow_html=True)

        for idx, (original_idx, row) in enumerate(display_df.iterrows()):
            sheet_row_num = original_idx + 2  # 1-based index + header offset
            title = str(row.get(title_col, "Untitled Discovery"))
            score = int(row.get("_numeric_score", 0))
            fact = str(row.get(fact_col, "Unverified Leak"))
            status = str(row.get(status_col, "Needs Review"))
            summary = str(row.get(summary_col, "No AI summary generated yet."))
            hook = str(row.get(hook_col, "No hook generated yet."))
            source_link = str(row.get(url_col, ""))

            # Fact badge classification
            badge_class = "badge-leak"
            if "official" in fact.lower(): badge_class = "badge-official"
            elif "press" in fact.lower(): badge_class = "badge-official"
            elif "speculation" in fact.lower(): badge_class = "badge-speculation"

            # Triage Item Card
            with st.container():
                st.markdown(f"""
                    <div class="os-panel" style="margin-bottom: 12px; padding: 16px 20px;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                            <div style="max-width: 75%;">
                                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                                    <span class="badge-priority">SCORE: {score}/100</span>
                                    <span class="{badge_class}">{fact.upper()}</span>
                                    <span style="font-size:0.75rem; color:#64748B;">• Row {sheet_row_num}</span>
                                </div>
                                <div style="font-size:1.05rem; font-weight:700; color:#F8FAFC;">{title}</div>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-size:0.8rem; padding:4px 10px; border-radius:6px; background:#162238; border:1px solid #233554; font-weight:600;">{status}</span>
                            </div>
                        </div>
                        <div style="background:#080D17; border-radius:8px; padding:12px; margin: 10px 0; border:1px solid #141F33; font-size:0.85rem;">
                            <div style="color:#C4B5FD; font-weight:600; margin-bottom:3px;">🎣 Short-form Hook: <span style="color:#E2E8F0; font-weight:400;">"{hook}"</span></div>
                            <div style="color:#94A3B8; margin-top:4px;"><b>Summary:</b> {summary}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Interactive Action Bar underneath each item
                act1, act2, act3, act4, act5 = st.columns([1, 1, 1.2, 1.5, 2.3])
                
                with act1:
                    if st.button("✅ Approve", key=f"app_{sheet_row_num}", use_container_width=True):
                        if update_sheet_status(ws_disc_name, sheet_row_num, "Approved", status_col):
                            st.toast(f"Row {sheet_row_num} Approved!", icon="✅")
                            st.cache_data.clear()
                            st.rerun()

                with act2:
                    if st.button("📋 To Queue", key=f"que_{sheet_row_num}", use_container_width=True):
                        if update_sheet_status(ws_disc_name, sheet_row_num, "In Clip Queue", status_col):
                            st.toast(f"Row {sheet_row_num} queued for script editor.", icon="📋")
                            st.cache_data.clear()
                            st.rerun()

                with act3:
                    if st.button("⛔ Reject / Archive", key=f"rej_{sheet_row_num}", use_container_width=True):
                        if update_sheet_status(ws_disc_name, sheet_row_num, "Rejected", status_col):
                            st.toast(f"Row {sheet_row_num} marked Rejected.", icon="🗑️")
                            st.cache_data.clear()
                            st.rerun()

                with act4:
                    if st.button("🧠 Run/Re-run Groq", key=f"ai_{sheet_row_num}", use_container_width=True):
                        with st.spinner("Executing Groq analysis..."):
                            try:
                                res = analyze_with_groq(row.to_dict())
                                save_ai_analysis(ws_disc_name, disc_headers, sheet_row_num, res)
                                st.success("Updated!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Groq failed: {e}")

                with act5:
                    if source_link and source_link.startswith("http"):
                        st.markdown(f"<div style='padding-top:6px;'><a href='{source_link}' target='_blank' style='font-size:0.8rem; color:#00E5FF; text-decoration:none;'>🔗 Open External Source ↗</a></div>", unsafe_allow_html=True)


# ==================================================
# TAB 2: SIGNAL TELEMETRY & CHARTS
# ==================================================
with tab_telemetry:
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        st.markdown("<div class='os-panel'><b>Signal Distribution by Evidence Credibility</b>", unsafe_allow_html=True)
        if fact_col in discovery_df.columns:
            counts = discovery_df[fact_col].replace("", "Unclassified").value_counts().reset_index()
            counts.columns = ["Evidence Type", "Count"]
            fig_pie = px.pie(
                counts,
                names="Evidence Type",
                values="Count",
                hole=0.65,
                color_discrete_sequence=["#10B981", "#7857FF", "#F59E0B", "#F43F5E", "#64748B"]
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94A3B8",
                height=280,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_c2:
        st.markdown("<div class='os-panel'><b>Hype Score Velocity Histogram</b>", unsafe_allow_html=True)
        if "_numeric_score" in discovery_df.columns:
            fig_hist = px.histogram(
                discovery_df,
                x="_numeric_score",
                nbins=15,
                color_discrete_sequence=["#00E5FF"],
            )
            fig_hist.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94A3B8",
                height=280,
                xaxis_title="Priority Score (0-100)",
                yaxis_title="Discovered Items",
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==================================================
# TAB 3: BATCH AUTOMATION ENGINE
# ==================================================
with tab_automation:
    st.markdown("""
        <div class="os-panel">
            <h3 style="margin:0 0 8px 0; font-size:1.1rem;">⚡ Batch Research Processor</h3>
            <p style="color:#94A3B8; font-size:0.85rem;">Automatically run Groq LLM extraction against all spreadsheet records that have not been scored yet.</p>
        </div>
    """, unsafe_allow_html=True)

    auto_col1, auto_col2 = st.columns([1, 2])

    with auto_col1:
        batch_limit = st.slider("Max items to process in batch", 1, 20, 5)
        temp_setting = st.slider("Model Temperature (Creativity vs Determinism)", 0.0, 0.7, 0.2, 0.05)
        
        unanalyzed = discovery_df[discovery_df["_numeric_score"] == 0] if "_numeric_score" in discovery_df else discovery_df
        st.write(f"📥 Found **{len(unanalyzed)}** unscored records in Sheets.")

        if st.button("🚀 Start Batch Groq Intake", type="primary", use_container_width=True):
            if unanalyzed.empty:
                st.success("All items in spreadsheet already have AI scores!")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0

                for i, (orig_idx, row_record) in enumerate(unanalyzed.head(batch_limit).iterrows()):
                    row_num = orig_idx + 2
                    status_text.text(f"Processing row {row_num} of {len(unanalyzed)}...")
                    try:
                        res = analyze_with_groq(row_record.to_dict(), custom_temperature=temp_setting)
                        save_ai_analysis(ws_disc_name, disc_headers, row_num, res)
                        success_count += 1
                    except Exception as err:
                        st.error(f"Error on row {row_num}: {err}")
                    progress_bar.progress((i + 1) / min(len(unanalyzed), batch_limit))

                status_text.text("Batch Complete!")
                st.success(f"Successfully processed and updated {success_count} records in Google Sheets!")
                st.cache_data.clear()
                st.rerun()

    with auto_col2:
        st.markdown("""
            <div style="background:#090E1A; border:1px solid #18253A; border-radius:10px; padding:16px; font-size:0.85rem;">
                <b style="color:#C4B5FD;">Prompt Engine Configuration</b>
                <p style="color:#94A3B8; margin-top:6px;">VicePlug OS classifies content claims using a strict truthfulness matrix designed to protect creator accounts from strikes and hallucinated release dates.</p>
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#A78BFA; background:#04070D; padding:10px; border-radius:6px; margin-top:8px;">
                    Model: llama-3.3-70b-versatile<br>
                    Schema: RFC-8259 Compliant JSON<br>
                    Target Output: Hook, Fact Status, Priority Score, Narrative Commentary
                </div>
            </div>
        """, unsafe_allow_html=True)


# ==================================================
# TAB 4: MASTER KNOWLEDGE BASE & RAW DATA
# ==================================================
with tab_master:
    st.markdown("<div class='os-panel'>", unsafe_allow_html=True)
    m_col1, m_col2 = st.columns([3, 1])
    with m_col1:
        st.markdown("<b>Complete Working Records</b> (Synced bidirectionally with Google Sheets)", unsafe_allow_html=True)
    with m_col2:
        csv_data = discovery_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Export CSV",
            data=csv_data,
            file_name=f"viceplug_research_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.dataframe(
        display_df.drop(columns=["_numeric_score"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
        height=500
    )
    st.markdown("</div>", unsafe_allow_html=True)
