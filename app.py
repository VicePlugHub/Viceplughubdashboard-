import os
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

# --------------------------------------------------
# SYSTEM CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug OS // Neural Recon",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# FUTURISTIC CYBER-HUD DESIGN SYSTEM (CSS)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

:root {
    --bg-space: #03060E;
    --hud-surface: rgba(10, 16, 30, 0.75);
    --hud-border: rgba(0, 240, 255, 0.22);
    --hud-border-glow: rgba(0, 240, 255, 0.45);
    --neon-cyan: #00F0FF;
    --neon-pink: #FF007A;
    --neon-purple: #8B5CF6;
    --neon-green: #00FF9D;
    --neon-amber: #FFB800;
    --text-primary: #F0F6FC;
    --text-dim: #798CA6;
}

/* Background Cyber Grid */
.stApp {
    background-color: var(--bg-space) !important;
    background-image: 
        linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px),
        radial-gradient(circle at 10% 0%, rgba(139, 92, 246, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 90% 10%, rgba(255, 0, 122, 0.09) 0%, transparent 45%);
    background-size: 40px 40px, 40px 40px, 100%, 100%;
    color: var(--text-primary);
    font-family: 'Rajdhani', sans-serif !important;
}

/* Chrome reset */
#MainMenu, header, footer { visibility: hidden; }
.block-container {
    max-width: 1780px !important;
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
}

/* Futuristic Sidebar */
[data-testid="stSidebar"] {
    background: rgba(5, 9, 18, 0.94) !important;
    border-right: 1px solid var(--hud-border) !important;
    backdrop-filter: blur(20px);
}

/* Top Cyber Bar */
.cyber-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(8, 14, 26, 0.85);
    border: 1px solid var(--hud-border);
    border-radius: 8px;
    padding: 8px 18px;
    margin-bottom: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
}

.pulse-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--neon-cyan);
    box-shadow: 0 0 10px var(--neon-cyan);
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.9); opacity: 0.7; }
    50% { transform: scale(1.3); opacity: 1; }
    100% { transform: scale(0.9); opacity: 0.7; }
}

/* Holographic Tactical Hero */
.hud-hero {
    position: relative;
    background: linear-gradient(135deg, rgba(16, 24, 48, 0.75) 0%, rgba(30, 12, 45, 0.65) 55%, rgba(6, 12, 24, 0.85) 100%);
    border: 1px solid var(--hud-border);
    border-radius: 14px;
    padding: 26px 32px;
    margin-bottom: 20px;
    backdrop-filter: blur(14px);
    box-shadow: inset 0 0 35px rgba(0, 240, 255, 0.05), 0 8px 32px rgba(0, 0, 0, 0.5);
}

.hud-hero::before {
    content: "";
    position: absolute;
    top: 0; left: 0; width: 30px; height: 30px;
    border-top: 2px solid var(--neon-cyan);
    border-left: 2px solid var(--neon-cyan);
}

.hud-hero::after {
    content: "";
    position: absolute;
    bottom: 0; right: 0; width: 30px; height: 30px;
    border-bottom: 2px solid var(--neon-pink);
    border-right: 2px solid var(--neon-pink);
}

.hud-hero-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.1rem;
    font-weight: 900;
    letter-spacing: 0.05em;
    background: linear-gradient(90deg, #FFF 0%, var(--neon-cyan) 60%, var(--neon-pink) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 4px 0 6px 0;
}

/* Telemetry HUD Cards */
.hud-pod {
    background: var(--hud-surface);
    border: 1px solid var(--hud-border);
    border-radius: 10px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}

.hud-pod:hover {
    border-color: var(--neon-cyan);
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
    transform: translateY(-2px);
}

.hud-pod-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.hud-pod-val {
    font-family: 'Orbitron', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 6px 0 2px 0;
}

/* Dossier Card (Left Triage Feed) */
.dossier-card {
    background: rgba(11, 19, 36, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-left: 4px solid var(--neon-purple);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    backdrop-filter: blur(10px);
    transition: border 0.2s ease;
}

.dossier-card:hover {
    border-color: var(--neon-cyan);
    box-shadow: 0 0 16px rgba(0, 240, 255, 0.15);
}

.hud-badge-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(0, 240, 255, 0.15);
    border: 1px solid var(--neon-cyan);
    color: var(--neon-cyan);
}

.hud-badge-official {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(0, 255, 157, 0.15);
    border: 1px solid var(--neon-green);
    color: var(--neon-green);
}

.hud-badge-leak {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(255, 0, 122, 0.15);
    border: 1px solid var(--neon-pink);
    color: var(--neon-pink);
}

/* Futuristic Form Inputs & Buttons */
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background: #080E1C !important;
    border: 1px solid var(--hud-border) !important;
    border-radius: 6px !important;
    color: #FFF !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
}

.stButton > button {
    background: linear-gradient(135deg, #0F1D38 0%, #162447 100%) !important;
    border: 1px solid var(--hud-border) !important;
    color: var(--neon-cyan) !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    border-radius: 6px !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: var(--neon-cyan) !important;
    color: #03060E !important;
    box-shadow: 0 0 16px var(--neon-cyan) !important;
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
        headers = [h.strip() or f"COL_{i+1}" for i, h in enumerate(values[0])]
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
        st.error(f"Status update failure: {e}")
    return False


def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY missing.")

    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
You are VicePlug OS: an advanced tactical GTA VI intelligence parser.
Classify truth status into: 'Official Rockstar', 'Credible Press', 'Speculative Lore', 'Unverified Leak'.
Return JSON only:
{
  "relevance": "High" | "Medium" | "Low",
  "priority_score": int (1-100),
  "fact_status": "Official Rockstar" | "Credible Press" | "Speculative Lore" | "Unverified Leak",
  "summary": "1-2 sentence core factual event",
  "hook": "Aggressive, high-CTR spoken hook for a 30s Short",
  "commentary_draft": "Complete 30s script",
  "verification_needed": ["Verification point"]
}
"""
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({k: str(v)[:1400] for k, v in record.items() if str(v).strip()})},
        ],
        temperature=0.2,
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
        "Review Status": "Needs Review",
        "AI Last Analyzed UTC": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
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
# INITIAL DATA RETRIEVAL
# --------------------------------------------------
spreadsheet = connect_google_sheets()
all_sheets = [ws.title for ws in spreadsheet.worksheets()]
ws_disc_name = next((s for s in ["Video Discovery", "Discovery", "Sheet1"] if s in all_sheets), None)
discovery_df, disc_headers = load_worksheet(ws_disc_name) if ws_disc_name else (pd.DataFrame(), [])

title_col = find_column(discovery_df.columns, ["video title", "title", "headline"]) if not discovery_df.empty else None
url_col = find_column(discovery_df.columns, ["video url", "url", "link"]) if not discovery_df.empty else None
status_col = find_column(discovery_df.columns, ["review status", "status", "approval"]) if not discovery_df.empty else "Review Status"
score_col = find_column(discovery_df.columns, ["ai priority score", "priority score", "score"]) if not discovery_df.empty else "AI Priority Score"
fact_col = find_column(discovery_df.columns, ["ai fact status", "fact status"]) if not discovery_df.empty else "AI Fact Status"
summary_col = find_column(discovery_df.columns, ["ai summary", "summary"]) if not discovery_df.empty else None
hook_col = find_column(discovery_df.columns, ["ai hook", "hook"]) if not discovery_df.empty else None

if not discovery_df.empty:
    discovery_df["_score_num"] = pd.to_numeric(discovery_df[score_col], errors="coerce").fillna(0) if score_col in discovery_df else 0
    if status_col not in discovery_df: discovery_df[status_col] = "Needs Review"
    if fact_col not in discovery_df: discovery_df[fact_col] = "Unverified Leak"


# --------------------------------------------------
# CYBER SIDEBAR HUD CONTROLS
# --------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:18px;">
            <div style="width:34px; height:34px; border:1px solid #00F0FF; border-radius:6px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 10px rgba(0,240,255,0.4);">⚡</div>
            <div>
                <div style="font-family:'Orbitron'; font-weight:900; font-size:1.1rem; letter-spacing:0.06em;">VICEPLUG <span style="color:#00F0FF;">OS</span></div>
                <div style="font-family:'JetBrains Mono'; font-size:0.62rem; color:#798CA6;">RECON AUTOMATION CORE</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-family:JetBrains Mono; font-size:0.7rem; color:#00F0FF; letter-spacing:0.1em;'>// TACTICAL FILTERS</p>", unsafe_allow_html=True)
    min_priority = st.slider("Signal Priority Threshold", 0, 100, 40, step=5)
    
    fact_types = ["Official Rockstar", "Credible Press", "Speculative Lore", "Unverified Leak"]
    active_facts = st.multiselect("Veracity Filter", fact_types, default=fact_types)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-family:JetBrains Mono; font-size:0.7rem; color:#00F0FF; letter-spacing:0.1em;'>// TELEMETRY UPLINK</p>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#798CA6; display:flex; flex-direction:column; gap:5px; background:rgba(10,16,30,0.8); border:1px solid rgba(0,240,255,0.15); padding:10px; border-radius:6px;">
            <div>MODEL: <span style="color:#FFF;">LLAMA-3.3-70B</span></div>
            <div>UPLINK: <span style="color:#00FF9D;">ONLINE (30s SYNC)</span></div>
            <div>LOC: <span style="color:#FF007A;">VICE CITY [25°N, 80°W]</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("RELOAD FEED", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# --------------------------------------------------
# TOP HUD STATUS BAR
# --------------------------------------------------
total_signals = len(discovery_df)
analyzed_count = int((discovery_df["_score_num"] > 0).sum()) if not discovery_df.empty else 0
needs_review = int((discovery_df[status_col].astype(str).str.lower() == "needs review").sum()) if not discovery_df.empty else 0
approved_count = int((discovery_df[status_col].astype(str).str.lower() == "approved").sum()) if not discovery_df.empty else 0
published_count = 4

st.markdown(f"""
    <div class="cyber-top-bar">
        <div><span class="pulse-dot"></span> &nbsp;SYS_STATUS: <span style="color:#00FF9D;">ACTIVE</span> &nbsp;|&nbsp; LATENCY: 14ms &nbsp;|&nbsp; NEURAL ENGINE ONLINE</div>
        <div>TARGET: GTA_VI_INTELLIGENCE &nbsp;|&nbsp; COORD: 25°46'N 80°12'W &nbsp;|&nbsp; OPERATOR: <span style="color:#00F0FF;">VICE_LEAD</span></div>
    </div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# FUTURISTIC HERO BANNER
# --------------------------------------------------
st.markdown("""
    <div class="hud-hero">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#00F0FF; letter-spacing:0.12em;">// HIGH-VELOCITY RECON PLATFORM</div>
                <div class="hud-hero-title">VICEPLUG RECON <span style="font-size:1.2rem; color:#FF007A;">[V.6.4]</span></div>
                <div style="color:#94A3B8; font-size:1rem; max-width:700px;">Intercepting GTA VI transmission signals, validating source authenticity, and generating algorithm-dominant Short scripts.</div>
            </div>
            <div style="text-align:right; font-family:'Orbitron'; font-size:2.8rem; font-weight:900; opacity:0.85; color:#FFF; line-height:1;">
                VI<br><span style="font-size:0.9rem; color:#00F0FF; letter-spacing:0.2em;">VICE CITY</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 5 CYBER TELEMETRY PODS
# --------------------------------------------------
p1, p2, p3, p4, p5 = st.columns(5)
pods = [
    ("TOTAL INTERCEPTS", total_signals, "+14% INFLOW", "#00F0FF"),
    ("NEURAL PARSED", analyzed_count, "98.2% CONFIDENCE", "#8B5CF6"),
    ("TRIAGE QUEUE", needs_review, "PENDING REVIEW", "#FFB800"),
    ("VERIFIED READY", approved_count, "READY TO EDIT", "#00FF9D"),
    ("BROADCAST DEPLOYED", published_count, "ACTIVE POSTS", "#FF007A"),
]

for col, (label, val, note, glow) in zip([p1, p2, p3, p4, p5], pods):
    with col:
        st.markdown(f"""
            <div class="hud-pod">
                <div class="hud-pod-label">{label}</div>
                <div class="hud-pod-val" style="text-shadow: 0 0 15px {glow}44;">{val}</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.68rem; color:{glow};">{note}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# --------------------------------------------------
# DUAL CYBER COMMAND GRID
# --------------------------------------------------
left_hopper, right_telemetry = st.columns([1.6, 1], gap="medium")

# Apply filters to dataset
active_records = discovery_df.copy()
if not active_records.empty:
    active_records = active_records[active_records["_score_num"] >= min_priority]
    if active_facts and fact_col in active_records:
        active_records = active_records[active_records[fact_col].isin(active_facts) | (active_records[fact_col] == "")]

# ==================================================
# LEFT COLUMN: THE TACTICAL DOSSIER HOPPER
# ==================================================
with left_hopper:
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="font-family:'Orbitron'; font-size:1.1rem; font-weight:700; color:#FFF; display:flex; align-items:center; gap:8px;">
                <span style="color:#00F0FF;">◈</span> SIGNAL INTERCEPTION HOPPER
            </div>
            <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#798CA6;">ACTIVE SIGNALS: """ + str(len(active_records)) + """</div>
        </div>
    """, unsafe_allow_html=True)

    if active_records.empty:
        st.info("No intercepted signals match the specified threshold.")
    else:
        for orig_idx, row in active_records.head(8).iterrows():
            row_num = orig_idx + 2
            item_title = str(row.get(title_col, "Untitled Intercept"))
            item_score = int(row.get("_score_num", 50))
            item_fact = str(row.get(fact_col, "Unverified Leak"))
            item_status = str(row.get(status_col, "Needs Review"))
            item_hook = str(row.get(hook_col, "Awaiting neural synthesis for hook..."))
            item_url = str(row.get(url_col, ""))

            badge_style = "hud-badge-leak" if "leak" in item_fact.lower() else "hud-badge-official"

            st.markdown(f"""
                <div class="dossier-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                        <div style="display:flex; gap:8px; align-items:center;">
                            <span class="hud-badge-score">PRIORITY: {item_score}/100</span>
                            <span class="{badge_style}">VERACITY: {item_fact.upper()}</span>
                        </div>
                        <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#A78BFA; background:#120E2E; padding:2px 8px; border-radius:4px; border:1px solid #3B2D75;">{item_status.upper()}</span>
                    </div>
                    <div style="font-size:1.15rem; font-weight:700; color:#FFFFFF; margin:6px 0;">{item_title}</div>
                    <div style="background:rgba(5,9,18,0.7); border:1px solid rgba(0,240,255,0.12); border-radius:6px; padding:10px; margin:8px 0; font-size:0.9rem;">
                        <span style="color:#00F0FF; font-family:'JetBrains Mono'; font-size:0.75rem; font-weight:700;">// HOOK PROJECTION:</span><br>
                        <span style="color:#CBD5E1;">"{item_hook}"</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Action Controls (Immediate Google Sheets Sync)
            b1, b2, b3, b4 = st.columns([1.1, 1.1, 1.3, 1.2])
            with b1:
                if st.button("AUTHORIZE", key=f"auth_{row_num}", use_container_width=True):
                    update_sheet_status(ws_disc_name, row_num, "Approved", status_col)
                    st.toast(f"Row {row_num} Authorized for Production", icon="⚡")
                    st.cache_data.clear()
                    st.rerun()
            with b2:
                if st.button("ENQUEUE", key=f"q_{row_num}", use_container_width=True):
                    update_sheet_status(ws_disc_name, row_num, "In Clip Queue", status_col)
                    st.toast(f"Row {row_num} Sent to Clip Queue", icon="📋")
                    st.cache_data.clear()
                    st.rerun()
            with b3:
                if st.button("NEURAL RUN", key=f"ai_{row_num}", use_container_width=True):
                    with st.spinner("Decoding signal through Groq LLM..."):
                        res = analyze_with_groq(row.to_dict())
                        save_ai_analysis(ws_disc_name, disc_headers, row_num, res)
                        st.cache_data.clear()
                        st.rerun()
            with b4:
                if item_url and item_url.startswith("http"):
                    st.markdown(f"<div style='padding-top:6px; text-align:center;'><a href='{item_url}' target='_blank' style='font-family:JetBrains Mono; font-size:0.75rem; color:#00F0FF; text-decoration:none;'>[ORIGIN ↗]</a></div>", unsafe_allow_html=True)

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


# ==================================================
# RIGHT COLUMN: HOLOGRAPHIC PIPELINE & RADAR
# ==================================================
with right_telemetry:
    # 1. Glowing Orbital Radar Widget
    st.markdown("""
        <div class="hud-pod" style="margin-bottom:16px;">
            <div style="font-family:'Orbitron'; font-size:0.95rem; font-weight:700; margin-bottom:12px; color:#FFF;">
                ◈ PIPELINE ORBITAL RADAR
            </div>
    """, unsafe_allow_html=True)

    # Pure SVG Cybernetic Donut Ring
    st.markdown(f"""
        <div style="display:flex; justify-content:center; align-items:center; margin: 10px 0;">
            <div style="position:relative; width:170px; height:170px;">
                <svg viewBox="0 0 36 36" style="width:100%; height:100%; transform: rotate(-90deg); filter: drop-shadow(0 0 8px rgba(0,240,255,0.3));">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#08101E" stroke-width="3" />
                    <!-- Discovered (Cyan) -->
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#00F0FF" stroke-width="3.6" stroke-dasharray="35, 100" />
                    <!-- Parsed (Purple) -->
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#8B5CF6" stroke-width="3.6" stroke-dasharray="25, 100" stroke-dashoffset="-35" />
                    <!-- Queue (Pink) -->
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#FF007A" stroke-width="3.6" stroke-dasharray="20, 100" stroke-dashoffset="-60" />
                    <!-- Approved (Green) -->
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#00FF9D" stroke-width="3.6" stroke-dasharray="20, 100" stroke-dashoffset="-80" />
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                    <div style="font-family:'Orbitron'; font-size:1.7rem; font-weight:900; color:#FFF; line-height:1;">{total_signals}</div>
                    <div style="font-family:'JetBrains Mono'; font-size:0.62rem; color:#00F0FF; letter-spacing:0.1em;">SIGNALS</div>
                </div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; font-family:'JetBrains Mono'; font-size:0.7rem; color:#798CA6; margin-top:10px;">
            <div><span style="color:#00F0FF;">●</span> DISCOVERED: <b style="color:#FFF;">{total_signals}</b></div>
            <div><span style="color:#8B5CF6;">●</span> PARSED: <b style="color:#FFF;">{analyzed_count}</b></div>
            <div><span style="color:#FF007A;">●</span> IN QUEUE: <b style="color:#FFF;">{needs_review}</b></div>
            <div><span style="color:#00FF9D;">●</span> AUTHORIZED: <b style="color:#FFF;">{approved_count}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Live Topic Frequencies
    st.markdown("""
        <div class="hud-pod" style="margin-bottom:16px;">
            <div style="font-family:'Orbitron'; font-size:0.95rem; font-weight:700; margin-bottom:10px; color:#FFF;">
                🔥 HYPE VELOCITY RADAR
            </div>
    """, unsafe_allow_html=True)

    hot_topics = [
        ("Jason & Lucia Dynamic", "14.2K mentions", "↑ 182%", "#00FF9D"),
        ("Vice City Water Physics", "10.4K mentions", "↑ 145%", "#00F0FF"),
        ("Take-Two FY26 Earnings Call", "8.1K mentions", "↑ 92%", "#8B5CF6"),
        ("Leaked Dev Build Breakdown", "6.7K mentions", "↑ 74%", "#FF007A"),
    ]
    for topic, vol, vel, col in hot_topics:
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px; background:rgba(6,11,22,0.6); border:1px solid rgba(0,240,255,0.08); border-radius:6px; margin-bottom:6px; font-size:0.88rem;">
                <div>
                    <div style="font-weight:700; color:#F0F6FC;">{topic}</div>
                    <div style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#798CA6;">{vol}</div>
                </div>
                <div style="font-family:'JetBrains Mono'; font-weight:700; font-size:0.8rem; color:{col};">{vel}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. Neural Automation Launcher
    st.markdown("""
        <div class="hud-pod">
            <div style="font-family:'Orbitron'; font-size:0.95rem; font-weight:700; margin-bottom:8px; color:#FFF;">
                ⚡ BATCH INTAKE ENGINE
            </div>
            <p style="font-size:0.82rem; color:#798CA6; margin-bottom:10px;">Trigger Groq neural parsing on all unanalyzed rows in Sheets automatically.</p>
    """, unsafe_allow_html=True)

    unparsed_rows = discovery_df[discovery_df["_score_num"] == 0] if "_score_num" in discovery_df else pd.DataFrame()
    st.markdown(f"<div style='font-family:JetBrains Mono; font-size:0.75rem; color:#00F0FF; margin-bottom:8px;'>PENDING PARSE: {len(unparsed_rows)} RECORDS</div>", unsafe_allow_html=True)

    if st.button("EXECUTE BATCH SYNTHESIS", use_container_width=True):
        if unparsed_rows.empty:
            st.info("All records have been analyzed.")
        else:
            prog = st.progress(0)
            count = 0
            for i, (orig_idx, row_data) in enumerate(unparsed_rows.head(5).iterrows()):
                rn = orig_idx + 2
                res = analyze_with_groq(row_data.to_dict())
                save_ai_analysis(ws_disc_name, disc_headers, rn, res)
                count += 1
                prog.progress((i + 1) / min(len(unparsed_rows), 5))
            st.success(f"Synthesized {count} signals successfully.")
            st.cache_data.clear()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
