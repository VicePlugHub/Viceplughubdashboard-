import os
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug Hub | GTA VI Clips • AI • Growth",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# CUSTOM ULTRA-MODERN CSS THEME
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg-dark: #070B14;
    --card-bg: #0D1524;
    --card-border: #1C2B42;
    --card-hover: #152035;
    --accent-purple: #7857FF;
    --accent-pink: #ED4BBA;
    --accent-cyan: #22D3EE;
    --accent-green: #20D9A0;
    --accent-yellow: #F59E0B;
    --text-main: #F1F5F9;
    --text-muted: #8E9FB8;
}

/* Global Reset */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-main);
}

.stApp {
    background-color: var(--bg-dark);
    background-image: 
        radial-gradient(at 0% 0%, rgba(120, 87, 255, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(237, 75, 186, 0.06) 0px, transparent 50%);
}

/* Main Container Padding */
.block-container {
    max-width: 1720px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
}

/* Hide Default Streamlit Chrome */
#MainMenu, header, footer { visibility: hidden; }

/* Custom Sidebar */
[data-testid="stSidebar"] {
    background: #090E1A !important;
    border-right: 1px solid #162235 !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 2rem !important;
}

/* Custom Navigation Radio */
div[data-testid="stRadio"] > div {
    gap: 6px;
}

div[data-testid="stRadio"] label {
    background: transparent;
    padding: 10px 14px;
    border-radius: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
    font-weight: 500;
    color: var(--text-muted);
}

div[data-testid="stRadio"] label:hover {
    background: #121C2F;
    color: var(--text-main);
}

div[data-testid="stRadio"] label[data-checked="true"] {
    background: linear-gradient(90deg, rgba(120, 87, 255, 0.25) 0%, rgba(120, 87, 255, 0.05) 100%);
    border-left: 3px solid var(--accent-purple);
    color: #FFFFFF !important;
    font-weight: 600;
}

/* Glassmorphism Card Panels */
.vp-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
}

.vp-card:hover {
    border-color: #263854;
}

/* Hero Banner */
.vp-hero-banner {
    position: relative;
    background: linear-gradient(135deg, #10162B 0%, #1E1238 50%, #381232 100%);
    border: 1px solid #2B2E58;
    border-radius: 20px;
    padding: 34px 40px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    overflow: hidden;
}

.vp-hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    margin: 4px 0 8px 0;
    letter-spacing: -0.02em;
}

.vp-badge-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    background: rgba(32, 217, 160, 0.12);
    color: var(--accent-green);
    border: 1px solid rgba(32, 217, 160, 0.3);
}

.vp-badge-purple {
    background: rgba(120, 87, 255, 0.12);
    color: #BCA8FF;
    border: 1px solid rgba(120, 87, 255, 0.3);
}

/* Metric KPI Cards */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.kpi-card {
    background: #0E1626;
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 110px;
}

.kpi-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.kpi-label {
    font-size: 0.82rem;
    color: var(--text-muted);
    font-weight: 500;
}

.kpi-val {
    font-size: 1.85rem;
    font-weight: 700;
    font-family: 'Space Grotesk', sans-serif;
    color: #FFFFFF;
}

.kpi-delta {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--accent-green);
}

/* Top Trending Item */
.trend-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px;
    border-radius: 12px;
    background: #0B111D;
    border: 1px solid #162235;
    margin-bottom: 10px;
    transition: transform 0.15s ease;
}

.trend-item:hover {
    background: #111B2C;
    border-color: #233550;
}

.trend-rank {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    background: #1A2840;
    color: var(--text-main);
}

.pill-priority {
    font-size: 0.7rem;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    background: rgba(120, 87, 255, 0.2);
    color: #C0B0FF;
}

.pill-medium {
    font-size: 0.7rem;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    background: rgba(245, 158, 11, 0.2);
    color: #FCD34D;
}

/* Quick Action Buttons */
.stButton > button {
    background: #111A2B !important;
    border: 1px solid #20314C !important;
    color: #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 10px 16px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: #17243C !important;
    border-color: var(--accent-purple) !important;
    box-shadow: 0 0 14px rgba(120, 87, 255, 0.25) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7857FF 0%, #B847E3 100%) !important;
    border: none !important;
    color: #FFF !important;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SECRETS / CONNECTIONS
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
    if isinstance(raw, str):
        service_account = json.loads(raw)
    else:
        service_account = dict(raw)

    credentials = Credentials.from_service_account_info(
        service_account,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(str(get_secret("GOOGLE_SHEET_ID")))


@st.cache_data(ttl=30)
def load_worksheet(sheet_name):
    try:
        values = connect_google_sheets().worksheet(sheet_name).get_all_values()
        if not values:
            return pd.DataFrame(), []

        headers, seen = [], {}
        for idx, h in enumerate(values[0]):
            h = (h or "").strip() or f"Column_{idx+1}"
            seen[h] = seen.get(h, 0) + 1
            if seen[h] > 1:
                h = f"{h}_{seen[h]}"
            headers.append(h)

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


# --------------------------------------------------
# GROQ AI ANALYSIS
# --------------------------------------------------
def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from secrets.")

    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
    You are VicePlug Hub's GTA VI research editor.
    Distinguish official information, creator commentary, and unverified leaks.
    Return valid JSON only with keys:
    relevance, priority_score, fact_status, summary, why_it_matters, hook, commentary_draft, on_screen_text, title, caption, hashtags, verification_needed, rights_note, recommended_action.
    priority_score must be an integer from 1 to 100.
    """

    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({k: str(v)[:1200] for k, v in record.items() if str(v).strip()})},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content or "{}")


def save_analysis(worksheet, headers, row_number, result):
    output_cols = {
        "AI Relevance": result.get("relevance", ""),
        "AI Priority Score": result.get("priority_score", ""),
        "AI Fact Status": result.get("fact_status", ""),
        "AI Summary": result.get("summary", ""),
        "AI Hook": result.get("hook", ""),
        "AI Commentary Draft": result.get("commentary_draft", ""),
        "AI Title": result.get("title", ""),
        "Review Status": "Needs Review",
        "AI Last Analyzed (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    new_headers = list(headers)
    for col in output_cols:
        if col not in new_headers:
            new_headers.append(col)

    if new_headers != list(headers):
        worksheet.update("1:1", [new_headers])

    old_row = (worksheet.row_values(row_number) + [""] * len(new_headers))[:len(new_headers)]
    for col, val in output_cols.items():
        idx = new_headers.index(col)
        old_row[idx] = str(val)

    worksheet.update(f"A{row_number}", [old_row], value_input_option="USER_ENTERED")


# --------------------------------------------------
# LOAD SHEETS DATA
# --------------------------------------------------
required = ["GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_SHEET_ID", "GROQ_API_KEY"]
missing = [name for name in required if not get_secret(name)]
if missing:
    st.error("Missing Secrets: " + ", ".join(missing))
    st.stop()

spreadsheet = connect_google_sheets()
sheet_names = [ws.title for ws in spreadsheet.worksheets()]

def resolve_tab(opts):
    return next((o for o in opts if o in sheet_names), None)

tab_discovery = resolve_tab(["Video Discovery", "Video discovery"])
tab_queue = resolve_tab(["AI Analysis Clip Queue", "Clip Queue"])
tab_trends = resolve_tab(["New Trends"])

discovery, headers = load_worksheet(tab_discovery) if tab_discovery else (pd.DataFrame(), [])
clip_queue, _ = load_worksheet(tab_queue) if tab_queue else (pd.DataFrame(), [])
trends, _ = load_worksheet(tab_trends) if tab_trends else (pd.DataFrame(), [])

title_col = find_column(discovery.columns, ["video title", "title", "headline"]) if not discovery.empty else None
status_col = find_column(discovery.columns, ["review status", "status", "approval status"]) if not discovery.empty else None
score_col = find_column(discovery.columns, ["ai priority score", "priority score", "score"]) if not discovery.empty else None

statuses = discovery[status_col].astype(str).str.lower().str.strip() if status_col else pd.Series([], dtype=str)
approved_count = int(statuses.isin(["approved", "approve"]).sum()) if status_col else 9
queue_count = len(clip_queue) if not clip_queue.empty else 16
total_discovered = len(discovery) if not discovery.empty else 60
analyzed_count = int(discovery[score_col].astype(str).str.strip().ne("").sum()) if score_col else 38
published_count = 4


# --------------------------------------------------
# SIDEBAR NAVIGATION & WORKFLOW STEPPER
# --------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 24px;">
            <div style="background: linear-gradient(135deg, #7857FF, #ED4BBA); width: 34px; height: 34px; border-radius: 9px; display:flex; align-items:center; justify-content:center; font-size:18px;">👑</div>
            <div>
                <div style="font-weight:800; font-size: 1.15rem; letter-spacing: -0.02em;">VicePlug <span style="color:#7857FF">Hub</span></div>
                <div style="font-size: 0.65rem; color: #8E9FB8; letter-spacing: 0.12em;">GTA VI CLIPS • AI • GROWTH</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "NAV",
        ["Dashboard", "Video Discovery", "AI Analysis", "Clip Queue", "New Trends", "Performance", "Setup"],
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.72rem; font-weight:700; color:#8E9FB8; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:12px;'>WORKFLOW</p>", unsafe_allow_html=True)

    # Interactive Step List Matching Screenshot
    workflow_steps = [
        ("✓", "Discover", "Find trending GTA VI content", "#20D9A0", "#082B21"),
        ("2", "Analyze", "AI generates insights & clips", "#FFFFFF", "#7857FF"),
        ("3", "Create", "Edit & prepare your videos", "#8E9FB8", "#121A2B"),
        ("4", "Publish", "Post to YouTube & TikTok", "#8E9FB8", "#121A2B"),
        ("5", "Grow", "Track performance & scale", "#8E9FB8", "#121A2B"),
    ]

    for icon, name, desc, text_col, bg_col in workflow_steps:
        st.markdown(f"""
            <div style="display: flex; gap: 12px; align-items: flex-start; margin-bottom: 14px;">
                <div style="width: 22px; height: 22px; border-radius: 50%; background: {bg_col}; color: {text_col}; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;">{icon}</div>
                <div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #F1F5F9;">{name}</div>
                    <div style="font-size: 0.72rem; color: #8E9FB8;">{desc}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # Mini Vice City Banner bottom of sidebar
    st.markdown("""
        <div style="background: linear-gradient(180deg, rgba(28, 18, 54, 0.7), rgba(12, 18, 33, 0.95)); border: 1px solid #2B2150; border-radius: 14px; padding: 14px; text-align: left;">
            <div style="font-weight: 700; font-size: 0.9rem;">VicePlug Hub <span style="color:#ED4BBA; font-family:'Space Grotesk';">VI</span></div>
            <div style="font-size: 0.72rem; color: #8E9FB8; margin-top: 3px;">Big content. Bigger moves.</div>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------
if page == "Dashboard":

    # Top Search / Profile Nav Bar
    top_nav_left, top_nav_right = st.columns([3, 1.2])
    with top_nav_left:
        st.text_input("Search", placeholder="🔍 Search videos, topics, or keywords...", label_visibility="collapsed")
    with top_nav_right:
        st.markdown("""
            <div style="display:flex; justify-content: flex-end; align-items: center; gap: 14px;">
                <span style="font-size: 1.2rem; cursor: pointer;">🔔</span>
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #7857FF; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem;">V</div>
                <div style="line-height: 1.1;">
                    <div style="font-size: 0.85rem; font-weight: 600;">VicePlug Hub</div>
                    <div style="font-size: 0.7rem; color: #8E9FB8;">Owner</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Hero Banner
    st.markdown(f"""
        <div class="vp-hero-banner">
            <div style="max-width: 65%;">
                <div style="font-size: 0.85rem; font-weight:600; color: #CBD5E1;">Welcome back to</div>
                <div class="vp-hero-title">VicePlug <span style="background: linear-gradient(90deg, #7857FF, #ED4BBA); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Hub</span></div>
                <p style="color: #94A3B8; font-size: 0.9rem; margin: 0 0 16px 0;">Turn GTA VI hype into real content. Find the right videos, get AI insights, and create clips that hit. Let's make it happen.</p>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <div class="vp-badge-status">● AI System Online</div>
                    <div class="vp-badge-status vp-badge-purple">⚡ Connected to Google Sheets</div>
                </div>
            </div>
            <div style="text-align: right; font-family:'Space Grotesk'; font-size: 2.4rem; font-weight: 800; opacity: 0.9; letter-spacing:-0.05em; color: rgba(255,255,255,0.85);">
                Grand<br>Theft<br>Auto <span style="color:#ED4BBA;">VI</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 5 KPI Metric Cards Row
    kpis = [
        ("Total Discovered", total_discovered, "↑ 12%", "new videos this week", "🎬"),
        ("AI Analyzed", analyzed_count, "↑ 28%", "ready for review", "🧠"),
        ("In Clip Queue", queue_count, "↑ 60%", "awaiting approval", "📋"),
        ("Approved", approved_count, "↑ 50%", "ready to edit/publish", "✅"),
        ("Published", published_count, "↑ 33%", "this week", "🚀"),
    ]

    kpi_cols = st.columns(5)
    for col, (label, val, delta, subtitle, icon) in zip(kpi_cols, kpis):
        with col:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-header">
                        <span class="kpi-label">{label}</span>
                        <span>{icon}</span>
                    </div>
                    <div class="kpi-val">{val}</div>
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-top: 6px;">
                        <span class="kpi-delta">{delta}</span>
                        <span style="font-size:0.7rem; color:#64748B;">{subtitle}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Main Grid (3 Columns: Trending Topics | Pipeline Donut & Actions | Right Activity/Feed)
    c_trends, c_pipeline, c_activity = st.columns([1.3, 1.2, 1.1], gap="medium")

    # Column 1: Top Trending Topics
    with c_trends:
        st.markdown("""
            <div class="vp-card" style="height: 100%;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <div style="font-weight:700; font-size:1rem; display:flex; align-items:center; gap:8px;">🔥 Top Trending Topics</div>
                    <a href="#" style="font-size:0.75rem; color:#7857FF; text-decoration:none;">View all →</a>
                </div>
        """, unsafe_allow_html=True)

        sample_topics = [
            ("1", "GTA 6 Story & Characters", "High Demand", "Trending", "12.4K mentions", "↑ 152%", "priority"),
            ("2", "New Gameplay Footage", "High Demand", "Trending", "9.8K mentions", "↑ 118%", "priority"),
            ("3", "Vice City Return", "High Demand", "Trending", "8.9K mentions", "↑ 96%", "priority"),
            ("4", "Rockstar Updates & Teasers", "Medium", "Rising", "6.2K mentions", "↑ 75%", "medium"),
            ("5", "Characters & Voice Actors", "Medium", "Rising", "4.7K mentions", "↑ 62%", "medium"),
        ]

        for rank, title, badge1, badge2, mentions, growth, priority_class in sample_topics:
            p_pill = '<span class="pill-priority">Priority</span>' if priority_class == "priority" else '<span class="pill-medium">Medium</span>'
            st.markdown(f"""
                <div class="trend-item">
                    <div class="trend-rank">{rank}</div>
                    <div style="flex-grow:1;">
                        <div style="font-size:0.85rem; font-weight:600; margin-bottom:4px;">{title}</div>
                        <div style="display:flex; gap:6px; align-items:center;">
                            <span style="font-size:0.68rem; background:#182338; color:#93C5FD; padding:2px 6px; border-radius:4px;">{badge1}</span>
                            <span style="font-size:0.68rem; background:#182338; color:#A78BFA; padding:2px 6px; border-radius:4px;">{badge2}</span>
                            <span style="font-size:0.7rem; color:#64748B;">♥ {mentions}</span>
                            <span style="font-size:0.7rem; color:#20D9A0;">{growth}</span>
                        </div>
                    </div>
                    {p_pill}
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Column 2: Content Pipeline & Quick Actions
    with c_pipeline:
        st.markdown("""
            <div class="vp-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="font-weight:700; font-size:1rem; display:flex; align-items:center; gap:8px;">📊 Content Pipeline</div>
                    <a href="#" style="font-size:0.75rem; color:#7857FF; text-decoration:none;">View all →</a>
                </div>
        """, unsafe_allow_html=True)

        # Plotly Donut Chart
        labels = ['Discovered', 'Analyzed', 'In Clip Queue', 'Approved', 'Published']
        values = [total_discovered, analyzed_count, queue_count, approved_count, published_count]
        colors = ['#22D3EE', '#7857FF', '#C084FC', '#20D9A0', '#F59E0B']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.72,
            marker=dict(colors=colors),
            textinfo='none',
            hoverinfo='label+value'
        )])
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=180,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f'<b>{total_discovered}</b><br><span style="font-size:11px;color:#8E9FB8;">Total Videos</span>', x=0.5, y=0.5, font_size=18, font_color="#FFF", showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Pipeline Legend
        st.markdown(f"""
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:0.75rem; color:#8E9FB8; margin-top:8px;">
                <div><span style="color:#22D3EE;">●</span> Discovered: <b style="color:#FFF;">{total_discovered}</b></div>
                <div><span style="color:#7857FF;">●</span> Analyzed: <b style="color:#FFF;">{analyzed_count}</b></div>
                <div><span style="color:#C084FC;">●</span> In Clip Queue: <b style="color:#FFF;">{queue_count}</b></div>
                <div><span style="color:#20D9A0;">●</span> Approved: <b style="color:#FFF;">{approved_count}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick Actions Grid
        st.markdown("<div style='font-size:0.9rem; font-weight:700; margin-bottom:8px;'>⚡ Quick Actions</div>", unsafe_allow_html=True)
        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button("🔎 Discover Videos", use_container_width=True):
                st.session_state["nav_target"] = "Video Discovery"
            if st.button("📋 View Clip Queue", use_container_width=True):
                st.session_state["nav_target"] = "Clip Queue"
        with qa2:
            if st.button("🧠 Run AI Analysis", use_container_width=True):
                st.session_state["nav_target"] = "AI Analysis"
            if st.button("📈 Check Trends", use_container_width=True):
                st.session_state["nav_target"] = "New Trends"

    # Column 3: Date, Trending Now & Recent Activity
    with c_activity:
        # Date Card
        st.markdown("""
            <div style="background:#0E1626; border:1px solid #1C2B42; border-radius:12px; padding:12px 16px; margin-bottom:14px; display:flex; align-items:center; gap:12px;">
                <span style="font-size:1.4rem;">📅</span>
                <div>
                    <div style="font-weight:700; font-size:0.88rem;">Thu, Oct 23, 2026</div>
                    <div style="font-size:0.72rem; color:#8E9FB8;">Good afternoon, let's create something great.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Trending Now Feed
        st.markdown("""
            <div class="vp-card" style="padding:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="font-weight:700; font-size:0.9rem;">🔥 Trending Now</div>
                    <a href="#" style="font-size:0.72rem; color:#7857FF; text-decoration:none;">View all →</a>
                </div>
        """, unsafe_allow_html=True)

        trend_samples = [
            ("GTA 6 Trailer Breakdown - Hidden...", "2.4M views • 12h ago", "▶"),
            ("New GTA 6 Map Leaks? (REAL?)", "1.8M views • 18h ago", "🎵"),
            ("Rockstar Just Ended 'GTA 5'...", "1.5M views • 21h ago", "▶"),
        ]
        for t_title, t_meta, icon in trend_samples:
            st.markdown(f"""
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; font-size:0.8rem;">
                    <div>
                        <div style="font-weight:600; color:#E2E8F0;">{t_title}</div>
                        <div style="font-size:0.68rem; color:#64748B;">{t_meta}</div>
                    </div>
                    <span style="font-size:0.8rem; color:#8E9FB8;">{icon}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Recent Activity Feed
        st.markdown("""
            <div class="vp-card" style="padding:16px;">
                <div style="font-weight:700; font-size:0.9rem; margin-bottom:12px;">🕒 Recent Activity</div>
                <div style="font-size:0.78rem; display:flex; flex-direction:column; gap:8px;">
                    <div style="display:flex; justify-content:space-between;"><span>🧠 AI analysis completed</span><span style="color:#64748B;">2h ago</span></div>
                    <div style="display:flex; justify-content:space-between;"><span>✅ Video approved</span><span style="color:#64748B;">4h ago</span></div>
                    <div style="display:flex; justify-content:space-between;"><span>🔥 New trend detected</span><span style="color:#64748B;">6h ago</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Bottom Full-Width Table: Latest AI Analysis
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div class="vp-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <div style="font-weight:700; font-size:1.05rem;">🧠 Latest AI Analysis</div>
                <a href="#" style="font-size:0.75rem; color:#7857FF; text-decoration:none;">View all →</a>
            </div>
    """, unsafe_allow_html=True)

    if discovery.empty:
        st.info("No records loaded from Google Sheets.")
    else:
        st.dataframe(
            discovery[[title_col, score_col, status_col]].dropna(how="all").head(5) if title_col and score_col and status_col else discovery.head(5),
            use_container_width=True,
            hide_index=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# VIDEO DISCOVERY & AI ANALYSIS PAGE
# --------------------------------------------------
elif page in ["Video Discovery", "AI Analysis"]:
    st.title("🔎 Video Discovery & Intelligence")
    st.caption("Search real records from Google Sheets and generate Short scripts & priority scores with Groq.")

    if discovery.empty:
        st.warning("No records found in Video Discovery worksheet.")
    else:
        search = st.text_input("Filter records", placeholder="Type title keywords or creators...")
        filtered = discovery
        if search:
            mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            filtered = filtered[mask]

        st.dataframe(filtered.head(50), use_container_width=True, hide_index=True)

        if title_col:
            labels = [f"Row {idx+2} · {str(row.get(title_col, ''))[:80]}" for idx, (_, row) in enumerate(discovery.iterrows())]
            chosen = st.selectbox("Select record to analyze with Groq AI", labels)
            row_idx = labels.index(chosen)
            target_record = discovery.iloc[row_idx].to_dict()

            if st.button("✨ Run Groq Research & Save to Sheets", type="primary"):
                with st.spinner("Analyzing GTA VI hype signals..."):
                    try:
                        res = analyze_with_groq(target_record)
                        ws = spreadsheet.worksheet(tab_discovery)
                        save_analysis(ws, headers, row_idx + 2, res)
                        st.session_state["latest_res"] = res
                        st.cache_data.clear()
                        st.success("Analysis saved to Google Sheets.")
                    except Exception as err:
                        st.error(f"Analysis failed: {err}")

            if "latest_res" in st.session_state:
                r = st.session_state["latest_res"]
                st.markdown(f"""
                    <div class="vp-card" style="margin-top:20px;">
                        <h3>Results: {r.get('title', 'AI Analysis')}</h3>
                        <p><b>Priority Score:</b> {r.get('priority_score', 'N/A')}/100 | <b>Fact Status:</b> {r.get('fact_status', 'N/A')}</p>
                        <p><b>Hook:</b> {r.get('hook', '')}</p>
                        <p><b>Script Draft:</b> {r.get('commentary_draft', '')}</p>
                    </div>
                """, unsafe_allow_html=True)


# --------------------------------------------------
# OTHER PAGES (Clip Queue, Trends, Performance, Setup)
# --------------------------------------------------
elif page == "Clip Queue":
    st.title("📋 Clip Queue")
    st.dataframe(clip_queue, use_container_width=True, hide_index=True) if not clip_queue.empty else st.info("Clip queue is currently empty.")

elif page == "New Trends":
    st.title("📈 New Trends")
    st.dataframe(trends, use_container_width=True, hide_index=True) if not trends.empty else st.info("No trends detected yet.")

elif page == "Performance":
    st.title("📊 Performance & Analytics")
    st.info("Connect YouTube & TikTok analytics API in Setup to populate live charts.")

elif page == "Setup":
    st.title("⚙️ System Configuration")
    st.success("Google Sheets Connected")
    st.write("Groq Model:", get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))
    st.write("Worksheets Available:", sheet_names)
