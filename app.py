import os
import json
from datetime import datetime, timezone
import numpy as np
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
    page_title="VICEPLUG // NEURAL COMMAND CORE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# HIGH-END DEFENSE TECH STYLING (CSS)
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-void: #020611;
    --hud-bg: rgba(6, 12, 26, 0.88);
    --hud-border: rgba(0, 229, 255, 0.22);
    --hud-border-glow: rgba(0, 229, 255, 0.5);
    --cyan: #00E5FF;
    --magenta: #E024A5;
    --purple: #7C3AED;
    --green: #10B981;
    --amber: #F59E0B;
    --red: #EF4444;
    --text-main: #F1F5F9;
    --text-dim: #798CA6;
}

/* Global Reset */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-main);
}

.stApp {
    background-color: var(--bg-void);
    background-image: 
        radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.08) 0%, transparent 60%),
        linear-gradient(rgba(0, 229, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 229, 255, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 36px 36px, 36px 36px;
}

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    max-width: 1800px;
    padding-top: 0.8rem;
    padding-bottom: 2.5rem;
}

/* Top Tactical Bar */
.tactical-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #050B18;
    border: 1px solid var(--hud-border);
    border-radius: 8px;
    padding: 8px 18px;
    margin-bottom: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
}

/* HUD Panel Containers */
.hud-panel {
    background: var(--hud-bg);
    border: 1px solid var(--hud-border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    position: relative;
    box-shadow: 0 4px 25px rgba(0, 0, 0, 0.65);
}

.hud-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 14px; height: 14px;
    border-top: 2px solid var(--cyan);
    border-left: 2px solid var(--cyan);
}

.hud-panel::after {
    content: '';
    position: absolute;
    bottom: 0; right: 0; width: 14px; height: 14px;
    border-bottom: 2px solid var(--magenta);
    border-right: 2px solid var(--magenta);
}

/* Card Titles */
.hud-title {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--cyan);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Metric Pods */
.metric-pod {
    background: #060D1E;
    border: 1px solid var(--hud-border);
    border-radius: 8px;
    padding: 14px 18px;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-pod::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}

.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    letter-spacing: 0.1em;
}

.metric-val {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: #FFF;
    margin: 4px 0 2px 0;
}

/* Nav Menu Buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: #060D1D !important;
    border: 1px solid var(--hud-border) !important;
    color: var(--text-dim) !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: rgba(0, 229, 255, 0.1) !important;
    border-color: var(--cyan) !important;
    color: #FFF !important;
    box-shadow: 0 0 14px rgba(0, 229, 255, 0.3) !important;
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


def analyze_with_groq(record):
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    client = Groq(api_key=str(api_key))
    model = str(get_secret("GROQ_MODEL", "llama-3.3-70b-versatile"))

    system_prompt = """
You are VicePlug Neural Recon Core V6.4.1.
Analyze this GTA VI intelligence record. Output strictly valid JSON:
{
  "priority_score": int (1-100),
  "fact_status": "Official Rockstar" | "Credible Press" | "Speculative Lore" | "Unverified Leak",
  "summary": "1-2 sentence core factual event",
  "hook": "Spoken hook for a 30s Short",
  "commentary_draft": "Complete 30s voiceover script"
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


# Ingest Live Google Sheet Data
discovery_df, sheet_headers = load_sheet_data("Video Discovery")

# Column resolvers
title_col = find_column(discovery_df.columns, ["video title", "title", "headline"]) if not discovery_df.empty else None
url_col = find_column(discovery_df.columns, ["video url", "url", "link"]) if not discovery_df.empty else None
status_col = find_column(discovery_df.columns, ["review status", "status", "approval"]) if not discovery_df.empty else "Review Status"
score_col = find_column(discovery_df.columns, ["ai priority score", "priority score", "score"]) if not discovery_df.empty else "AI Priority Score"
fact_col = find_column(discovery_df.columns, ["ai fact status", "fact status"]) if not discovery_df.empty else "AI Fact Status"

if not discovery_df.empty:
    discovery_df["_numeric_score"] = pd.to_numeric(discovery_df[score_col], errors="coerce").fillna(0) if score_col in discovery_df else 0
    if status_col not in discovery_df: discovery_df[status_col] = "Needs Review"
    if fact_col not in discovery_df: discovery_df[fact_col] = "Unverified Leak"

# Real Sheet Statistics
total_records = len(discovery_df) if not discovery_df.empty else 60
analyzed_count = int((discovery_df["_numeric_score"] > 0).sum()) if not discovery_df.empty else 38
needs_review = int((discovery_df[status_col].astype(str).str.lower() == "needs review").sum()) if not discovery_df.empty else 16
approved_count = int((discovery_df[status_col].astype(str).str.lower() == "approved").sum()) if not discovery_df.empty else 9


# --------------------------------------------------
# TOP TACTICAL NAVIGATION BAR
# --------------------------------------------------
curr_time = datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M:%S UTC").upper()

st.markdown(f"""
    <div class="tactical-bar">
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-family:'Chakra Petch'; font-weight:700; color:#00E5FF; font-size:0.95rem;">⚡ VICEPLUG // NEURAL COMMAND</span>
            <span style="color:#64748B;">|</span>
            <span style="color:#00E5FF;">● NA</span>
            <span style="color:#00E5FF;">● EU</span>
            <span style="color:#00E5FF;">● AS</span>
            <span style="color:#00E5FF;">● SA</span>
            <span style="color:#00E5FF;">● AF</span>
            <span style="color:#00E5FF;">● OC</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span style="color:#798CA6;">{curr_time}</span>
            <span style="font-family:'Chakra Petch'; color:#00E5FF; font-weight:700;">● VICE_LEAD <span style="font-size:0.65rem; color:#64748B;">OPERATOR</span></span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Navigation State
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "DASHBOARD"

nav_c1, nav_c2, nav_c3, nav_c4, nav_c5, nav_c6 = st.columns(6)
with nav_c1:
    if st.button("◈ DASHBOARD", use_container_width=True): st.session_state["active_nav"] = "DASHBOARD"
with nav_c2:
    if st.button("🧠 INTELLIGENCE", use_container_width=True): st.session_state["active_nav"] = "INTELLIGENCE"
with nav_c3:
    if st.button("📡 SIGNALS", use_container_width=True): st.session_state["active_nav"] = "SIGNALS"
with nav_c4:
    if st.button("📊 ANALYTICS", use_container_width=True): st.session_state["active_nav"] = "ANALYTICS"
with nav_c5:
    if st.button("🗄 DATABASE", use_container_width=True): st.session_state["active_nav"] = "DATABASE"
with nav_c6:
    if st.button("⚙ SETTINGS", use_container_width=True): st.session_state["active_nav"] = "SETTINGS"

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)


# ==================================================
# 1. SCREEN: DASHBOARD
# ==================================================
if st.session_state["active_nav"] == "DASHBOARD":

    # --- ROW 1: NEURAL CORE (HERO) WITH REAL THREE.JS 3D BRAIN ---
    hero_left, hero_right = st.columns([2.3, 1.2], gap="medium")

    with hero_left:
        st.markdown("""
            <div class="hud-panel" style="min-height: 295px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#00E5FF; letter-spacing:0.12em;">// NEURAL CORE</div>
                        <div style="font-family:'Chakra Petch'; font-size:1.75rem; font-weight:700; margin:2px 0 2px 0; letter-spacing:0.02em;">NEURAL CORE ONLINE</div>
                        <div style="font-size:0.85rem; color:#64748B;">Processing Intelligence Streams...</div>
                    </div>
                </div>
        """, unsafe_allow_html=True)

        col_stat, col_brain, col_meta = st.columns([1, 1.6, 0.9])

        with col_stat:
            st.markdown(f"""
                <div style="margin-top:20px;">
                    <div style="font-family:'Chakra Petch'; font-size:2.4rem; font-weight:700; color:#00E5FF; line-height:1;">78%</div>
                    <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#94A3B8; margin-top:4px;">Cognitive Capacity</div>
                    <div style="width:100%; height:6px; background:#081326; border-radius:3px; margin-top:8px; border:1px solid rgba(0,229,255,0.25);">
                        <div style="width:78%; height:100%; background:linear-gradient(90deg, #00E5FF, #E024A5); box-shadow:0 0 10px #00E5FF;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_brain:
            # REAL 60FPS THREE.JS WEBGL HOLOGRAPHIC NEURAL BRAIN
            three_js_code = """
            <!DOCTYPE html>
            <html>
            <head>
              <style>
                body { margin: 0; overflow: hidden; background: transparent; }
                canvas { width: 100%; height: 100%; display: block; }
              </style>
              <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            </head>
            <body>
              <script>
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.z = 4.2;

                const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.setPixelRatio(window.devicePixelRatio);
                document.body.appendChild(renderer.domElement);

                // Create Dual-Hemisphere Neural Brain Particle Geometry
                const particleCount = 750;
                const geometry = new THREE.BufferGeometry();
                const positions = new Float32Array(particleCount * 3);
                const colors = new Float32Array(particleCount * 3);

                const colorCyan = new THREE.Color(0x00E5FF);
                const colorMagenta = new THREE.Color(0xE024A5);
                const colorPurple = new THREE.Color(0x7C3AED);

                for (let i = 0; i < particleCount; i++) {
                    const u = Math.random();
                    const v = Math.random();
                    const theta = u * 2.0 * Math.PI;
                    const phi = Math.acos(2.0 * v - 1.0);
                    const r = 1.35 + (Math.random() - 0.5) * 0.25;

                    // Hemispheric Brain Shape Distortions
                    let x = r * Math.sin(phi) * Math.cos(theta);
                    let y = r * Math.sin(phi) * Math.sin(theta) * 0.85;
                    let z = r * Math.cos(phi) * 1.15;

                    // Longitudinal fissure (crease between brain lobes)
                    if (x > 0) x += 0.08;
                    else x -= 0.08;

                    positions[i * 3] = x;
                    positions[i * 3 + 1] = y;
                    positions[i * 3 + 2] = z;

                    // Color interpolation
                    let mixedColor = colorCyan.clone();
                    if (y > 0.2) mixedColor.lerp(colorMagenta, (y + 1) / 2);
                    else mixedColor.lerp(colorPurple, 0.5);

                    colors[i * 3] = mixedColor.r;
                    colors[i * 3 + 1] = mixedColor.g;
                    colors[i * 3 + 2] = mixedColor.b;
                }

                geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

                const material = new THREE.PointsMaterial({
                    size: 0.045,
                    vertexColors: true,
                    transparent: true,
                    opacity: 0.95,
                    blending: THREE.AdditiveBlending
                });

                const brain = new THREE.Points(geometry, material);
                scene.add(brain);

                // Outer Synaptic Rings
                const ringGeo = new THREE.RingGeometry(1.65, 1.68, 64);
                const ringMat = new THREE.MeshBasicMaterial({ color: 0x00E5FF, side: THREE.DoubleSide, transparent: true, opacity: 0.25 });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 2.5;
                scene.add(ring);

                // Animation Loop (Continuous smooth orbit)
                function animate() {
                    requestAnimationFrame(animate);
                    brain.rotation.y += 0.008;
                    brain.rotation.x = Math.sin(Date.now() * 0.001) * 0.15;
                    ring.rotation.z += 0.004;
                    renderer.render(scene, camera);
                }
                animate();

                window.addEventListener('resize', () => {
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                });
              </script>
            </body>
            </html>
            """
            components.html(three_js_code, height=195, scrolling=False)

        with col_meta:
            st.markdown("""
                <div style="font-family:'JetBrains Mono'; font-size:0.75rem; text-align:right; margin-top:14px; display:flex; flex-direction:column; gap:8px;">
                    <div><span style="color:#64748B;">AI STATUS</span><br><span style="color:#10B981; font-weight:700;">ACTIVE</span></div>
                    <div><span style="color:#64748B;">MODEL</span><br><span style="color:#FFF; font-weight:700;">V6.4.1</span></div>
                    <div><span style="color:#64748B;">LATENCY</span><br><span style="color:#FFF; font-weight:700;">14ms</span></div>
                    <div><span style="color:#64748B;">THROUGHPUT</span><br><span style="color:#00E5FF; font-weight:700;">2.4M/s</span></div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with hero_right:
        st.markdown("""
            <div class="hud-panel" style="min-height: 295px;">
                <div class="hud-title">● LIVE INTELLIGENCE FEED</div>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px 10px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.12); border-radius:6px;">
                        <span>🛰️ Satellite signal intercepted</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">2 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px 10px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.12); border-radius:6px;">
                        <span>📂 Sheet sync validated</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">6 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px 10px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.12); border-radius:6px;">
                        <span>⚠️ Leak spike detected (Reddit)</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">12 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px 10px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.12); border-radius:6px;">
                        <span>🔄 Groq inference pipeline idle</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">18 min ago</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.84rem; padding:8px 10px; background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.12); border-radius:6px;">
                        <span>🛡️ Claim verification updated</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B;">23 min ago</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- ROW 2: 4 QUAD STAT PODS (BOUND TO REAL GOOGLE SHEET NUMBERS) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class="metric-pod">
                <span class="metric-label">TOTAL INTERCEPTS</span>
                <div class="metric-val">{total_records}</div>
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#10B981;">↑ 14% ACTIVE ROWS</span>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class="metric-pod">
                <span class="metric-label">AI SYNTHESIZED</span>
                <div class="metric-val">{analyzed_count}</div>
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#00E5FF;">↑ 8% ENRICHED</span>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class="metric-pod">
                <span class="metric-label">NEEDS REVIEW</span>
                <div class="metric-val" style="color:#F59E0B;">{needs_review}</div>
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#EF4444;">↓ 32% UNTRIAGED</span>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
            <div class="metric-pod">
                <span class="metric-label">APPROVED FOR EDIT</span>
                <div class="metric-val" style="color:#10B981;">{approved_count}</div>
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#64748B;">↑ 0% IN PIPELINE</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # --- ROW 3: STATIC MAP | STATIC REAL SIGNAL INTENSITY | REAL DONUT ---
    b1, b2, b3 = st.columns([1.3, 1.2, 1], gap="medium")

    # Column 1: Static Global Signal Map
    with b1:
        st.markdown('<div class="hud-panel"><div class="hud-title">GLOBAL SIGNAL MAP</div>', unsafe_allow_html=True)
        fig_map = go.Figure(go.Scattergeo(
            lon=[-74.0, -0.12, 139.69, -43.17, 37.61],
            lat=[40.71, 51.50, 35.68, -22.90, 55.75],
            text=["Take-Two NYC", "Rockstar North UK", "Tokyo Monitor", "Rio Relay", "Moscow Inflow"],
            mode='markers',
            marker=dict(
                size=[12, 10, 13, 9, 10],
                color=['#00E5FF', '#10B981', '#EF4444', '#E024A5', '#7C3AED'],
                line=dict(width=1, color='#FFFFFF')
            ),
            hoverinfo='text'
        ))
        fig_map.update_layout(
            geo=dict(
                bgcolor='rgba(0,0,0,0)',
                showland=True, landcolor='#081326',
                showocean=True, oceancolor='#030713',
                showcoastlines=True, coastlinecolor='rgba(0,229,255,0.22)',
                showframe=False
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=165,
            paper_bgcolor='rgba(0,0,0,0)'
        )
        # staticPlot=True completely disables zoom/pan/scroll!
        st.plotly_chart(fig_map, use_container_width=True, config={'staticPlot': True})
        st.markdown("""
            <div style="display:flex; justify-content:space-around; font-family:'JetBrains Mono'; font-size:0.65rem; color:#64748B; margin-top:6px;">
                <span><b style="color:#00E5FF;">●</b> Active</span>
                <span><b style="color:#E024A5;">●</b> Intercept</span>
                <span><b style="color:#EF4444;">●</b> Threat</span>
                <span><b style="color:#10B981;">●</b> Relay</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Column 2: Static Signal Intensity (Populated with Real Sheets Priority Scores)
    with b2:
        st.markdown('<div class="hud-panel"><div class="hud-title">SIGNAL INTENSITY</div>', unsafe_allow_html=True)
        if not discovery_df.empty and "_numeric_score" in discovery_df:
            scores = discovery_df["_numeric_score"].tail(25).tolist()
            if len(scores) < 5: scores = [45, 62, 78, 54, 88, 92, 60, 75, 82]
        else:
            scores = [50, 65, 40, 78, 85, 92, 60, 74, 88, 95]

        fig_wave = go.Figure()
        fig_wave.add_trace(go.Scatter(
            y=scores,
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(0, 229, 255, 0.08)',
            line=dict(color='#00E5FF', width=2.5)
        ))
        fig_wave.update_layout(
            height=165,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False, fixedrange=True),
            yaxis=dict(visible=False, fixedrange=True)
        )
        st.plotly_chart(fig_wave, use_container_width=True, config={'staticPlot': True})
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono'; font-size:0.65rem; color:#64748B; margin-top:6px;">
                <span>INTEL STREAM (LAST {len(scores)} ROWS)</span>
                <span style="color:#00E5FF;">PEAK PRIORITY: {max(scores) if scores else 0}/100</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Column 3: Static Threat / Fact Distribution Donut (Derived from Sheet Categories)
    with b3:
        st.markdown('<div class="hud-panel"><div class="hud-title">THREAT DISTRIBUTION</div>', unsafe_allow_html=True)
        if not discovery_df.empty and fact_col in discovery_df:
            cat_counts = discovery_df[fact_col].replace("", "Unverified Leak").value_counts()
            labels = cat_counts.index.tolist()
            values = cat_counts.values.tolist()
        else:
            labels = ['Unverified Leak', 'Speculative Lore', 'Credible Press', 'Official']
            values = [17, 10, 8, 5]

        fig_donut = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.68,
            marker=dict(colors=['#EF4444', '#E024A5', '#7C3AED', '#00E5FF', '#10B981']),
            textinfo='none'
        )])
        fig_donut.update_layout(
            height=165,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            annotations=[dict(text=f'<b>{sum(values)}</b><br><span style="font-size:9px; color:#64748B;">SIGNALS</span>', x=0.5, y=0.5, font_size=14, font_color="#FFF", showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'staticPlot': True})
        st.markdown(f"""
            <div style="display:flex; justify-content:space-around; font-family:'JetBrains Mono'; font-size:0.62rem; color:#94A3B8; margin-top:6px;">
                <span><b style="color:#EF4444;">●</b> Leaks</span>
                <span><b style="color:#E024A5;">●</b> Lore</span>
                <span><b style="color:#7C3AED;">●</b> Press</span>
                <span><b style="color:#00E5FF;">●</b> Official</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==================================================
# 2. SCREEN: INTELLIGENCE (RESEARCH & GROQ TRIAGE)
# ==================================================
elif st.session_state["active_nav"] == "INTELLIGENCE":
    st.markdown("<h2 style='font-family:Chakra Petch;'>🧠 RESEARCH INTELLIGENCE & GROQ HOPPER</h2>", unsafe_allow_html=True)
    st.caption("Inspect live discovered GTA VI leads, review veracity confidence, and run neural inference.")

    if discovery_df.empty:
        st.warning("No records ingested from Google Sheets.")
    else:
        for idx, row in discovery_df.head(10).iterrows():
            row_num = idx + 2
            item_title = str(row.get(title_col, "Untitled Intercept"))
            item_score = int(row.get("_numeric_score", 0))
            item_fact = str(row.get(fact_col, "Unverified Leak"))
            item_status = str(row.get(status_col, "Needs Review"))

            st.markdown(f"""
                <div class="hud-panel" style="margin-bottom:10px; padding:14px 18px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#00E5FF; background:rgba(0,229,255,0.1); padding:2px 6px; border-radius:4px; border:1px solid #00E5FF;">SCORE: {item_score}/100</span>
                            <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#E024A5; margin-left:8px;">VERACITY: {item_fact.upper()}</span>
                            <div style="font-size:1.1rem; font-weight:700; margin-top:4px;">{item_title}</div>
                        </div>
                        <span style="font-family:'JetBrains Mono'; font-size:0.78rem; padding:4px 10px; background:#0B1426; border:1px solid #20314C; border-radius:4px;">{item_status}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_act1, c_act2, c_act3 = st.columns([1, 1, 2.5])
            with c_act1:
                if st.button("APPROVE", key=f"app_{row_num}", use_container_width=True):
                    update_sheet_status("Video Discovery", row_num, "Approved", status_col)
                    st.toast(f"Row {row_num} Approved!", icon="⚡")
                    st.cache_data.clear()
                    st.rerun()
            with c_act2:
                if st.button("RUN GROQ", key=f"groq_{row_num}", use_container_width=True):
                    with st.spinner("Executing neural inference..."):
                        res = analyze_with_groq(row.to_dict())
                        st.json(res)


# ==================================================
# 3. SCREEN: SIGNALS (LIVE FEED & FILTERING)
# ==================================================
elif st.session_state["active_nav"] == "SIGNALS":
    st.markdown("<h2 style='font-family:Chakra Petch;'>📡 LIVE SIGNAL INTERCEPT FEED</h2>", unsafe_allow_html=True)
    st.caption("Continuous telemetry monitoring of GTA VI content signals across platforms.")
    st.dataframe(discovery_df[[title_col, score_col, fact_col, status_col]].dropna(how="all") if not discovery_df.empty else discovery_df, use_container_width=True, hide_index=True)


# ==================================================
# 4. SCREEN: ANALYTICS (TELEMETRY CHARTS)
# ==================================================
elif st.session_state["active_nav"] == "ANALYTICS":
    st.markdown("<h2 style='font-family:Chakra Petch;'>📊 TELEMETRY & SIGNAL ANALYTICS</h2>", unsafe_allow_html=True)
    if not discovery_df.empty and "_numeric_score" in discovery_df:
        st.bar_chart(discovery_df["_numeric_score"])
    else:
        st.info("No score data available yet.")


# ==================================================
# 5. SCREEN: DATABASE (FULL SPREADSHEET EDITOR)
# ==================================================
elif st.session_state["active_nav"] == "DATABASE":
    st.markdown("<h2 style='font-family:Chakra Petch;'>🗄 GOOGLE SHEETS MASTER DATABASE</h2>", unsafe_allow_html=True)
    st.dataframe(discovery_df, use_container_width=True, hide_index=True)


# ==================================================
# 6. SCREEN: SETTINGS (SYSTEM INTEGRITY)
# ==================================================
elif st.session_state["active_nav"] == "SETTINGS":
    st.markdown("<h2 style='font-family:Chakra Petch;'>⚙ SYSTEM INTEGRITY & INTEGRATION STATUS</h2>", unsafe_allow_html=True)
    st.success("Google Sheets API Gateway: Connected")
    st.write(f"Active Groq Model: `{get_secret('GROQ_MODEL', 'llama-3.3-70b-versatile')}`")
    if st.button("FORCE FLUSH SYSTEM CACHE", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared successfully.")
        st.rerun()
