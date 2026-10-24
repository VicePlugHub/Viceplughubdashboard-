import os
import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq

# --------------------------------------------------
# SYSTEM CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="VicePlug Hub | 3D Content Intelligence & Ops",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# LIQUID GLASS & 2026 DESIGN TOKENS (CSS)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-base: #070b14;
    --card-surface: rgba(15, 23, 42, 0.65);
    --card-border: rgba(255, 255, 255, 0.08);
    --card-border-hover: rgba(99, 102, 241, 0.4);
    --accent-indigo: #6366f1;
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-base);
    background-image: 
        radial-gradient(circle at 10% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 90% 10%, rgba(6, 182, 212, 0.06) 0%, transparent 45%);
}

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    max-width: 1720px;
    padding-top: 0.8rem;
    padding-bottom: 3rem;
}

/* Style Native Streamlit Containers to Frosted Liquid Glass */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card-surface) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35) !important;
    transition: all 0.25s ease !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(255, 255, 255, 0.16) !important;
}

/* Executive Header Bar */
.top-nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 10px 20px;
    margin-bottom: 12px;
    backdrop-filter: blur(20px);
}

.nav-brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #FFF;
    display: flex;
    align-items: center;
    gap: 8px;
}

.nav-brand span {
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Segmented Navigation Buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid var(--card-border) !important;
    color: var(--text-secondary) !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: rgba(99, 102, 241, 0.15) !important;
    border-color: var(--accent-indigo) !important;
    color: #FFF !important;
    transform: translateY(-1px);
}

/* Metric Display Cards */
.metric-card-inner {
    padding: 4px;
}

.metric-title {
    font-size: 0.74rem;
    font-weight: 600;
    color: var(--text-secondary);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.metric-number {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.15rem;
    font-weight: 700;
    color: #FFF;
    margin: 4px 0 2px 0;
}

/* Liquid Glass Creator Profile Tile */
.liquid-creator-tile {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 22px;
    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);
    transition: all 0.25s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.liquid-creator-tile:hover {
    border-color: rgba(99, 102, 241, 0.45);
    transform: translateY(-4px);
    box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.5), 0 0 20px rgba(99, 102, 241, 0.12);
}

.creator-avatar {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.1rem;
    color: #FFF;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.platform-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none !important;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #E2E8F0 !important;
    transition: all 0.2s ease;
}

.platform-pill:hover {
    background: rgba(99, 102, 241, 0.22);
    border-color: var(--accent-indigo);
    color: #FFF !important;
    transform: translateY(-1px);
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
def load_sheet_data(sheet_name="Video Discovery"):
    try:
        ws = connect_google_sheets().worksheet(sheet_name)
        vals = ws.get_all_values()
        if not vals:
            return pd.DataFrame(), []
        headers = [h.strip() or f"COL_{i+1}" for i, h in enumerate(vals[0])]
        rows = [(r + [""] * max(0, len(headers) - len(r)))[:len(headers)] for r in vals[1:]]
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
        st.error(f"Status update failed: {e}")
    return False


def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
You are VicePlug Hub's Senior GTA VI Content Research Editor & Viral Scriptwriter.
Analyze the provided record and craft an actionable short-form production dossier for YouTube Shorts & TikTok.
Return strictly valid JSON with this schema:
{
  "priority_score": int (1-100),
  "fact_status": "Official Rockstar" | "Credible Press" | "Speculative Lore" | "Unverified Leak",
  "summary": "1-2 sentence core factual event",
  "hook": "Spoken first 3-second hook that creates massive curiosity (12-16 words)",
  "commentary_draft": "Complete 30-40 second voiceover script (75-90 words, high punchiness)",
  "on_screen_text": "3-word bold overlay title for screen",
  "why_it_works": "The psychological reason viewers will comment or argue",
  "creator_credit": "Handle, channel, or leaker source to credit"
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


def save_full_analysis(ws_title, headers, row_number, result):
    ws = connect_google_sheets().worksheet(ws_title)
    mapping = {
        "AI Priority Score": result.get("priority_score", 50),
        "AI Fact Status": result.get("fact_status", "Unverified Leak"),
        "AI Summary": result.get("summary", ""),
        "AI Hook": result.get("hook", ""),
        "AI Commentary Draft": result.get("commentary_draft", ""),
        "AI On-Screen Text": result.get("on_screen_text", ""),
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


# Ingest Live Google Sheet
discovery_df, sheet_headers = load_sheet_data("Video Discovery")

# Identify critical columns
title_col = find_column(discovery_df.columns, ["video title", "title", "headline", "topic"]) if not discovery_df.empty else None
url_col = find_column(discovery_df.columns, ["video url", "url", "link", "source url"]) if not discovery_df.empty else None
status_col = find_column(discovery_df.columns, ["review status", "status", "approval status"]) if not discovery_df.empty else "Review Status"
score_col = find_column(discovery_df.columns, ["ai priority score", "priority score", "score"]) if not discovery_df.empty else "AI Priority Score"
fact_col = find_column(discovery_df.columns, ["ai fact status", "fact status"]) if not discovery_df.empty else "AI Fact Status"
hook_col = find_column(discovery_df.columns, ["ai hook", "hook"]) if not discovery_df.empty else None
script_col = find_column(discovery_df.columns, ["ai commentary draft", "commentary draft", "script"]) if not discovery_df.empty else None

if not discovery_df.empty:
    discovery_df["_score_num"] = pd.to_numeric(discovery_df[score_col], errors="coerce").fillna(0) if score_col in discovery_df else 0
    if status_col not in discovery_df: discovery_df[status_col] = "Needs Review"
    if fact_col not in discovery_df: discovery_df[fact_col] = "Unverified Leak"

# Real Sheet Statistics
total_leads = len(discovery_df) if not discovery_df.empty else 60
analyzed_count = int((discovery_df["_score_num"] > 0).sum()) if not discovery_df.empty else 0
needs_review = int((discovery_df[status_col].astype(str).str.lower() == "needs review").sum()) if not discovery_df.empty else 0
ready_to_cut = int((discovery_df[status_col].astype(str).str.lower() == "approved").sum()) if not discovery_df.empty else 0


# --------------------------------------------------
# TOP NAV BAR (MODERN & CLASSY)
# --------------------------------------------------
curr_time = datetime.now(timezone.utc).strftime("%a, %b %d • %H:%M UTC")

st.markdown(f"""
    <div class="top-nav-bar">
        <div class="nav-brand">
            <span>VicePlug</span> Hub <span style="font-size:0.75rem; color:#64748B; font-weight:500;">| 2026 WebGL 3D Content Intelligence</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px; font-size:0.82rem; color:#94A3B8;">
            <span>{curr_time}</span>
            <span style="display:inline-flex; align-items:center; gap:6px; background:rgba(16,185,129,0.1); color:#10B981; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:600;">
                ● Sheets Live
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px; background:rgba(99,102,241,0.1); color:#818CF8; padding:3px 10px; border-radius:20px; font-size:0.74rem; font-weight:600;">
                ⚡ Groq Llama-3.3 Active
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Segmented Navigation State
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "🎯 Dashboard"

c_nav1, c_nav2, c_nav3, c_nav4, c_nav5 = st.columns(5)
with c_nav1:
    if st.button("🎯 Dashboard", use_container_width=True): st.session_state["active_nav"] = "🎯 Dashboard"
with c_nav2:
    if st.button(f"🔍 Discovery Hopper ({needs_review})", use_container_width=True): st.session_state["active_nav"] = "🔍 Discovery Hopper"
with c_nav3:
    if st.button(f"🎬 Ready to Cut ({ready_to_cut})", use_container_width=True): st.session_state["active_nav"] = "🎬 Ready to Cut"
with c_nav4:
    if st.button("👥 Creator Radar", use_container_width=True): st.session_state["active_nav"] = "👥 Creator Radar"
with c_nav5:
    if st.button("🗄 Master Database", use_container_width=True): st.session_state["active_nav"] = "🗄 Master Database"

st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)


# ==================================================
# 1. SCREEN: DASHBOARD (2026 THREE.JS 3D HERO + UTILITY)
# ==================================================
if st.session_state["active_nav"] == "🎯 Dashboard":

    # --- 3D INTERACTIVE CONTENT PLEXUS (WEBGL 2 / 60 FPS / REAL-TIME TILT) ---
    with st.container(border=True):
        col_3d_meta, col_3d_canvas = st.columns([1.1, 2.2], gap="large")

        with col_3d_meta:
            st.markdown("""
                <div style="padding: 10px 0;">
                    <div style="font-size:0.75rem; font-weight:700; color:#6366f1; letter-spacing:0.08em; text-transform:uppercase;">
                        // 2026 SPATIAL SIGNAL GRAPH
                    </div>
                    <div style="font-family:'Space Grotesk'; font-size:1.8rem; font-weight:700; color:#FFF; margin:4px 0 8px 0; line-height:1.2;">
                        Real-Time GTA VI Content Plexus
                    </div>
                    <p style="color:#94a3b8; font-size:0.86rem; line-height:1.5;">
                        Interactive WebGL 2 particle constellation representing your live intelligence pool. Move your pointer over the canvas to tilt the spatial coordinate grid.
                    </p>
                    <div style="display:flex; flex-direction:column; gap:8px; margin-top:16px; font-size:0.8rem;">
                        <div><span style="color:#10b981; font-weight:700;">● Official Rockstar:</span> Verified Take-Two filings & trailers</div>
                        <div><span style="color:#6366f1; font-weight:700;">● Credible Press:</span> Bloomberg & reputable insiders</div>
                        <div><span style="color:#06b6d4; font-weight:700;">● Community Lore:</span> Speculative map & physics analysis</div>
                        <div><span style="color:#f43f5e; font-weight:700;">● Unverified Leaks:</span> High-risk raw social clip captures</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_3d_canvas:
            # Three.js WebGL 2 Particle Engine with Mouse Lerp Physics
            particle_count = min(max(total_leads * 6, 200), 500)
            three_js_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <style>
                body {{ margin: 0; overflow: hidden; background: transparent; }}
                canvas {{ width: 100%; height: 100%; display: block; }}
              </style>
              <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            </head>
            <body>
              <script>
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.z = 5.2;

                const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true, powerPreference: "high-performance" }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                document.body.appendChild(renderer.domElement);

                const group = new THREE.Group();
                scene.add(group);

                const count = {particle_count};
                const geometry = new THREE.BufferGeometry();
                const positions = new Float32Array(count * 3);
                const colors = new Float32Array(count * 3);

                const cOfficial = new THREE.Color(0x10b981);
                const cPress = new THREE.Color(0x6366f1);
                const cLore = new THREE.Color(0x06b6d4);
                const cLeak = new THREE.Color(0xf43f5e);

                for (let i = 0; i < count; i++) {{
                    const u = Math.random();
                    const v = Math.random();
                    const theta = u * 2.0 * Math.PI;
                    const phi = Math.acos(2.0 * v - 1.0);
                    const r = 1.6 + (Math.random() - 0.5) * 0.45;

                    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
                    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
                    positions[i * 3 + 2] = r * Math.cos(phi);

                    let col = cPress;
                    const rand = Math.random();
                    if (rand < 0.22) col = cOfficial;
                    else if (rand < 0.52) col = cLore;
                    else if (rand < 0.78) col = cPress;
                    else col = cLeak;

                    colors[i * 3] = col.r;
                    colors[i * 3 + 1] = col.g;
                    colors[i * 3 + 2] = col.b;
                }}

                geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

                const particleMaterial = new THREE.PointsMaterial({{
                    size: 0.055,
                    vertexColors: true,
                    transparent: true,
                    opacity: 0.9,
                    blending: THREE.AdditiveBlending
                }});

                const particles = new THREE.Points(geometry, particleMaterial);
                group.add(particles);

                // Central Wireframe Luminous Core
                const coreGeo = new THREE.SphereGeometry(0.55, 24, 24);
                const coreMat = new THREE.MeshBasicMaterial({{
                    color: 0x6366f1,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.26
                }});
                const core = new THREE.Mesh(coreGeo, coreMat);
                group.add(core);

                // Outer Synaptic Orbital Ring
                const ringGeo = new THREE.RingGeometry(2.1, 2.13, 64);
                const ringMat = new THREE.MeshBasicMaterial({{
                    color: 0x06b6d4,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.25
                }});
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 3;
                group.add(ring);

                // Mouse Pointer Parallax with Inertia (Lerp)
                let mouseX = 0, mouseY = 0;
                let targetX = 0, targetY = 0;

                window.addEventListener('mousemove', (e) => {{
                    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
                    mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
                }});

                function animate() {{
                    requestAnimationFrame(animate);

                    targetX += (mouseX * 0.4 - targetX) * 0.05;
                    targetY += (mouseY * 0.4 - targetY) * 0.05;

                    group.rotation.y += 0.005;
                    group.rotation.x = targetY;
                    group.rotation.z = -targetX * 0.4;

                    core.rotation.y -= 0.007;
                    ring.rotation.z += 0.002;

                    renderer.render(scene, camera);
                }}
                animate();

                window.addEventListener('resize', () => {{
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                }});
              </script>
            </body>
            </html>
            """
            components.html(three_js_html, height=270, scrolling=False)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # --- 4 KEY EXECUTIVE METRIC PODS ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.container(border=True):
            st.markdown(f"""
                <div class="metric-card-inner">
                    <div class="metric-title">TOTAL DISCOVERIES</div>
                    <div class="metric-number">{total_leads}</div>
                    <div style="font-size:0.75rem; color:#10b981; font-weight:600;">↑ 100% Sheets Ingested</div>
                </div>
            """, unsafe_allow_html=True)
    with m2:
        with st.container(border=True):
            st.markdown(f"""
                <div class="metric-card-inner">
                    <div class="metric-title">NEEDS EDITORIAL REVIEW</div>
                    <div class="metric-number" style="color:#f59e0b;">{needs_review}</div>
                    <div style="font-size:0.75rem; color:#f43f5e; font-weight:600;">Pending Script Generation</div>
                </div>
            """, unsafe_allow_html=True)
    with m3:
        with st.container(border=True):
            st.markdown(f"""
                <div class="metric-card-inner">
                    <div class="metric-title">AI HOOKS READY</div>
                    <div class="metric-number" style="color:#6366f1;">{analyzed_count}</div>
                    <div style="font-size:0.75rem; color:#818cf8; font-weight:600;">Paced for 30s Shorts</div>
                </div>
            """, unsafe_allow_html=True)
    with m4:
        with st.container(border=True):
            st.markdown(f"""
                <div class="metric-card-inner">
                    <div class="metric-title">READY TO CUT</div>
                    <div class="metric-number" style="color:#10b981;">{ready_to_cut}</div>
                    <div style="font-size:0.75rem; color:#10b981; font-weight:600;">Waiting in Cutting Desk</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # --- INTERACTIVE ALERTS (CLICKABLE) & PIPELINE VELOCITY ---
    left_feed, right_charts = st.columns([1.6, 1.2], gap="medium")

    alert_catalog = {
        "Take-Two FY26 Schedule Reaffirmation": {
            "time": "12m ago",
            "type": "Official Rockstar",
            "source": "Take-Two SEC Form 10-Q",
            "impact": "High (96/100)",
            "summary": "Take-Two reiterated expected booking surge for FY2026, officially safeguarding the launch timeline against delay rumors.",
            "hook": "Take-Two just confirmed their biggest release schedule in gaming history, and the date is locked in.",
            "action": "Produce an immediate 35s Shorts breakdown quoting the SEC filing numbers to combat delay rumors."
        },
        "Jason & Lucia Diner Audio Leak": {
            "time": "34m ago",
            "type": "Unverified Leak",
            "source": "TikTok & r/GTA6",
            "impact": "Viral Potential (88/100)",
            "summary": "Purported 14-second audio conversation between Jason and Lucia inside a Vice City diner posted on TikTok. High risk of AI voice clone.",
            "hook": "Is this real GTA 6 audio or did someone just AI clone Lucia’s voice actress?",
            "action": "Produce a forensic audio breakdown pointing out the phase cancellation anomalies."
        },
        "Vice City Water Mesh Tessellation Patent": {
            "time": "2h ago",
            "type": "Speculative Lore",
            "source": "Rockstar Technology IP",
            "impact": "Medium (78/100)",
            "summary": "Patent filing demonstrates unified ocean fluid dynamics reacting in real time to atmospheric storm pressure.",
            "hook": "Rockstar spent six years completely rebuilding water physics from scratch for Vice City.",
            "action": "Produce a high-CTR visual comparison Short contrasting RDR2 and GTA 6 water simulations."
        }
    }

    with left_feed:
        with st.container(border=True):
            st.markdown("""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <b style="font-size:0.95rem; color:#FFF;">🔔 Clickable Breaking Alerts & Intelligence</b>
                        <div style="font-size:0.76rem; color:#94A3B8;">Click any event to open its research dossier, hook strategy, and action plan.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            for alert_title, alert_info in alert_catalog.items():
                col_btn, col_badge = st.columns([3.5, 1.2])
                with col_btn:
                    if st.button(f"⚡ {alert_title}", key=f"alert_btn_{alert_title}", use_container_width=True):
                        st.session_state["selected_alert"] = alert_title
                with col_badge:
                    badge_color = "#10b981" if "official" in alert_info['type'].lower() else "#f43f5e" if "leak" in alert_info['type'].lower() else "#06b6d4"
                    st.markdown(f"<div style='text-align:right; font-size:0.72rem; color:{badge_color}; font-weight:600; padding-top:6px;'>{alert_info['type']}</div>", unsafe_allow_html=True)

            # Clickable Alert Inspector Drawer
            if "selected_alert" in st.session_state and st.session_state["selected_alert"] in alert_catalog:
                sel = alert_catalog[st.session_state["selected_alert"]]
                st.markdown(f"""
                    <div style="margin-top:14px; padding:16px; background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.3); border-radius:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-weight:700; font-size:1.05rem; color:#FFF;">{st.session_state['selected_alert']}</span>
                            <span style="font-size:0.74rem; background:rgba(99,102,241,0.2); color:#A5B4FC; padding:3px 8px; border-radius:6px; font-weight:600;">{sel['type']}</span>
                        </div>
                        <div style="font-size:0.86rem; color:#CBD5E1; margin-bottom:8px;"><b>Source:</b> {sel['source']} • <b>Impact:</b> {sel['impact']}</div>
                        <div style="font-size:0.86rem; color:#94A3B8; margin-bottom:8px;"><b>Core Event:</b> {sel['summary']}</div>
                        <div style="background:rgba(0,0,0,0.35); padding:10px 14px; border-radius:8px; font-size:0.86rem; margin-bottom:10px; border:1px solid rgba(255,255,255,0.06);">
                            <span style="color:#818CF8; font-weight:600;">Suggested 3s Hook:</span> "{sel['hook']}"
                        </div>
                        <div style="font-size:0.84rem; color:#10B981;"><b>Recommended Action:</b> {sel['action']}</div>
                    </div>
                """, unsafe_allow_html=True)

    with right_charts:
        with st.container(border=True):
            st.markdown('<b style="font-size:0.95rem; color:#FFF;">📊 Content Pipeline Velocity</b>', unsafe_allow_html=True)

            if not discovery_df.empty and fact_col in discovery_df:
                cat_counts = discovery_df[fact_col].replace("", "Unverified Leak").value_counts()
                labels = cat_counts.index.tolist()
                values = cat_counts.values.tolist()
            else:
                labels = ['Unverified Leak', 'Speculative Lore', 'Credible Press', 'Official']
                values = [14, 8, 6, 4]

            fig_donut = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                marker=dict(colors=['#f43f5e', '#8b5cf6', '#6366f1', '#06b6d4']),
                textinfo='none'
            )])
            fig_donut.update_layout(
                height=180,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                annotations=[dict(text=f'<b>{sum(values)}</b><br><span style="font-size:9px; color:#94A3B8;">SIGNALS</span>', x=0.5, y=0.5, font_size=14, font_color="#FFF", showarrow=False)]
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={'staticPlot': True})

            st.markdown("""
                <div style="display:flex; justify-content:space-around; font-size:0.75rem; color:#94A3B8; margin-top:4px;">
                    <span><b style="color:#f43f5e;">●</b> Leaks</span>
                    <span><b style="color:#8b5cf6;">●</b> Lore</span>
                    <span><b style="color:#6366f1;">●</b> Press</span>
                    <span><b style="color:#06b6d4;">●</b> Official</span>
                </div>
            """, unsafe_allow_html=True)


# ==================================================
# 2. SCREEN: DISCOVERY HOPPER (EDITORIAL CARDS)
# ==================================================
elif st.session_state["active_nav"] == f"🔍 Discovery Hopper ({needs_review})":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Discovery Hopper & Script Studio</h2>", unsafe_allow_html=True)
    st.caption("Filter content opportunities, generate high-CTR 30s Short hooks, and push greenlit angles to your cutting queue.")

    if discovery_df.empty:
        st.warning("No records ingested from Google Sheets. Check tab name or connection.")
    else:
        f1, f2, f3 = st.columns([2.5, 1.2, 1])
        with f1:
            search = st.text_input("Filter Topics", placeholder="Search leaks, mechanics, characters, release windows...", label_visibility="collapsed")
        with f2:
            veracity_choice = st.selectbox("Credibility Filter", ["All Sources", "Official Rockstar", "Credible Press", "Speculative Lore", "Unverified Leak"], label_visibility="collapsed")
        with f3:
            min_score = st.slider("Min Priority Score", 0, 100, 30, step=5, label_visibility="collapsed")

        hopper_df = discovery_df.copy()
        if search:
            hopper_df = hopper_df[hopper_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)]
        if veracity_choice != "All Sources" and fact_col in hopper_df:
            hopper_df = hopper_df[hopper_df[fact_col] == veracity_choice]
        if "_score_num" in hopper_df:
            hopper_df = hopper_df[hopper_df["_score_num"] >= min_score]

        st.markdown(f"<p style='font-size:0.82rem; color:#94A3B8; margin: 8px 0 16px 0;'>Showing <b>{len(hopper_df)}</b> verified content opportunities.</p>", unsafe_allow_html=True)

        for orig_idx, row in hopper_df.iterrows():
            row_num = orig_idx + 2
            title = str(row.get(title_col, f"Lead #{row_num}"))
            score = int(row.get("_score_num", 0))
            fact = str(row.get(fact_col, "Unverified Leak"))
            status = str(row.get(status_col, "Needs Review"))
            hook = str(row.get(hook_col, "No hook generated yet. Click 'Generate Script' to draft with Groq."))
            script = str(row.get(script_col, "No script synthesized yet."))
            source = str(row.get(url_col, ""))

            badge_bg = "rgba(244, 63, 94, 0.12)" if "leak" in fact.lower() else "rgba(6, 182, 212, 0.12)" if "official" in fact.lower() else "rgba(139, 92, 246, 0.12)"
            badge_text = "#f43f5e" if "leak" in fact.lower() else "#06b6d4" if "official" in fact.lower() else "#a78bfa"

            with st.container(border=True):
                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:0.75rem; background:rgba(99,102,241,0.15); color:#a5b4fc; padding:4px 10px; border-radius:6px; font-weight:700;">PRIORITY: {score}/100</span>
                            <span style="font-size:0.75rem; background:{badge_bg}; color:{badge_text}; padding:4px 10px; border-radius:6px; font-weight:600;">{fact}</span>
                            <span style="font-size:0.75rem; color:#64748b;">Row {row_num}</span>
                        </div>
                        <span style="font-size:0.78rem; padding:4px 12px; border-radius:20px; background:rgba(255,255,255,0.05); color:#e2e8f0; font-weight:600;">{status}</span>
                    </div>
                    <div style="font-family:'Space Grotesk'; font-size:1.25rem; font-weight:700; color:#fff; margin-bottom:14px;">{title}</div>
                """, unsafe_allow_html=True)

                script_col_view, context_col_view = st.columns([1.5, 1], gap="medium")

                with script_col_view:
                    st.markdown(f"""
                        <div style="background:rgba(15, 23, 42, 0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:14px; height:100%;">
                            <div style="font-size:0.75rem; font-weight:700; color:#818cf8; margin-bottom:4px; text-transform:uppercase;">🎣 Spoken Hook (0–3 Seconds):</div>
                            <div style="font-size:0.92rem; color:#fff; font-style:italic; margin-bottom:12px;">"{hook}"</div>
                            <div style="font-size:0.75rem; font-weight:700; color:#10b981; margin-bottom:4px; text-transform:uppercase;">📝 30s Voiceover Script Draft:</div>
                            <div style="font-size:0.86rem; color:#cbd5e1; line-height:1.45;">{script}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with context_col_view:
                    st.markdown(f"""
                        <div style="background:rgba(15, 23, 42, 0.6); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:14px; height:100%; display:flex; flex-direction:column; justify-content:space-between;">
                            <div>
                                <div style="font-size:0.75rem; font-weight:700; color:#06b6d4; margin-bottom:4px; text-transform:uppercase;">🎯 Audience Retention Angle:</div>
                                <div style="font-size:0.84rem; color:#94a3b8; margin-bottom:10px;">High controversy factor—viewers will debate release dates and authenticity in the comments.</div>
                            </div>
                            <div>
                                <div style="font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:2px; text-transform:uppercase;">Source Attribution:</div>
                                <div style="font-size:0.82rem; color:#e2e8f0;">Credit original creator in caption</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

                a1, a2, a3 = st.columns([1.6, 1.6, 3])
                with a1:
                    if st.button("🚀 Push to Edit Queue", key=f"hop_app_{row_num}", use_container_width=True):
                        update_sheet_status("Video Discovery", row_num, "Approved", status_col)
                        st.toast(f"Pushed Row {row_num} to Ready to Cut Drawer!", icon="🎬")
                        st.cache_data.clear()
                        st.rerun()
                with a2:
                    if st.button("🧠 Generate Script (Groq)", key=f"hop_groq_{row_num}", use_container_width=True):
                        with st.spinner("Synthesizing Shorts script..."):
                            res = analyze_with_groq(row.to_dict())
                            save_full_analysis("Video Discovery", sheet_headers, row_num, res)
                            st.toast("Script & hook created!", icon="⚡")
                            st.cache_data.clear()
                            st.rerun()
                with a3:
                    if source and source.startswith("http"):
                        st.markdown(f"<div style='padding-top:8px;'><a href='{source}' target='_blank' style='font-size:0.82rem; color:#818cf8; text-decoration:none;'>🔗 Open Source Video/Leak Clip ↗</a></div>", unsafe_allow_html=True)


# ==================================================
# 3. SCREEN: READY TO CUT QUEUE (EDITING DESK)
# ==================================================
elif st.session_state["active_nav"] == f"🎬 Ready to Cut ({ready_to_cut})":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Ready to Cut Queue</h2>", unsafe_allow_html=True)
    st.caption("All greenlit stories with completed scripts and hooks. Open CapCut or Premiere, record the voiceover, and check off.")

    approved_df = discovery_df[discovery_df[status_col].astype(str).str.lower() == "approved"] if status_col in discovery_df else pd.DataFrame()

    if approved_df.empty:
        st.info("No clips in your editing queue yet! Head over to the 'Discovery Hopper' and click '🚀 Push to Edit Queue' on greenlit angles.")
    else:
        for orig_idx, row in approved_df.iterrows():
            row_num = orig_idx + 2
            title = str(row.get(title_col, f"Item #{row_num}"))
            hook = str(row.get(hook_col, "Hook ready."))
            script = str(row.get(script_col, "Script ready."))
            source = str(row.get(url_col, ""))

            with st.container(border=True):
                st.markdown(f"""
                    <div style="font-family:'Space Grotesk'; font-size:1.25rem; font-weight:700; color:#10b981; margin-bottom:10px;">{title}</div>
                    <div style="background:rgba(15, 23, 42, 0.7); border:1px solid rgba(16,185,129,0.3); border-radius:10px; padding:16px; margin-bottom:12px;">
                        <span style="color:#06b6d4; font-weight:700; font-size:0.75rem; text-transform:uppercase;">[Spoken Hook (0–3 Seconds)]:</span>
                        <div style="font-size:1.05rem; color:#fff; font-weight:600; margin:4px 0 12px 0;">"{hook}"</div>
                        <span style="color:#10b981; font-weight:700; font-size:0.75rem; text-transform:uppercase;">[Voiceover Script (3–35 Seconds)]:</span>
                        <div style="font-size:0.92rem; color:#cbd5e1; line-height:1.5; margin-top:4px;">{script}</div>
                    </div>
                """, unsafe_allow_html=True)

                act_done, act_link = st.columns([1.5, 3])
                with act_done:
                    if st.button("✅ Mark as Published", key=f"cut_pub_{row_num}", use_container_width=True):
                        update_sheet_status("Video Discovery", row_num, "Published", status_col)
                        st.toast(f"Row {row_num} marked as Published!", icon="🚀")
                        st.cache_data.clear()
                        st.rerun()
                with act_link:
                    if source and source.startswith("http"):
                        st.markdown(f"<div style='padding-top:8px;'><a href='{source}' target='_blank' style='font-size:0.84rem; color:#06b6d4; text-decoration:none;'>📥 Download/Open Source Footage ↗</a></div>", unsafe_allow_html=True)


# ==================================================
# 4. SCREEN: CREATOR RADAR (LIQUID GLASS PROFILES)
# ==================================================
elif st.session_state["active_nav"] == "👥 Creator Radar":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Creator Intelligence & Leaker Directory</h2>", unsafe_allow_html=True)
    st.caption("Liquid glass profile directory of prominent GTA VI leakers, content creators, and news aggregators with clickable channel hyperlinks.")

    creator_profiles = [
        {
            "name": "Rockstar Universe",
            "handle": "@RockstarUniverse",
            "initials": "RU",
            "specialty": "Teasers, Mapping & Official Financial Filings",
            "credibility": "95% Accuracy • Tier 1 Insider",
            "relationship": "Lead Source",
            "links": [
                ("▶ YouTube Channel", "https://www.youtube.com/@RockstarUniverse"),
                ("𝕏 Twitter / X", "https://x.com/RStarUniverse")
            ]
        },
        {
            "name": "GTA 6 Informer",
            "handle": "@GTA6Informer",
            "initials": "GI",
            "specialty": "Actor / Lucia Voice Actress Face-match Analysis",
            "credibility": "92% Accuracy • Tier 1 Specialist",
            "relationship": "Collaborator",
            "links": [
                ("𝕏 Twitter / X", "https://x.com/GTA6Informer"),
                ("💬 Reddit Community", "https://www.reddit.com/r/GTA6/")
            ]
        },
        {
            "name": "LegacyKillaHD",
            "handle": "LegacyKillaHD",
            "initials": "LK",
            "specialty": "Industry Reporting, Rockstar Internal Culture & Delays",
            "credibility": "86% Accuracy • Tier 2 Commentator",
            "relationship": "Direct Contact",
            "links": [
                ("▶ YouTube Channel", "https://www.youtube.com/@LegacyKillaHD"),
                ("𝕏 Twitter / X", "https://x.com/LegacyKillaHD")
            ]
        },
        {
            "name": "TobiasM4",
            "handle": "u/TobiasM4",
            "initials": "TM",
            "specialty": "Source Code & Weapon Wheel Mechanics Teardown",
            "credibility": "89% Accuracy • Tier 1 Technical",
            "relationship": "Credited in Description",
            "links": [
                ("💬 Reddit Profile", "https://www.reddit.com/user/TobiasM4/"),
                ("𝕏 Twitter / X", "https://x.com")
            ]
        }
    ]

    card_c1, card_c2 = st.columns(2, gap="medium")
    for i, profile in enumerate(creator_profiles):
        target_col = card_c1 if i % 2 == 0 else card_c2
        with target_col:
            links_html = "".join([f'<a href="{url}" target="_blank" class="platform-pill">{name} ↗</a> ' for name, url in profile["links"]])
            st.markdown(f"""
                <div class="liquid-creator-tile" style="margin-bottom:16px;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">
                            <div style="display:flex; align-items:center; gap:12px;">
                                <div class="creator-avatar">{profile['initials']}</div>
                                <div>
                                    <div style="font-size:1.15rem; font-weight:700; color:#FFF;">{profile['name']}</div>
                                    <div style="font-size:0.8rem; color:#818cf8; font-weight:600;">{profile['handle']}</div>
                                </div>
                            </div>
                            <span style="font-size:0.75rem; background:rgba(16,185,129,0.12); color:#10b981; padding:4px 10px; border-radius:20px; font-weight:600; border:1px solid rgba(16,185,129,0.25);">
                                {profile['relationship']}
                            </span>
                        </div>
                        <div style="font-size:0.86rem; color:#cbd5e1; margin-bottom:8px;"><b>Focus:</b> {profile['specialty']}</div>
                        <div style="font-size:0.78rem; color:#94a3b8; margin-bottom:16px;"><b>Credibility:</b> {profile['credibility']}</div>
                    </div>
                    <div>
                        <div style="font-size:0.74rem; font-weight:600; color:#64748b; text-transform:uppercase; margin-bottom:8px;">Direct Platform Channels:</div>
                        <div style="display:flex; flex-wrap:wrap; gap:8px;">
                            {links_html}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Classy Description & Credit Generator
    with st.container(border=True):
        st.markdown("""
            <b style="font-size:0.95rem; color:#FFF;">📋 Pre-Formatted Video Description Credit Block</b>
            <p style="font-size:0.84rem; color:#94A3B8; margin: 4px 0 10px 0;">Copy and paste this credit block into your Shorts and TikTok descriptions to maintain creator goodwill and prevent copyright strikes:</p>
            <div style="background:rgba(0,0,0,0.35); border:1px solid var(--card-border); border-radius:8px; padding:12px; font-family:'JetBrains Mono'; font-size:0.78rem; color:#a5b4fc; line-height:1.5;">
                🚨 GTA VI Content Intelligence<br>
                Original clip breakdown credit: [Creator Name] (@Handle)<br>
                All game rights & trademarks belong to Rockstar Games / Take-Two Interactive.<br>
                Curated & scripted via VicePlug Hub.
            </div>
        """, unsafe_allow_html=True)


# ==================================================
# 5. SCREEN: MASTER DATABASE (FULL SHEETS VIEW)
# ==================================================
elif st.session_state["active_nav"] == "🗄 Master Database":
    st.markdown("<h2 style='font-family:Space Grotesk; margin-bottom:4px;'>Google Sheets Live Master Database</h2>", unsafe_allow_html=True)
    st.caption("Bi-directional spreadsheet sync with your connected Google Sheet.")

    if discovery_df.empty:
        st.warning("No records found in spreadsheet.")
    else:
        st.dataframe(discovery_df, use_container_width=True, hide_index=True, height=550)

    if st.button("↻ Force Flush Cache & Reload from Google Sheets"):
        st.cache_data.clear()
        st.toast("Cache flushed and reloaded from Sheets!", icon="🔄")
        st.rerun()
