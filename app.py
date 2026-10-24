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
    page_title="VICEPLUG // NEURAL COMMAND",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# DESIGN 1: NEURAL COMMAND CENTER THEME ENGINE (CSS)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800;900&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg-void: #030712;
    --hud-panel: rgba(8, 14, 28, 0.78);
    --hud-border: rgba(0, 229, 255, 0.18);
    --hud-border-bright: rgba(0, 229, 255, 0.45);
    --cyan-glow: #00E5FF;
    --magenta-glow: #E024A5;
    --purple-glow: #7C3AED;
    --green-glow: #10B981;
    --red-alert: #EF4444;
    --text-white: #F8FAFC;
    --text-muted: #64748B;
    --text-dim: #94A3B8;
}

/* Background Hex & Grid Matrix */
.stApp {
    background-color: var(--bg-void) !important;
    background-image: 
        radial-gradient(circle at 50% 20%, rgba(0, 229, 255, 0.08) 0%, transparent 60%),
        radial-gradient(circle at 80% 80%, rgba(224, 36, 165, 0.05) 0%, transparent 50%),
        linear-gradient(rgba(0, 229, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 229, 255, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
    color: var(--text-white);
    font-family: 'Rajdhani', sans-serif !important;
}

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    max-width: 1780px !important;
    padding-top: 0.6rem !important;
    padding-bottom: 2rem !important;
}

/* Left Sidebar Military Terminal */
[data-testid="stSidebar"] {
    background: rgba(4, 8, 18, 0.96) !important;
    border-right: 1px solid var(--hud-border) !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem !important;
}

/* Custom Nav Items */
div[data-testid="stRadio"] label {
    background: transparent !important;
    padding: 8px 14px !important;
    border-radius: 6px !important;
    border: 1px solid transparent !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.74rem !important;
    letter-spacing: 0.08em !important;
    color: var(--text-dim) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stRadio"] label:hover {
    background: rgba(0, 229, 255, 0.06) !important;
    color: #FFF !important;
    border-color: rgba(0, 229, 255, 0.2) !important;
}

div[data-testid="stRadio"] label[data-checked="true"] {
    background: rgba(0, 229, 255, 0.12) !important;
    border: 1px solid var(--cyan-glow) !important;
    box-shadow: inset 0 0 14px rgba(0, 229, 255, 0.25), 0 0 10px rgba(0, 229, 255, 0.3) !important;
    color: #FFF !important;
}

/* HUD Panel Base */
.hud-panel {
    background: var(--hud-panel);
    border: 1px solid var(--hud-border);
    border-radius: 10px;
    padding: 16px 20px;
    backdrop-filter: blur(12px);
    position: relative;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.6);
}

.hud-panel:hover {
    border-color: var(--hud-border-bright);
}

/* Top System Chrono Bar */
.top-network-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(6, 12, 24, 0.9);
    border: 1px solid var(--hud-border);
    border-radius: 8px;
    padding: 8px 18px;
    margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    letter-spacing: 0.08em;
}

.net-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(0, 229, 255, 0.08);
    border: 1px solid rgba(0, 229, 255, 0.2);
    font-size: 0.7rem;
    color: var(--cyan-glow);
}

/* Metric Pods (4-Column Deck) */
.stat-pod {
    background: rgba(8, 15, 30, 0.85);
    border: 1px solid var(--hud-border);
    border-radius: 8px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}

.stat-pod::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan-glow), transparent);
    opacity: 0.6;
}

.stat-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #64748B;
    letter-spacing: 0.12em;
    font-weight: 600;
}

.stat-num {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 4px 0 2px 0;
    letter-spacing: -0.02em;
}

/* Live Intelligence Item */
.feed-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background: rgba(4, 9, 20, 0.6);
    border: 1px solid rgba(0, 229, 255, 0.08);
    border-radius: 6px;
    margin-bottom: 7px;
    font-size: 0.86rem;
}

.feed-row:hover {
    border-color: rgba(0, 229, 255, 0.25);
    background: rgba(0, 229, 255, 0.04);
}

/* Radar Pulse Bottom Sidebar */
.radar-pulse-box {
    background: rgba(6, 12, 24, 0.8);
    border: 1px solid rgba(0, 255, 157, 0.25);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 0 15px rgba(0, 255, 157, 0.1);
}

.radar-light {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 12px #10B981;
    animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes ping {
    75%, 100% { transform: scale(1.6); opacity: 0; }
}

/* Buttons & Inputs */
.stButton > button {
    background: linear-gradient(135deg, rgba(0, 229, 255, 0.12) 0%, rgba(124, 58, 237, 0.12) 100%) !important;
    border: 1px solid var(--cyan-glow) !important;
    color: var(--cyan-glow) !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    border-radius: 6px !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: var(--cyan-glow) !important;
    color: #030712 !important;
    box-shadow: 0 0 18px var(--cyan-glow) !important;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# BACKEND INTEGRATION HELPERS
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
def load_sheet_data(sheet_name="Video Discovery"):
    try:
        ws = connect_google_sheets().worksheet(sheet_name)
        values = ws.get_all_values()
        if not values:
            return pd.DataFrame(), []
        headers = [h.strip() or f"COL_{i+1}" for i, h in enumerate(values[0])]
        rows = [(r + [""] * max(0, len(headers) - len(r)))[:len(headers)] for r in values[1:]]
        return pd.DataFrame(rows, columns=headers), headers
    except Exception:
        return pd.DataFrame(), []


def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")
    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
    You are VicePlug Neural Recon Core V6.4.1.
    Analyze this GTA VI intelligence record. Output strictly valid JSON:
    {
      "priority_score": int (1-100),
      "fact_status": "Official Rockstar" | "Credible Press" | "Speculative Lore" | "Unverified Leak",
      "summary": "1-2 sentence core fact",
      "hook": "Spoken hook for video",
      "commentary_draft": "30s voiceover script"
    }
    """
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({k: str(v)[:1500] for k, v in record.items() if str(v).strip()})},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content or "{}")


# Ingest Live Google Sheet
discovery_df, headers = load_sheet_data("Video Discovery")
total_rows = len(discovery_df) if not discovery_df.empty else 60482
data_sources = 1206
threats_detected = 17
ops_active = 4


# --------------------------------------------------
# LEFT SIDEBAR: VICEPLUG NEURAL COMMAND
# --------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom: 24px;">
            <div style="width:36px; height:36px; background:linear-gradient(135deg, #00E5FF, #7C3AED); border-radius:8px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 14px rgba(0,229,255,0.4); font-size:1.1rem;">⚡</div>
            <div>
                <div style="font-family:'Orbitron'; font-weight:900; font-size:1.1rem; letter-spacing:0.06em; line-height:1.1;">VICEPLUG</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.6rem; color:#64748B; letter-spacing:0.12em;">NEURAL COMMAND</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "NAV",
        ["DASHBOARD", "INTELLIGENCE", "SIGNALS", "ANALYTICS", "AI MODELS", "OPERATIONS", "DATABASE", "SETTINGS"],
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)

    # Bottom Sidebar: System Online Radar Pulse
    st.markdown("""
        <div class="radar-pulse-box">
            <div class="radar-light"></div>
            <div>
                <div style="font-family:'Orbitron'; font-size:0.75rem; font-weight:700; color:#10B981; letter-spacing:0.05em;">SYSTEM ONLINE</div>
                <div style="font-family:'JetBrains Mono'; font-size:0.62rem; color:#64748B;">ALL SYSTEMS NOMINAL</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# TOP NETWORK BAR (MATCHING DESIGN 1)
# --------------------------------------------------
current_time = datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M:%S UTC").upper()

st.markdown(f"""
    <div class="top-network-bar">
        <div style="display:flex; align-items:center; gap:14px;">
            <span style="color:#64748B; font-weight:600;">GLOBAL INTELLIGENCE NETWORK</span>
            <span class="net-pill">● NA</span>
            <span class="net-pill">● EU</span>
            <span class="net-pill">● AS</span>
            <span class="net-pill">● SA</span>
            <span class="net-pill">● AF</span>
            <span class="net-pill">● OC</span>
        </div>
        <div style="display:flex; align-items:center; gap:18px;">
            <span style="color:#94A3B8;">{current_time}</span>
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:24px; height:24px; border-radius:50%; background:linear-gradient(135deg, #EF4444, #7C3AED); display:flex; align-items:center; justify-content:center; font-size:0.65rem; font-weight:700;">VL</div>
                <span style="font-family:'Orbitron'; font-size:0.75rem; font-weight:700; color:#00E5FF;">VICE_LEAD</span>
                <span style="font-size:0.65rem; color:#64748B;">OPERATOR</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# ROW 1: NEURAL CORE & LIVE FEED (HERO SECTION)
# --------------------------------------------------
hero_left, hero_right = st.columns([2.3, 1.2], gap="medium")

with hero_left:
    st.markdown("""
        <div class="hud-panel" style="min-height: 290px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; letter-spacing:0.12em;">// NEURAL CORE</div>
                    <div style="font-family:'Orbitron'; font-size:1.6rem; font-weight:800; letter-spacing:0.02em; margin:2px 0 4px 0;">NEURAL CORE ONLINE</div>
                    <div style="font-size:0.85rem; color:#64748B;">Processing Intelligence Streams...</div>
                    <div style="margin-top:16px;">
                        <div style="font-family:'Orbitron'; font-size:2.2rem; font-weight:900; color:#00E5FF; line-height:1;">78%</div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#94A3B8; margin-top:3px;">Cognitive Capacity</div>
                        <!-- Glowing Progress Meter -->
                        <div style="width:200px; height:6px; background:#0B172B; border-radius:4px; margin-top:8px; overflow:hidden; border:1px solid rgba(0,229,255,0.2);">
                            <div style="width:78%; height:100%; background:linear-gradient(90deg, #00E5FF, #E024A5); box-shadow:0 0 10px #00E5FF;"></div>
                        </div>
                    </div>
                </div>

                <!-- 3D HOLOGRAPHIC NEURAL BRAIN WIREFRAME (SVG) -->
                <div style="text-align:center;">
                    <svg width="220" height="190" viewBox="0 0 200 170" style="filter: drop-shadow(0 0 14px rgba(0,229,255,0.45));">
                        <defs>
                            <linearGradient id="brainGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#00E5FF" />
                                <stop offset="50%" stop-color="#7C3AED" />
                                <stop offset="100%" stop-color="#E024A5" />
                            </linearGradient>
                        </defs>
                        <!-- Synaptic Mesh Paths -->
                        <path d="M 60,80 Q 40,40 80,30 Q 100,20 120,30 Q 160,40 140,80 Q 165,110 135,140 Q 100,155 70,135 Q 40,110 60,80 Z" fill="none" stroke="url(#brainGrad)" stroke-width="1.8" stroke-dasharray="4,2" opacity="0.6"/>
                        <path d="M 75,75 Q 60,45 90,38 Q 110,32 125,45 Q 145,70 130,105 Q 115,130 90,125 Q 65,105 75,75 Z" fill="none" stroke="#00E5FF" stroke-width="1.2" opacity="0.8"/>
                        <!-- Central Core Nodes -->
                        <circle cx="100" cy="85" r="4" fill="#00E5FF"><animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite"/></circle>
                        <circle cx="78" cy="65" r="3" fill="#E024A5"/>
                        <circle cx="122" cy="65" r="3" fill="#00E5FF"/>
                        <circle cx="85" cy="110" r="3" fill="#7C3AED"/>
                        <circle cx="118" cy="105" r="3" fill="#E024A5"/>
                        <circle cx="138" cy="82" r="2.5" fill="#00E5FF"/>
                        <circle cx="62" cy="82" r="2.5" fill="#00FF9D"/>
                        <!-- Synaptic Connections -->
                        <line x1="100" y1="85" x2="78" y2="65" stroke="#00E5FF" stroke-width="1" opacity="0.7"/>
                        <line x1="100" y1="85" x2="122" y2="65" stroke="#E024A5" stroke-width="1" opacity="0.7"/>
                        <line x1="100" y1="85" x2="85" y2="110" stroke="#7C3AED" stroke-width="1" opacity="0.7"/>
                        <line x1="100" y1="85" x2="118" y2="105" stroke="#00E5FF" stroke-width="1" opacity="0.7"/>
                        <line x1="78" y1="65" x2="62" y2="82" stroke="#00FF9D" stroke-width="0.8" opacity="0.5"/>
                        <line x1="122" y1="65" x2="138" y2="82" stroke="#E024A5" stroke-width="0.8" opacity="0.5"/>
                    </svg>
                </div>

                <!-- Telemetry Meta Block -->
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; text-align:right; display:flex; flex-direction:column; gap:8px;">
                    <div><span style="color:#64748B;">AI STATUS</span><br><span style="color:#10B981; font-weight:700;">ACTIVE</span></div>
                    <div><span style="color:#64748B;">MODEL</span><br><span style="color:#FFF; font-weight:700;">V6.4.1</span></div>
                    <div><span style="color:#64748B;">LATENCY</span><br><span style="color:#FFF; font-weight:700;">14ms</span></div>
                    <div><span style="color:#64748B;">THROUGHPUT</span><br><span style="color:#00E5FF; font-weight:700;">2.4M/s</span></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with hero_right:
    st.markdown("""
        <div class="hud-panel" style="min-height: 290px;">
            <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#00E5FF; letter-spacing:0.1em; margin-bottom:12px;">
                ● LIVE INTELLIGENCE FEED
            </div>
            <div class="feed-row">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#00E5FF; font-size:0.9rem;">🛰️</span>
                    <span style="font-size:0.82rem; color:#E2E8F0;">Satellite signal intercepted</span>
                </div>
                <span style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#64748B;">2 min ago</span>
            </div>
            <div class="feed-row">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#F59E0B; font-size:0.9rem;">📂</span>
                    <span style="font-size:0.82rem; color:#E2E8F0;">New data source validated</span>
                </div>
                <span style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#64748B;">6 min ago</span>
            </div>
            <div class="feed-row">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#EF4444; font-size:0.9rem;">⚠️</span>
                    <span style="font-size:0.82rem; color:#E2E8F0;">Anomalous traffic detected</span>
                </div>
                <span style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#64748B;">12 min ago</span>
            </div>
            <div class="feed-row">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#10B981; font-size:0.9rem;">🔄</span>
                    <span style="font-size:0.82rem; color:#E2E8F0;">Model refinement complete</span>
                </div>
                <span style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#64748B;">18 min ago</span>
            </div>
            <div class="feed-row">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#E024A5; font-size:0.9rem;">🛡️</span>
                    <span style="font-size:0.82rem; color:#E2E8F0;">Threat pattern updated</span>
                </div>
                <span style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#64748B;">23 min ago</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# ROW 2: 4 QUAD STAT METRICS (MATCHING DESIGN 1)
# --------------------------------------------------
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

metrics_deck = [
    ("TOTAL INTERCEPTS", f"{total_rows:,}", "↑ 14%", "#10B981"),
    ("DATA SOURCES", f"{data_sources:,}", "↑ 8%", "#10B981"),
    ("THREATS DETECTED", f"{threats_detected}", "↓ 32%", "#EF4444"),
    ("OPS ACTIVE", f"{ops_active}", "↑ 0%", "#64748B"),
]

for col, (label, val, delta, dcol) in zip([m1, m2, m3, m4], metrics_deck):
    with col:
        st.markdown(f"""
            <div class="stat-pod">
                <div class="stat-title">{label}</div>
                <div style="display:flex; align-items:flex-end; justify-content:space-between;">
                    <div class="stat-num">{val}</div>
                    <div style="font-family:'JetBrains Mono'; font-size:0.75rem; font-weight:700; color:{dcol}; margin-bottom:4px;">{delta}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)


# --------------------------------------------------
# ROW 3: GLOBAL SIGNAL MAP | INTENSITY | THREATS
# --------------------------------------------------
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
bot1, bot2, bot3 = st.columns([1.4, 1.2, 1], gap="medium")

# Column 1: Global Signal Map
with bot1:
    st.markdown("""
        <div class="hud-panel" style="min-height: 240px;">
            <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; letter-spacing:0.1em; margin-bottom:8px;">
                GLOBAL SIGNAL MAP
            </div>
            <!-- Futuristic SVG World Map with Signal Points -->
            <div style="position:relative; width:100%; height:140px; display:flex; justify-content:center; align-items:center;">
                <svg viewBox="0 0 500 240" style="width:100%; height:100%; opacity:0.85;">
                    <path d="M 50,60 Q 90,40 130,55 Q 160,80 150,110 Q 130,130 90,120 Q 50,100 50,60 Z" fill="#0A162C" stroke="#00E5FF" stroke-width="0.8"/>
                    <path d="M 120,130 Q 160,140 150,190 Q 130,220 110,210 Q 90,170 120,130 Z" fill="#0A162C" stroke="#00E5FF" stroke-width="0.8"/>
                    <path d="M 230,50 Q 280,45 300,75 Q 290,120 250,110 Q 220,90 230,50 Z" fill="#0A162C" stroke="#00E5FF" stroke-width="0.8"/>
                    <path d="M 240,115 Q 285,120 280,170 Q 260,205 235,170 Q 230,135 240,115 Z" fill="#0A162C" stroke="#00E5FF" stroke-width="0.8"/>
                    <path d="M 310,40 Q 420,30 450,70 Q 440,120 370,110 Q 320,80 310,40 Z" fill="#0A162C" stroke="#00E5FF" stroke-width="0.8"/>
                    <path d="M 390,150 Q 440,145 435,185 Q 400,205 385,180 Z" fill="#0A162C" stroke="#00E5FF" stroke-width="0.8"/>
                    <!-- Pulse Nodes -->
                    <circle cx="105" cy="75" r="4" fill="#00E5FF" filter="drop-shadow(0 0 6px #00E5FF)"/>
                    <circle cx="260" cy="70" r="4" fill="#00FF9D" filter="drop-shadow(0 0 6px #00FF9D)"/>
                    <circle cx="390" cy="65" r="4" fill="#EF4444" filter="drop-shadow(0 0 6px #EF4444)"/>
                    <circle cx="130" cy="170" r="4" fill="#E024A5" filter="drop-shadow(0 0 6px #E024A5)"/>
                    <circle cx="410" cy="175" r="4" fill="#00E5FF" filter="drop-shadow(0 0 6px #00E5FF)"/>
                </svg>
            </div>
            <!-- Legend -->
            <div style="display:flex; justify-content:space-around; font-family:'JetBrains Mono'; font-size:0.65rem; color:#64748B; margin-top:8px;">
                <span><b style="color:#00E5FF;">●</b> Active</span>
                <span><b style="color:#E024A5;">●</b> Intercept</span>
                <span><b style="color:#EF4444;">●</b> Threat</span>
                <span><b style="color:#00FF9D;">●</b> Relay</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Column 2: Signal Intensity Curves
with bot2:
    st.markdown("""
        <div class="hud-panel" style="min-height: 240px;">
            <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; letter-spacing:0.1em; margin-bottom:8px;">
                SIGNAL INTENSITY
            </div>
            <!-- Glowing Neon Waveform Visualizer -->
            <div style="width:100%; height:140px; display:flex; align-items:center; justify-content:center;">
                <svg viewBox="0 0 350 140" style="width:100%; height:100%;">
                    <!-- Wave 1 Cyan -->
                    <path d="M 0,80 Q 40,20 90,75 T 180,65 T 270,70 T 350,55" fill="none" stroke="#00E5FF" stroke-width="2.5" style="filter: drop-shadow(0 0 8px rgba(0,229,255,0.7));" />
                    <!-- Wave 2 Magenta -->
                    <path d="M 0,95 Q 50,135 100,85 T 190,105 T 280,60 T 350,90" fill="none" stroke="#E024A5" stroke-width="2" style="filter: drop-shadow(0 0 8px rgba(224,36,165,0.7));" opacity="0.8" />
                    <!-- Grid Reference Line -->
                    <line x1="0" y1="70" x2="350" y2="70" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3,3"/>
                </svg>
            </div>
            <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono'; font-size:0.65rem; color:#64748B; margin-top:8px;">
                <span>SPECTRUM: 2.4 - 5.8 GHz</span>
                <span style="color:#00E5FF;">PEAK AMPLITUDE: 94.2 dB</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Column 3: Threat Distribution Donut
with bot3:
    st.markdown("""
        <div class="hud-panel" style="min-height: 240px;">
            <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; letter-spacing:0.1em; margin-bottom:8px;">
                THREAT DISTRIBUTION
            </div>
            <div style="display:flex; align-items:center; justify-content:space-between; margin-top:4px;">
                <!-- Glowing Threat Ring -->
                <div style="position:relative; width:125px; height:125px;">
                    <svg viewBox="0 0 36 36" style="width:100%; height:100%; transform: rotate(-90deg); filter: drop-shadow(0 0 8px rgba(0,229,255,0.3));">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#0B1528" stroke-width="3.5" />
                        <!-- Cyber 41% (Cyan) -->
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#00E5FF" stroke-width="3.5" stroke-dasharray="41, 100" />
                        <!-- Comms 24% (Purple) -->
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#7C3AED" stroke-width="3.5" stroke-dasharray="24, 100" stroke-dashoffset="-41" />
                        <!-- Physical 18% (Magenta) -->
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#E024A5" stroke-width="3.5" stroke-dasharray="18, 100" stroke-dashoffset="-65" />
                        <!-- Financial 12% (Pink) -->
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#EF4444" stroke-width="3.5" stroke-dasharray="12, 100" stroke-dashoffset="-83" />
                    </svg>
                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                        <div style="font-family:'Orbitron'; font-size:1.4rem; font-weight:800; color:#FFF; line-height:1;">17</div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.55rem; color:#64748B;">THREATS</div>
                    </div>
                </div>

                <!-- Breakdown Percentage List -->
                <div style="font-family:'JetBrains Mono'; font-size:0.68rem; color:#94A3B8; display:flex; flex-direction:column; gap:5px;">
                    <div><span style="color:#00E5FF;">●</span> Cyber <b style="color:#FFF;">41%</b></div>
                    <div><span style="color:#7C3AED;">●</span> Comms <b style="color:#FFF;">24%</b></div>
                    <div><span style="color:#E024A5;">●</span> Physical <b style="color:#FFF;">18%</b></div>
                    <div><span style="color:#EF4444;">●</span> Financial <b style="color:#FFF;">12%</b></div>
                    <div><span style="color:#64748B;">●</span> Other <b style="color:#FFF;">5%</b></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# ACTION CONTROL: LAUNCH RESEARCH AUTOMATION
# --------------------------------------------------
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
with st.expander("⚡ ENGAGE RESEARCH TRIAGE & BATCH NEURAL HARVEST", expanded=False):
    triage_left, triage_right = st.columns([2, 1])
    with triage_left:
        st.markdown("<b style='color:#00E5FF; font-family:JetBrains Mono;'>Ingested Google Sheets Records</b>", unsafe_allow_html=True)
        st.dataframe(discovery_df.head(10), use_container_width=True, hide_index=True)
    with triage_right:
        st.markdown("<b style='color:#00E5FF; font-family:JetBrains Mono;'>Execute Groq Neural Synthesis</b>", unsafe_allow_html=True)
        if st.button("RUN NEURAL SYNTHESIS (ROW 2)", use_container_width=True):
            if not discovery_df.empty:
                with st.spinner("Decoding signal through Groq LLM..."):
                    record = discovery_df.iloc[0].to_dict()
                    res = analyze_with_groq(record)
                    st.success("Target Analysis Complete!")
                    st.json(res)
